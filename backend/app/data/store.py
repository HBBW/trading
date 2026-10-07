from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date

import duckdb
import pandas as pd

from ..config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS universe (
    symbol VARCHAR PRIMARY KEY,
    name VARCHAR,
    sector VARCHAR,
    active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ohlcv (
    symbol VARCHAR NOT NULL,
    date DATE NOT NULL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume BIGINT,
    PRIMARY KEY (symbol, date)
);

CREATE TABLE IF NOT EXISTS scan_runs (
    run_id VARCHAR PRIMARY KEY,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    mode VARCHAR,
    status VARCHAR DEFAULT 'running',
    universe_size INTEGER,
    fetched INTEGER,
    scanned INTEGER,
    candidates INTEGER,
    errors INTEGER,
    message VARCHAR
);

CREATE TABLE IF NOT EXISTS scan_results (
    run_id VARCHAR NOT NULL,
    symbol VARCHAR NOT NULL,
    score DOUBLE,
    signal VARCHAR,
    close DOUBLE,
    rsi DOUBLE,
    rsi_prev DOUBLE,
    ema20 DOUBLE,
    ema50 DOUBLE,
    sma200 DOUBLE,
    vol_avg20 DOUBLE,
    atr14 DOUBLE,
    value_avg20 DOUBLE,
    volume BIGINT,
    entry DOUBLE,
    stop_loss DOUBLE,
    tp1 DOUBLE,
    tp2 DOUBLE,
    risk_reward DOUBLE,
    data_date DATE,
    breakdown VARCHAR,
    scalp_score DOUBLE,
    scalp_signal VARCHAR,
    scalp_entry DOUBLE,
    scalp_stop_loss DOUBLE,
    scalp_tp1 DOUBLE,
    scalp_tp2 DOUBLE,
    scalp_risk_reward DOUBLE,
    scalp_breakdown VARCHAR,
    day_score DOUBLE,
    day_signal VARCHAR,
    day_entry DOUBLE,
    day_stop_loss DOUBLE,
    day_tp1 DOUBLE,
    day_tp2 DOUBLE,
    day_risk_reward DOUBLE,
    day_breakdown VARCHAR,
    overnight_score DOUBLE,
    overnight_signal VARCHAR,
    overnight_entry DOUBLE,
    overnight_stop_loss DOUBLE,
    overnight_tp1 DOUBLE,
    overnight_tp2 DOUBLE,
    overnight_risk_reward DOUBLE,
    overnight_breakdown VARCHAR,
    adx14 DOUBLE,
    di_plus14 DOUBLE,
    di_minus14 DOUBLE,
    macd DOUBLE,
    macd_signal DOUBLE,
    macd_hist DOUBLE,
    bb_bandwidth DOUBLE,
    bb_pctb DOUBLE,
    stoch_k DOUBLE,
    stoch_d DOUBLE,
    dist_52w_high DOUBLE,
    atr_pct DOUBLE,
    rs DOUBLE,
    obv_slope DOUBLE,
    created_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (run_id, symbol)
);
"""

_write_lock = threading.Lock()


@contextmanager
def get_conn(read_only: bool = False) -> Iterator[duckdb.DuckDBPyConnection]:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(settings.db_path), read_only=read_only)
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with _write_lock, get_conn() as conn:
        conn.execute(_SCHEMA)
        conn.execute("ALTER TABLE scan_results ADD COLUMN IF NOT EXISTS volume BIGINT")
        for col in [
            "scalp_score DOUBLE",
            "scalp_signal VARCHAR",
            "scalp_entry DOUBLE",
            "scalp_stop_loss DOUBLE",
            "scalp_tp1 DOUBLE",
            "scalp_tp2 DOUBLE",
            "scalp_risk_reward DOUBLE",
            "scalp_breakdown VARCHAR",
            "day_score DOUBLE",
            "day_signal VARCHAR",
            "day_entry DOUBLE",
            "day_stop_loss DOUBLE",
            "day_tp1 DOUBLE",
            "day_tp2 DOUBLE",
            "day_risk_reward DOUBLE",
            "day_breakdown VARCHAR",
            "overnight_score DOUBLE",
            "overnight_signal VARCHAR",
            "overnight_entry DOUBLE",
            "overnight_stop_loss DOUBLE",
            "overnight_tp1 DOUBLE",
            "overnight_tp2 DOUBLE",
            "overnight_risk_reward DOUBLE",
            "overnight_breakdown VARCHAR",
            "adx14 DOUBLE",
            "di_plus14 DOUBLE",
            "di_minus14 DOUBLE",
            "macd DOUBLE",
            "macd_signal DOUBLE",
            "macd_hist DOUBLE",
            "bb_bandwidth DOUBLE",
            "bb_pctb DOUBLE",
            "stoch_k DOUBLE",
            "stoch_d DOUBLE",
            "dist_52w_high DOUBLE",
            "atr_pct DOUBLE",
            "rs DOUBLE",
            "obv_slope DOUBLE",
        ]:
            conn.execute(f"ALTER TABLE scan_results ADD COLUMN IF NOT EXISTS {col}")


def upsert_universe(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    frame = df[["symbol", "name", "sector"]].copy()
    frame["symbol"] = frame["symbol"].str.upper().str.strip()
    with _write_lock, get_conn() as conn:
        conn.register("_universe_df", frame)
        conn.execute(
            """
            INSERT OR REPLACE INTO universe (symbol, name, sector, active, updated_at)
            SELECT symbol, name, sector, TRUE, now() FROM _universe_df
            """
        )
        conn.unregister("_universe_df")
    return len(frame)


def get_universe(active_only: bool = True) -> pd.DataFrame:
    where = "WHERE active" if active_only else ""
    with get_conn(read_only=False) as conn:
        return conn.execute(
            f"SELECT symbol, name, sector FROM universe {where} ORDER BY symbol"
        ).df()


def upsert_ohlcv(symbol: str, df: pd.DataFrame) -> int:
    """Append-only upsert of daily bars for one symbol.

    df must have columns: date, open, high, low, close, volume (extra columns ignored).
    """
    if df.empty:
        return 0
    frame = df[["date", "open", "high", "low", "close", "volume"]].copy()
    frame["symbol"] = symbol
    frame = frame.dropna(subset=["date", "close"])
    frame = frame[["symbol", "date", "open", "high", "low", "close", "volume"]]
    with _write_lock, get_conn() as conn:
        conn.register("_ohlcv_df", frame)
        conn.execute(
            """
            INSERT OR REPLACE INTO ohlcv (symbol, date, open, high, low, close, volume)
            SELECT symbol, date, open, high, low, close, COALESCE(volume, 0) FROM _ohlcv_df
            """
        )
        conn.unregister("_ohlcv_df")
    return len(frame)


def last_ohlcv_date(symbol: str) -> date | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT max(date) FROM ohlcv WHERE symbol = ?", [symbol]
        ).fetchone()
    return row[0] if row and row[0] is not None else None


def count_ohlcv(symbol: str) -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT count(*) FROM ohlcv WHERE symbol = ?", [symbol]).fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def get_ohlcv_stats(symbols: list[str]) -> pd.DataFrame:
    """Cached bar count and last date per symbol, in one query."""
    if not symbols:
        return pd.DataFrame(columns=["symbol", "last_date", "bars"])
    frame = pd.DataFrame({"symbol": symbols})
    with get_conn() as conn:
        conn.register("_syms", frame)
        stats = conn.execute(
            """
            SELECT s.symbol, max(o.date) AS last_date, count(o.date) AS bars
            FROM _syms s
            LEFT JOIN ohlcv o USING (symbol)
            GROUP BY s.symbol
            """
        ).df()
        conn.unregister("_syms")
    return stats


def load_ohlcv(symbol: str, days: int = 300) -> pd.DataFrame:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT date, open, high, low, close, volume
            FROM ohlcv WHERE symbol = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            [symbol, days],
        ).df().sort_values("date").reset_index(drop=True)


def create_scan_run(run_id: str, mode: str, universe_size: int, started_at: str) -> None:
    with _write_lock, get_conn() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO scan_runs
                (run_id, started_at, mode, status, universe_size)
            VALUES (?, ?, ?, 'running', ?)
            """,
            [run_id, started_at, mode, universe_size],
        )


def finish_scan_run(run_id: str, **fields) -> None:
    allowed = {
        "finished_at",
        "status",
        "fetched",
        "scanned",
        "candidates",
        "errors",
        "message",
    }
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return
    sets = ", ".join(f"{k} = ?" for k in updates)
    with _write_lock, get_conn() as conn:
        conn.execute(f"UPDATE scan_runs SET {sets} WHERE run_id = ?", [*updates.values(), run_id])


def save_scan_results(rows: list[dict]) -> int:
    if not rows:
        return 0
    frame = pd.DataFrame(rows)
    cols = [
        "run_id", "symbol", "score", "signal", "close", "rsi", "rsi_prev",
        "ema20", "ema50", "sma200", "vol_avg20", "atr14", "value_avg20", "volume",
        "entry", "stop_loss", "tp1", "tp2", "risk_reward", "data_date", "breakdown",
        "scalp_score", "scalp_signal", "scalp_entry", "scalp_stop_loss", "scalp_tp1",
        "scalp_tp2", "scalp_risk_reward", "scalp_breakdown",
        "day_score", "day_signal", "day_entry", "day_stop_loss", "day_tp1",
        "day_tp2", "day_risk_reward", "day_breakdown",
        "overnight_score", "overnight_signal", "overnight_entry", "overnight_stop_loss",
        "overnight_tp1", "overnight_tp2", "overnight_risk_reward", "overnight_breakdown",
        "adx14", "di_plus14", "di_minus14", "macd", "macd_signal", "macd_hist",
        "bb_bandwidth", "bb_pctb", "stoch_k", "stoch_d", "dist_52w_high", "atr_pct",
        "rs", "obv_slope",
    ]
    frame = frame.reindex(columns=cols)
    with _write_lock, get_conn() as conn:
        conn.register("_results_df", frame)
        conn.execute(
            f"""
            INSERT OR REPLACE INTO scan_results ({", ".join(cols)})
            SELECT {", ".join(cols)} FROM _results_df
            """
        )
        conn.unregister("_results_df")
    return len(frame)


def latest_run() -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM scan_runs WHERE status = 'ok' ORDER BY finished_at DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return dict(zip([c[0] for c in conn.description], row, strict=False))


def run_on_date(day: date) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM scan_runs
            WHERE status = 'ok' AND CAST(finished_at AS DATE) = ?
            ORDER BY finished_at DESC LIMIT 1
            """,
            [day],
        ).fetchone()
        if row is None:
            return None
        return dict(zip([c[0] for c in conn.description], row, strict=False))


def recent_runs(limit: int = 20) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM scan_runs ORDER BY started_at DESC LIMIT ?", [limit]
        ).fetchall()
        cols = [c[0] for c in conn.description]
    return [dict(zip(cols, r, strict=False)) for r in rows]


def get_results(
    run_id: str,
    min_score: float | None = None,
    signal: str | None = None,
    sector: str | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    clauses = ["r.run_id = ?"]
    params: list = [run_id]
    if min_score is not None:
        clauses.append("r.score >= ?")
        params.append(min_score)
    if signal:
        clauses.append("r.signal = ?")
        params.append(signal)
    if sector:
        clauses.append("u.sector = ?")
        params.append(sector)
    sql = f"""
        SELECT r.*, u.name, u.sector
        FROM scan_results r
        LEFT JOIN universe u USING (symbol)
        WHERE {" AND ".join(clauses)}
        ORDER BY r.score DESC, r.symbol
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    with get_conn() as conn:
        return conn.execute(sql, params).df()
