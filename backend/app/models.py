from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class ScanRun(BaseModel):
    run_id: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    mode: str | None = None
    status: str | None = None
    universe_size: int | None = None
    fetched: int | None = None
    scanned: int | None = None
    candidates: int | None = None
    errors: int | None = None
    message: str | None = None


class ScanResult(BaseModel):
    symbol: str
    name: str | None = None
    sector: str | None = None
    score: float
    signal: str
    close: float | None = None
    rsi: float | None = None
    rsi_prev: float | None = None
    ema20: float | None = None
    ema50: float | None = None
    sma200: float | None = None
    vol_avg20: float | None = None
    atr14: float | None = None
    value_avg20: float | None = None
    volume: float | None = None
    entry: float | None = None
    stop_loss: float | None = None
    tp1: float | None = None
    tp2: float | None = None
    risk_reward: float | None = None
    data_date: date | None = None
    breakdown: dict | None = None
    scalp_score: float | None = None
    scalp_signal: str | None = None
    scalp_entry: float | None = None
    scalp_stop_loss: float | None = None
    scalp_tp1: float | None = None
    scalp_tp2: float | None = None
    scalp_risk_reward: float | None = None
    scalp_breakdown: dict | None = None
    day_score: float | None = None
    day_signal: str | None = None
    day_entry: float | None = None
    day_stop_loss: float | None = None
    day_tp1: float | None = None
    day_tp2: float | None = None
    day_risk_reward: float | None = None
    day_breakdown: dict | None = None
    overnight_score: float | None = None
    overnight_signal: str | None = None
    overnight_entry: float | None = None
    overnight_stop_loss: float | None = None
    overnight_tp1: float | None = None
    overnight_tp2: float | None = None
    overnight_risk_reward: float | None = None
    overnight_breakdown: dict | None = None


class ScanLatestResponse(BaseModel):
    run: ScanRun | None = None
    results: list[ScanResult] = []


class Bar(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


class SeriesPoint(BaseModel):
    date: date
    value: float


class TickerResponse(BaseModel):
    symbol: str
    name: str | None = None
    sector: str | None = None
    data_date: date | None = None
    bars: list[Bar] = []
    indicators: dict = {}
    series: dict[str, list[SeriesPoint]] = {}
    evaluation: dict | None = None
    error: str | None = None


class MarketStatusResponse(BaseModel):
    now: datetime
    timezone: str
    is_trading_day: bool
    is_open: bool
    session: str | None = None
    next_event: str | None = None
