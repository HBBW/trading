import numpy as np
import pandas as pd
import pytest

from app.config import settings
from app.strategy import (
    evaluate,
    evaluate_daytrade,
    evaluate_overnight,
    evaluate_scalp,
)


def make_frame(n: int = 260) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=n)
    close = np.full(n, 100.0)
    df = pd.DataFrame(
        {
            "date": dates,
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": np.full(n, 1_000_000.0),
        }
    )
    df["ema20"] = 99.0
    df["ema50"] = 96.0
    df["sma200"] = 80.0
    df["rsi14"] = 50.0
    df["vol_avg20"] = 100_000.0
    df["atr14"] = 2.0
    df["value_avg20"] = 2_000_000_000.0
    return df


def test_perfect_setup_scores_100_and_buy():
    df = make_frame()
    df.loc[df.index[-3]:, "rsi14"] = [50.0, 40.0, 42.0]
    df.loc[df.index[-1], "volume"] = 200_000.0
    df.loc[df.index[-2], "high"] = 98.0

    ev = evaluate(df, settings)

    assert ev is not None
    assert ev["liquid"] is True
    assert all(ev["checks"].values())
    assert ev["score"] == 100.0
    assert ev["signal"] == "POTENTIAL BUY"
    plan = ev["plan"]
    assert plan["entry"] == 100.0
    assert plan["stop_loss"] == 95.0
    assert plan["tp1"] == 110.0
    assert plan["tp2"] == 115.0
    assert plan["risk_reward"] == 3.0


def test_watchlist_when_partial():
    df = make_frame()
    df.loc[df.index[-3]:, "rsi14"] = [50.0, 46.0, 48.0]
    df.loc[df.index[-1], "volume"] = 120_000.0
    df["ema50"] = 90.0

    ev = evaluate(df, settings)

    assert ev is not None
    assert ev["score"] == 65.0
    assert ev["signal"] == "WATCHLIST"


def test_swing_stop_capped_at_max_pct():
    df = make_frame()
    df.loc[df.index[-10]:, "low"] = 50.0

    ev = evaluate(df, settings)

    assert ev is not None
    assert ev["plan"]["stop_loss"] == 88.0


def test_strong_score_without_pullback_is_watchlist():
    df = make_frame()
    df.loc[df.index[-3]:, "rsi14"] = [50.0, 46.0, 48.0]
    df.loc[df.index[-1], "volume"] = 200_000.0
    df.loc[df.index[-2], "high"] = 98.0

    ev = evaluate(df, settings)

    assert ev is not None
    assert ev["score"] >= 75
    assert ev["signal"] == "WATCHLIST"


def test_illiquid_is_flagged():
    df = make_frame()
    df["value_avg20"] = 1_000_000.0

    ev = evaluate(df, settings)

    assert ev is not None
    assert ev["liquid"] is False
    assert ev["checks"]["value_avg"] is False


def test_no_history_returns_none():
    assert evaluate(pd.DataFrame(), settings) is None
    assert evaluate(None, settings) is None


def make_scalp_ready_frame() -> pd.DataFrame:
    df = make_frame()
    df["vol_avg20"] = 600_000.0
    df["value_avg20"] = 6_000_000_000.0
    df["ema20"] = 99.0
    df.loc[df.index[-1], "low"] = 98.0
    df.loc[df.index[-1], "volume"] = 1_000_000.0
    df.loc[df.index[-3]:, "rsi14"] = [55.0, 55.0, 60.0]
    df.loc[df.index[-2], "high"] = 98.0
    return df


def test_scalp_ready_with_tight_levels():
    ev = evaluate_scalp(make_scalp_ready_frame(), settings)

    assert ev is not None
    assert ev["score"] == 100.0
    assert ev["signal"] == "POTENTIAL SCALP"
    plan = ev["plan"]
    assert plan["entry"] == 100.0
    assert plan["stop_loss"] == 98.0
    assert plan["tp1"] == 102.0
    assert plan["tp2"] == 104.0
    assert plan["risk_reward"] == 2.0


def test_scalp_rsi_out_of_range_blocks_ready():
    df = make_scalp_ready_frame()
    df.loc[df.index[-1], "rsi14"] = 75.0

    ev = evaluate_scalp(df, settings)

    assert ev is not None
    assert ev["signal"] == "WATCHLIST"
    assert ev["checks"]["rsi_ok"] is False


def test_scalp_cut_loss_capped_at_two_percent():
    df = make_scalp_ready_frame()
    df.loc[df.index[-1], "low"] = 90.0
    df.loc[df.index[-1], "atr14"] = 4.0

    ev = evaluate_scalp(df, settings)

    assert ev is not None
    assert ev["plan"]["stop_loss"] == 98.0


def make_day_ready_frame() -> pd.DataFrame:
    df = make_frame()
    df["vol_avg20"] = 600_000.0
    df["value_avg20"] = 6_000_000_000.0
    df.loc[df.index[-20:], "low"] = 98.0
    df.loc[df.index[-2], "high"] = 98.0
    df.loc[df.index[-2], "low"] = 95.0
    df.loc[df.index[-1], "volume"] = 1_000_000.0
    df.loc[df.index[-3]:, "rsi14"] = [55.0, 55.0, 60.0]
    return df


def test_daytrade_ready_with_range_levels():
    ev = evaluate_daytrade(make_day_ready_frame(), settings)

    assert ev is not None
    assert ev["score"] == 100.0
    assert ev["signal"] == "POTENTIAL DAY"
    plan = ev["plan"]
    assert plan["entry"] == 100.0
    assert plan["stop_loss"] == pytest.approx(98.65, abs=0.01)
    assert plan["tp1"] == pytest.approx(101.5, abs=0.01)
    assert plan["tp2"] == pytest.approx(102.4, abs=0.01)
    assert plan["risk_reward"] == 1.8


def test_daytrade_without_breakout_is_watchlist():
    df = make_day_ready_frame()
    df.loc[df.index[-2], "high"] = 101.0

    ev = evaluate_daytrade(df, settings)

    assert ev is not None
    assert ev["signal"] == "WATCHLIST"
    assert ev["checks"]["close_above_prev_high"] is False


def make_overnight_ready_frame() -> pd.DataFrame:
    df = make_frame()
    df["vol_avg20"] = 600_000.0
    df["value_avg20"] = 6_000_000_000.0
    df.loc[df.index[-20:], "low"] = 98.0
    df.loc[df.index[-20:], "high"] = 100.8
    df.loc[df.index[-1], "volume"] = 1_000_000.0
    df.loc[df.index[-3]:, "rsi14"] = [55.0, 55.0, 60.0]
    return df


def test_overnight_ready_with_range_levels():
    ev = evaluate_overnight(make_overnight_ready_frame(), settings)

    assert ev is not None
    assert ev["score"] == 85.0
    assert ev["signal"] == "POTENTIAL OVERNIGHT"
    plan = ev["plan"]
    assert plan["entry"] == 100.0
    assert plan["stop_loss"] == pytest.approx(99.16, abs=0.01)
    assert plan["tp1"] == pytest.approx(100.98, abs=0.01)
    assert plan["tp2"] == pytest.approx(101.68, abs=0.01)
    assert plan["risk_reward"] == 2.0


def test_overnight_weak_close_is_not_ready():
    df = make_overnight_ready_frame()
    df.loc[df.index[-1], "high"] = 104.0
    df.loc[df.index[-1], "low"] = 96.0

    ev = evaluate_overnight(df, settings)

    assert ev is not None
    assert ev["signal"] == "WATCHLIST"
    assert ev["checks"]["strong_close"] is False
