from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Settings, settings


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def _wilder(values: np.ndarray, period: int) -> np.ndarray:
    n = len(values)
    out = np.full(n, np.nan)
    if n <= period:
        return out
    out[period] = values[1 : period + 1].mean()
    for i in range(period + 1, n):
        out[i] = (out[i - 1] * (period - 1) + values[i]) / period
    return out


def _wilder_nan(values: np.ndarray, period: int) -> np.ndarray:
    """Wilder smoothing that tolerates leading NaNs in the input."""
    n = len(values)
    out = np.full(n, np.nan)
    if n < period:
        return out
    start: int | None = None
    for end in range(period - 1, n):
        window = values[end - period + 1 : end + 1]
        if not np.isnan(window).any():
            out[end] = float(window.mean())
            start = end
            break
    if start is None:
        return out
    for i in range(start + 1, n):
        value = values[i]
        if np.isnan(value):
            out[i] = out[i - 1]
        else:
            out[i] = (out[i - 1] * (period - 1) + value) / period
    return out


def _true_range(df: pd.DataFrame) -> np.ndarray:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.fillna(df["high"] - df["low"]).to_numpy(dtype=float)


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).fillna(0).to_numpy(dtype=float)
    loss = (-delta).clip(lower=0).fillna(0).to_numpy(dtype=float)
    avg_gain = _wilder(gain, period)
    avg_loss = _wilder(loss, period)
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = np.where(avg_loss > 0, avg_gain / avg_loss, np.nan)
    out = 100.0 - 100.0 / (1.0 + rs)
    out = np.where((avg_loss == 0) & (avg_gain > 0), 100.0, out)
    out = np.where((avg_loss == 0) & (avg_gain == 0), 50.0, out)
    return pd.Series(out, index=series.index, name=f"rsi{period}")


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    tr = _true_range(df)
    values = _wilder(tr, period)
    return pd.Series(values, index=df.index, name=f"atr{period}")


def adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Average Directional Index with +DI/-DI (Wilder)."""
    n = len(df)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    up = np.zeros(n)
    down = np.zeros(n)
    if n > 1:
        up[1:] = np.diff(high)
        down[1:] = -np.diff(low)
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    tr = _true_range(df)
    atr_values = _wilder(tr, period)
    with np.errstate(divide="ignore", invalid="ignore"):
        plus_di = np.divide(
            100.0 * _wilder(plus_dm, period),
            atr_values,
            out=np.full(n, np.nan),
            where=atr_values > 0,
        )
        minus_di = np.divide(
            100.0 * _wilder(minus_dm, period),
            atr_values,
            out=np.full(n, np.nan),
            where=atr_values > 0,
        )
        denom = plus_di + minus_di
        dx = np.divide(
            100.0 * np.abs(plus_di - minus_di),
            denom,
            out=np.full(n, np.nan),
            where=denom > 0,
        )
    return pd.DataFrame(
        {"adx14": _wilder_nan(dx, period), "di_plus14": plus_di, "di_minus14": minus_di},
        index=df.index,
    )


def macd(
    close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    line = ema(close, fast) - ema(close, slow)
    signal_line = line.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame(
        {"macd": line, "macd_signal": signal_line, "macd_hist": line - signal_line},
        index=close.index,
    )


def bollinger(close: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    mid = close.rolling(window).mean()
    std = close.rolling(window).std(ddof=0)
    upper = mid + num_std * std
    lower = mid - num_std * std
    width = upper - lower
    n = len(close)
    with np.errstate(divide="ignore", invalid="ignore"):
        bandwidth = np.divide(
            width, mid, out=np.full(n, np.nan), where=mid > 0
        ) * 100.0
        pctb = np.divide(
            close - lower, width, out=np.full(n, np.nan), where=width > 0
        )
    return pd.DataFrame(
        {
            "bb_mid": mid,
            "bb_upper": upper,
            "bb_lower": lower,
            "bb_bandwidth": bandwidth,
            "bb_pctb": pctb,
        },
        index=close.index,
    )


def stochastic(df: pd.DataFrame, k: int = 14, d: int = 3) -> pd.DataFrame:
    lowest = df["low"].rolling(k).min()
    highest = df["high"].rolling(k).max()
    rng = highest - lowest
    n = len(df)
    with np.errstate(divide="ignore", invalid="ignore"):
        k_line = np.divide(
            100.0 * (df["close"] - lowest), rng, out=np.full(n, np.nan), where=rng > 0
        )
    k_series = pd.Series(k_line, index=df.index)
    return pd.DataFrame({"stoch_k": k_series, "stoch_d": k_series.rolling(d).mean()},
                        index=df.index)


def obv(df: pd.DataFrame, slope_window: int = 10) -> pd.DataFrame:
    direction = np.sign(df["close"].diff().fillna(0.0))
    line = (direction * df["volume"]).cumsum()
    return pd.DataFrame({"obv": line, "obv_slope": line - line.shift(slope_window)},
                        index=df.index)


def _relative_strength(
    df: pd.DataFrame, benchmark: pd.DataFrame | pd.Series | None, lookback: int
) -> pd.Series:
    """Stock return minus benchmark return over `lookback` bars, in percentage points."""
    if benchmark is None or len(benchmark) == 0:
        return pd.Series(np.nan, index=df.index)
    bench = benchmark
    if isinstance(bench, pd.DataFrame):
        if "close" not in bench.columns:
            return pd.Series(np.nan, index=df.index)
        frame = bench[["date", "close"]].copy()
        frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()
        bench = frame.drop_duplicates("date").set_index("date")["close"]
    else:
        bench = bench.copy()
        bench.index = pd.to_datetime(bench.index).normalize()
    idx = pd.to_datetime(df["date"]).dt.normalize()
    aligned = pd.Series(bench.reindex(idx).to_numpy(dtype=float), index=df.index)
    stock_ret = df["close"] / df["close"].shift(lookback) - 1.0
    bench_ret = aligned / aligned.shift(lookback) - 1.0
    return (stock_ret - bench_ret) * 100.0


def add_indicators(
    df: pd.DataFrame,
    cfg: Settings | None = None,
    benchmark: pd.DataFrame | pd.Series | None = None,
) -> pd.DataFrame:
    cfg = cfg or settings
    out = df.copy()
    out["ema20"] = ema(out["close"], 20)
    out["ema50"] = ema(out["close"], 50)
    out["sma200"] = sma(out["close"], 200)
    out["rsi14"] = rsi(out["close"], cfg.rsi_period)
    out["vol_avg20"] = out["volume"].rolling(20).mean()
    out[f"atr{cfg.atr_period}"] = atr(out, cfg.atr_period)
    out["value_avg20"] = (out["close"] * out["volume"]).rolling(20).mean()
    out = out.join(macd(out["close"], cfg.macd_fast, cfg.macd_slow, cfg.macd_signal))
    out = out.join(bollinger(out["close"], cfg.bb_window, cfg.bb_std))
    out = out.join(stochastic(out, cfg.stoch_k, cfg.stoch_d))
    out = out.join(adx(out, cfg.adx_period))
    out = out.join(obv(out, cfg.obv_slope_window))
    out["atr_pct"] = out[f"atr{cfg.atr_period}"] / out["close"] * 100.0
    out["high_52w"] = out["high"].rolling(cfg.high_52w_window, min_periods=60).max()
    out["dist_52w_high"] = (out["close"] - out["high_52w"]) / out["high_52w"] * 100.0
    out["rs"] = _relative_strength(out, benchmark, cfg.rs_lookback)
    return out
