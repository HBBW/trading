from __future__ import annotations

from datetime import date, datetime

import pandas as pd
from fastapi import APIRouter

from ..config import settings
from ..data import store
from ..data.fetcher import update_price_cache
from ..indicators import add_indicators
from ..models import Bar, MarketStatusResponse, SeriesPoint, TickerResponse
from ..strategy import evaluate, evaluate_daytrade, evaluate_overnight, evaluate_scalp, trade_block

router = APIRouter(prefix="/api", tags=["ticker"])


@router.get("/market/status", response_model=MarketStatusResponse)
def market_status() -> MarketStatusResponse:
    now = datetime.now(settings.tz)
    sessions = settings.sessions()
    is_open = settings.in_market_hours(now)
    session: str | None = None
    next_event: str | None = None
    t = now.time()

    if now.weekday() < 5:
        if is_open:
            for i, (start, end) in enumerate(sessions):
                if start <= t <= end:
                    session = "morning" if i == 0 else "afternoon"
                    next_event = f"close {end.strftime('%H:%M')} WIB"
                    break
        elif t < sessions[0][0]:
            next_event = f"open {sessions[0][0].strftime('%H:%M')} WIB"
        elif sessions[0][1] < t < sessions[1][0]:
            next_event = f"reopen {sessions[1][0].strftime('%H:%M')} WIB"
        else:
            next_event = "next trading day 09:00 WIB"
    else:
        next_event = "next trading day 09:00 WIB"

    return MarketStatusResponse(
        now=now,
        timezone=settings.timezone,
        is_trading_day=settings.is_trading_day(now.date()),
        is_open=is_open,
        session=session,
        next_event=next_event,
    )


@router.get("/ticker/{symbol}", response_model=TickerResponse)
def ticker_detail(symbol: str, days: int = 180, refresh: bool = False) -> TickerResponse:
    sym = symbol.upper().replace(".JK", "").strip()
    days = max(30, min(days, 500))

    universe = store.get_universe()
    meta = universe[universe["symbol"] == sym]
    name = str(meta.iloc[0]["name"]) if not meta.empty else None
    sector = str(meta.iloc[0]["sector"]) if not meta.empty else None

    hist = store.load_ohlcv(sym, settings.history_days)
    need_fetch = refresh or hist.empty
    if not hist.empty and settings.is_trading_day():
        last_day = pd.to_datetime(hist["date"].iloc[-1]).date()
        need_fetch = need_fetch or last_day < date.today()
    if need_fetch:
        try:
            update_price_cache([sym])
            hist = store.load_ohlcv(sym, settings.history_days)
        except Exception:  # noqa: BLE001 - serve cache when provider fails
            pass

    if hist.empty:
        return TickerResponse(symbol=sym, name=name, sector=sector, error="no data available")

    benchmark = store.load_ohlcv(settings.benchmark_symbol, settings.history_days)
    if benchmark.empty:
        try:
            update_price_cache([settings.benchmark_symbol])
            benchmark = store.load_ohlcv(settings.benchmark_symbol, settings.history_days)
        except Exception:  # noqa: BLE001 - benchmark is best-effort
            pass

    frame = add_indicators(hist, settings, benchmark)
    ev = evaluate(frame, settings)
    scalp = evaluate_scalp(frame, settings)
    day = evaluate_daytrade(frame, settings)
    overnight = evaluate_overnight(frame, settings)
    tail = frame.tail(days)
    bars = [
        Bar(
            date=pd.to_datetime(r["date"]).date(),
            open=float(r["open"]),
            high=float(r["high"]),
            low=float(r["low"]),
            close=float(r["close"]),
            volume=float(r["volume"]),
        )
        for _, r in tail.iterrows()
    ]
    last = frame.iloc[-1]
    indicators = {
        "ema20": _num(last.get("ema20")),
        "ema50": _num(last.get("ema50")),
        "sma200": _num(last.get("sma200")),
        "rsi14": _num(last.get("rsi14")),
        "vol_avg20": _num(last.get("vol_avg20")),
        "atr14": _num(last.get(f"atr{settings.atr_period}")),
        "value_avg20": _num(last.get("value_avg20")),
        "adx14": _num(last.get("adx14")),
        "di_plus14": _num(last.get("di_plus14")),
        "di_minus14": _num(last.get("di_minus14")),
        "macd": _num(last.get("macd")),
        "macd_signal": _num(last.get("macd_signal")),
        "macd_hist": _num(last.get("macd_hist")),
        "bb_upper": _num(last.get("bb_upper")),
        "bb_lower": _num(last.get("bb_lower")),
        "bb_bandwidth": _num(last.get("bb_bandwidth")),
        "bb_pctb": _num(last.get("bb_pctb")),
        "stoch_k": _num(last.get("stoch_k")),
        "stoch_d": _num(last.get("stoch_d")),
        "dist_52w_high": _num(last.get("dist_52w_high")),
        "atr_pct": _num(last.get("atr_pct")),
        "rs": _num(last.get("rs")),
        "obv_slope": _num(last.get("obv_slope")),
    }
    series: dict[str, list[SeriesPoint]] = {}
    for col, key in [
        ("ema20", "ema20"),
        ("ema50", "ema50"),
        ("sma200", "sma200"),
        ("rsi14", "rsi14"),
        ("bb_upper", "bb_upper"),
        ("bb_lower", "bb_lower"),
        ("macd", "macd"),
        ("macd_signal", "macd_signal"),
        ("macd_hist", "macd_hist"),
        ("stoch_k", "stoch_k"),
        ("stoch_d", "stoch_d"),
        ("adx14", "adx14"),
    ]:
        if col not in tail.columns:
            continue
        points = tail[["date", col]].dropna()
        series[key] = [
            SeriesPoint(date=pd.to_datetime(r["date"]).date(), value=round(float(r[col]), 2))
            for _, r in points.iterrows()
        ]
    evaluation = None
    blocks = {"scalp": scalp, "day": day, "overnight": overnight}
    if ev is not None or any(v is not None for v in blocks.values()):
        swing = trade_block(ev) or {
            "score": None,
            "signal": None,
            "checks": None,
            "breakdown": None,
            "plan": None,
        }
        evaluation = {**swing, **{key: trade_block(value) for key, value in blocks.items()}}
    return TickerResponse(
        symbol=sym,
        name=name,
        sector=sector,
        data_date=pd.to_datetime(last["date"]).date(),
        bars=bars,
        indicators=indicators,
        series=series,
        evaluation=evaluation,
    )


def _num(value) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), 2)
