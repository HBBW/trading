from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import routes_scan, routes_ticker
from .data import store
from .scheduler import build_scheduler
from .universe import seed_universe

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    store.init_db()
    if store.get_universe().empty:
        count = seed_universe()
        log.info("universe seeded: %s tickers", count)

    scheduler = None
    if os.environ.get("TRADING_DISABLE_SCHEDULER") != "1":
        scheduler = build_scheduler()
        scheduler.start()
        log.info("scheduler started (tz=%s)", scheduler.timezone)
    app.state.scheduler = scheduler
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


app = FastAPI(title="IDX Swing Screener", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_scan.router)
app.include_router(routes_ticker.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
