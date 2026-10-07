import numpy as np
import pandas as pd
import pytest

from app.indicators import atr, ema, rsi, sma

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
