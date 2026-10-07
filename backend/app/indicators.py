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
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    tr = tr.fillna(df["high"] - df["low"])
    values = _wilder(tr.to_numpy(dtype=float), period)
    return pd.Series(values, index=df.index, name=f"atr{period}")


def add_indicators(df: pd.DataFrame, cfg: Settings | None = None) -> pd.DataFrame:
    cfg = cfg or settings
    out = df.copy()
    out["ema20"] = ema(out["close"], 20)
    out["ema50"] = ema(out["close"], 50)
    out["sma200"] = sma(out["close"], 200)
    out["rsi14"] = rsi(out["close"], cfg.rsi_period)
    out["vol_avg20"] = out["volume"].rolling(20).mean()
    out[f"atr{cfg.atr_period}"] = atr(out, cfg.atr_period)
    out["value_avg20"] = (out["close"] * out["volume"]).rolling(20).mean()
    return out
