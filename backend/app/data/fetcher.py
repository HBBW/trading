from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from typing import Protocol

import pandas as pd

from ..config import settings

log = logging.getLogger(__name__)

_OHLCV_COLS = ["open", "high", "low", "close", "volume"]


class DataProvider(Protocol):
    """Pluggable market-data source.

    Swap in a paid realtime API (goapi.io, EODHD, ...) by implementing this
    protocol and wiring it in `get_provider()`.
    """

    name: str

    def fetch_daily(
        self,
        symbols: list[str],
        start: date,
        end: date | None = None,
    ) -> dict[str, pd.DataFrame]:
        """Return {symbol: DataFrame[date, open, high, low, close, volume]}."""
        ...


class YFinanceProvider:
    name = "yfinance"

    def __init__(self, suffix: str | None = None) -> None:
        self.suffix = suffix if suffix is not None else settings.ticker_suffix

    def _to_yahoo(self, symbol: str) -> str:
        return f"{symbol}{self.suffix}"

    def fetch_daily(
        self,
        symbols: list[str],
        start: date,
        end: date | None = None,
    ) -> dict[str, pd.DataFrame]:
        import yfinance as yf

        end_dt = (end or date.today()) + timedelta(days=1)
        fetched: dict[str, pd.DataFrame] = {}

        for i in range(0, len(symbols), settings.batch_size):
            chunk = symbols[i : i + settings.batch_size]
            yahoo = [self._to_yahoo(s) for s in chunk]
            raw = self._download_with_retry(yf, yahoo, start, end_dt)
            if raw is None or raw.empty:
                continue
            for sym, ys in zip(chunk, yahoo, strict=False):
                df = self._extract(raw, ys)
                if df is not None and not df.empty:
                    fetched[sym] = df
        return fetched

    def _download_with_retry(self, yf, yahoo: list[str], start: date, end_dt: date):
        last_exc: Exception | None = None
        for attempt in range(settings.fetch_retries):
            try:
                return yf.download(
                    yahoo,
                    start=start.isoformat(),
                    end=end_dt.isoformat(),
                    interval="1d",
                    auto_adjust=False,
                    actions=False,
                    group_by="ticker",
                    threads=True,
                    progress=False,
                )
            except Exception as exc:  # noqa: BLE001 - retry any provider error
                last_exc = exc
                wait = settings.fetch_backoff * (attempt + 1)
                log.warning("yfinance batch failed (attempt %s/%s): %s", attempt + 1, settings.fetch_retries, exc)
                time.sleep(wait)
        log.error("yfinance batch giving up: %s", last_exc)
        return None

    @staticmethod
    def _extract(raw: pd.DataFrame, yahoo_symbol: str) -> pd.DataFrame | None:
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                if yahoo_symbol in raw.columns.get_level_values(0):
                    df = raw[yahoo_symbol].copy()
                elif yahoo_symbol in raw.columns.get_level_values(1):
                    df = raw.xs(yahoo_symbol, axis=1, level=1).copy()
                else:
                    return None
            else:
                df = raw.copy()
        except Exception:  # noqa: BLE001
            return None
        if df is None or df.empty:
            return None
        df = df.rename(columns=str.lower)
        missing = [c for c in _OHLCV_COLS if c not in df.columns]
        if missing:
            return None
        df = df[_OHLCV_COLS].copy()
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype("int64")
        for c in ["open", "high", "low", "close"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=["close"])
        df.index = pd.to_datetime(df.index).date
        df.index.name = "date"
        return df.reset_index()


def get_provider(name: str | None = None) -> DataProvider:
    provider = (name or settings.provider).lower()
    if provider == "yfinance":
        return YFinanceProvider()
    raise ValueError(f"unknown provider: {provider}")


def update_price_cache(
    symbols: list[str],
    provider: DataProvider | None = None,
    history_days: int | None = None,
) -> tuple[int, list[str]]:
    """Fetch recent bars per symbol (append-only) into DuckDB.

    Returns (symbols_updated, failed_symbols).
    """
    from . import store

    provider = provider or get_provider()
    days = history_days or settings.history_days
    today = date.today()
    default_start = today - timedelta(days=days)

    starts: dict[str, date] = {}
    stats = store.get_ohlcv_stats(symbols)
    if not stats.empty:
        stats = stats.set_index("symbol")
    for sym in symbols:
        cached: date | None = None
        bars = 0
        if not stats.empty and sym in stats.index:
            row = stats.loc[sym]
            if pd.notna(row["last_date"]):
                cached = pd.Timestamp(row["last_date"]).date()
            bars = int(row["bars"])
        if cached is None or bars < settings.min_history_bars:
            starts[sym] = default_start
        else:
            starts[sym] = cached - timedelta(days=settings.cache_overlap_days)

    fetched_total = 0
    failed: list[str] = []
    remaining = sorted(symbols, key=lambda s: starts[s])

    for i in range(0, len(remaining), settings.batch_size):
        chunk = remaining[i : i + settings.batch_size]
        chunk_start = min(starts[s] for s in chunk)
        try:
            data = provider.fetch_daily(chunk, start=chunk_start, end=today)
        except Exception as exc:  # noqa: BLE001
            log.error("fetch failed for chunk %s..%s: %s", chunk[0], chunk[-1], exc)
            failed.extend(chunk)
            continue
        for sym in chunk:
            df = data.get(sym)
            if df is None or df.empty:
                failed.append(sym)
                continue
            fetched_total += store.upsert_ohlcv(sym, df)
    return fetched_total, failed
