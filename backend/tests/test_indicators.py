import numpy as np
import pandas as pd
import pytest

from app.indicators import add_indicators, adx, atr, bollinger, ema, macd, obv, rsi, sma, stochastic

CANONICAL_CLOSES = [
    44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08,
    45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64,
    46.21, 46.25, 45.71, 46.45, 45.78, 45.35, 44.03, 44.18, 44.22, 44.57,
    43.42, 42.66, 43.13,
]

CANONICAL_RSI_14 = [
    70.53, 66.32, 66.55, 69.41, 66.36, 57.97, 62.93, 63.26, 56.06, 62.38,
    54.71, 50.42, 39.99, 41.46, 41.87, 45.46, 37.30, 33.08, 37.77,
]


def test_rsi_matches_wilder_reference():
    out = rsi(pd.Series(CANONICAL_CLOSES), 14)
    got = out.iloc[14:].to_numpy()
    assert len(got) == len(CANONICAL_RSI_14)
    assert np.allclose(got, np.array(CANONICAL_RSI_14), atol=0.2)


def test_rsi_all_gains_returns_100():
    out = rsi(pd.Series(np.arange(1, 40, dtype=float)), 14)
    assert out.iloc[-1] == pytest.approx(100.0)


def test_ema_recursion():
    out = ema(pd.Series([1, 2, 3, 4, 5]), span=3)
    assert out.tolist() == pytest.approx([1.0, 1.5, 2.25, 3.125, 4.0625])


def test_sma_window():
    out = sma(pd.Series([1, 2, 3, 4, 5]), 3)
    assert np.isnan(out.iloc[1])
    assert out.iloc[2] == pytest.approx(2.0)
    assert out.iloc[4] == pytest.approx(4.0)


def test_atr_constant_range():
    n = 40
    df = pd.DataFrame(
        {"high": [1.1] * n, "low": [0.9] * n, "close": [1.0] * n}
    )
    out = atr(df, 14)
    assert np.isnan(out.iloc[13])
    assert out.iloc[14] == pytest.approx(0.2)
    assert out.iloc[-1] == pytest.approx(0.2)


def _trend_frame(n: int = 120, step: float = 1.0) -> pd.DataFrame:
    close = 100 + np.arange(n) * step
    return pd.DataFrame(
        {
            "date": pd.bdate_range("2024-01-01", periods=n),
            "open": close,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": np.full(n, 1_000_000.0),
        }
    )


def test_adx_uptrend_has_positive_di():
    out = adx(_trend_frame(), 14)
    assert out["adx14"].iloc[-1] > 20
    assert out["di_plus14"].iloc[-1] > out["di_minus14"].iloc[-1]


def test_macd_positive_on_uptrend():
    out = macd(_trend_frame()["close"])
    assert out["macd"].iloc[-1] > 0
    assert out["macd_hist"].iloc[-1] > 0


def test_bollinger_band_ordering():
    out = bollinger(_trend_frame()["close"])
    assert out["bb_upper"].iloc[-1] > out["bb_mid"].iloc[-1] > out["bb_lower"].iloc[-1]


def test_stochastic_high_on_uptrend():
    out = stochastic(_trend_frame(), 14, 3)
    assert out["stoch_k"].iloc[-1] > 90


def test_obv_rising_with_price():
    out = obv(_trend_frame(), 10)
    assert out["obv_slope"].iloc[-1] > 0


def test_add_indicators_relative_strength_vs_benchmark():
    stock = _trend_frame(n=120, step=2.0)
    bench = _trend_frame(n=120, step=1.0)[["date", "close"]]
    out = add_indicators(stock, benchmark=bench)
    assert out["rs"].iloc[-1] > 0
    assert {"adx14", "macd_hist", "bb_pctb", "stoch_k", "dist_52w_high", "atr_pct", "rs"} <= set(
        out.columns
    )
