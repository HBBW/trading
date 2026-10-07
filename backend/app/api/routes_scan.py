from __future__ import annotations

import json
import uuid
from datetime import date

import pandas as pd
from fastapi import APIRouter, Request

from ..data import store
from ..models import ScanLatestResponse, ScanResult, ScanRun
from ..scanner import run_scan

router = APIRouter(prefix="/api/scan", tags=["scan"])


def _run_model(run: dict | None) -> ScanRun | None:
    if run is None:
        return None
    return ScanRun(**{k: v for k, v in run.items() if k in ScanRun.model_fields})


def _result_model(row: pd.Series) -> ScanResult:
    data = row.to_dict()
    data.pop("created_at", None)
    data.pop("run_id", None)
    for key in ("breakdown", "scalp_breakdown", "day_breakdown", "overnight_breakdown"):
        value = data.get(key)
        if isinstance(value, str):
            try:
                data[key] = json.loads(value)
            except json.JSONDecodeError:
                data[key] = None
        elif value is None or (isinstance(value, float) and pd.isna(value)):
            data[key] = None
    return ScanResult(**data)


@router.get("/latest", response_model=ScanLatestResponse)
def latest_scan(
    min_score: float | None = None,
    signal: str | None = None,
    sector: str | None = None,
    limit: int = 200,
):
    run = store.latest_run()
    if run is None:
        return ScanLatestResponse()
    df = store.get_results(
        run["run_id"], min_score=min_score, signal=signal, sector=sector, limit=limit
    )
    return ScanLatestResponse(
        run=_run_model(run),
        results=[_result_model(row) for _, row in df.iterrows()],
    )


@router.get("/runs")
def list_runs(limit: int = 20):
    return store.recent_runs(limit)


@router.post("/run")
def trigger_scan(request: Request, mode: str = "manual", limit: int | None = None):
    job_id = f"manual-{uuid.uuid4().hex[:8]}"
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler is not None:
        scheduler.add_job(
            run_scan,
            kwargs={"mode": mode, "limit": limit},
            id=job_id,
            max_instances=1,
            misfire_grace_time=300,
        )
        return {"status": "scheduled", "job_id": job_id}
    summary = run_scan(mode=mode, limit=limit)
    return {"status": "done", "result": summary}


@router.get("/{day}", response_model=ScanLatestResponse)
def scan_on_date(
    day: date,
    min_score: float | None = None,
    signal: str | None = None,
    sector: str | None = None,
    limit: int = 200,
):
    run = store.run_on_date(day)
    if run is None:
        return ScanLatestResponse()
    df = store.get_results(
        run["run_id"], min_score=min_score, signal=signal, sector=sector, limit=limit
    )
    return ScanLatestResponse(
        run=_run_model(run),
        results=[_result_model(row) for _, row in df.iterrows()],
    )
