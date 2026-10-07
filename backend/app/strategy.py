from __future__ import annotations

import pandas as pd

from .config import Settings, settings


def _f(value) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _r(value: float | None, nd: int = 2) -> float | None:
    return None if value is None else round(value, nd)


_QUALITY_WEIGHTS = {
    "adx_strong": 0.30,
    "rs_positive": 0.25,
    "macd_bull": 0.15,
    "stoch_bull": 0.10,
    "near_52w_high": 0.10,
    "bb_above_mid": 0.05,
    "obv_rising": 0.05,
}


def _num_at(row, key: str) -> float | None:
    if key not in row.index:
        return None
    value = row.get(key)
    if value is None or pd.isna(value):
        return None
    return float(value)


def _bandwidth_rank(df: pd.DataFrame, cfg: Settings) -> float | None:
    if "bb_bandwidth" not in df.columns:
        return None
    series = df["bb_bandwidth"].dropna()
    if len(series) < 30:
        return None
    last = float(series.iloc[-1])
    window = series.iloc[-120:]
    return float((window <= last).mean() * 100.0)


def _quality(df: pd.DataFrame, cfg: Settings) -> tuple[dict[str, bool], float]:
    """Trend/momentum quality checks from the extended indicator set.

    Missing indicators are omitted so frames without the extended columns
    (e.g. older scans or synthetic test frames) keep the base behaviour.
    """
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    checks: dict[str, bool] = {}

    adx = _num_at(last, "adx14")
    if adx is not None:
        checks["adx_strong"] = adx >= cfg.adx_min
    rs = _num_at(last, "rs")
    if rs is not None:
        checks["rs_positive"] = rs >= 0
    macd_hist = _num_at(last, "macd_hist")
    if macd_hist is not None:
        checks["macd_bull"] = macd_hist > 0
    stoch_k = _num_at(last, "stoch_k")
    stoch_d = _num_at(last, "stoch_d")
    stoch_k_prev = _num_at(prev, "stoch_k")
    if stoch_k is not None and stoch_d is not None:
        checks["stoch_bull"] = stoch_k >= stoch_d and (
            stoch_k_prev is None or stoch_k >= stoch_k_prev
        )
    pctb = _num_at(last, "bb_pctb")
    if pctb is not None:
        checks["bb_above_mid"] = pctb >= 0.5
    rank = _bandwidth_rank(df, cfg)
    if rank is not None:
        checks["bb_squeeze"] = rank <= cfg.bb_squeeze_pct
    dist52 = _num_at(last, "dist_52w_high")
    if dist52 is not None:
        checks["near_52w_high"] = dist52 >= -cfg.near_52w_high_pct
    obv_slope = _num_at(last, "obv_slope")
    if obv_slope is not None:
        checks["obv_rising"] = obv_slope > 0

    score = sum(w for key, w in _QUALITY_WEIGHTS.items() if checks.get(key)) * cfg.w_quality
    return checks, score


def _quality_gate(checks: dict[str, bool]) -> bool:
    """POTENTIAL signals need a non-choppy trend and index outperformance when known."""
    return checks.get("adx_strong", True) and checks.get("rs_positive", True)


def evaluate(df: pd.DataFrame, cfg: Settings | None = None) -> dict | None:
    """Evaluate the last bar of an OHLCV+indicator frame. Returns None if insufficient data."""
    cfg = cfg or settings
    if df is None or len(df) < 2:
        return None
    last = df.iloc[-1]
    prev = df.iloc[-2]

    close = _f(last["close"])
    rsi_now = _f(last["rsi14"])
    rsi_prev = _f(prev["rsi14"])
    ema20 = _f(last["ema20"])
    ema50 = _f(last["ema50"])
    sma200 = _f(last["sma200"])
    vol = _f(last["volume"])
    vol_avg = _f(last["vol_avg20"])
    atr14 = _f(last[f"atr{cfg.atr_period}"])
    value_avg = _f(last["value_avg20"])

    required = [close, rsi_now, rsi_prev, ema50, sma200, vol_avg, atr14, value_avg]
    if any(v is None for v in required):
        return None

    liquidity = {
        "price_min": close >= cfg.min_price,
        "value_avg": value_avg >= cfg.min_avg_value_20d,
        "vol_avg": vol_avg >= cfg.min_vol_avg_20d,
    }
    liquid = all(liquidity.values())

    trend = {
        "close_above_ema50": close > ema50,
        "ema50_above_sma200": ema50 > sma200,
    }

    lookback = df["rsi14"].iloc[-cfg.pullback_lookback :]
    pullback = {
        "rsi_pullback": bool((lookback <= cfg.rsi_pullback_max).any()),
        "rsi_rising": rsi_now > rsi_prev,
    }

    volume = {
        "volume_above_avg": vol > vol_avg,
        "volume_strong": vol > vol_avg * cfg.vol_bonus_mult,
    }

    prev_high = _f(prev["high"])
    near_ema50 = ema50 > 0 and abs(close - ema50) / ema50 <= cfg.near_ema50_pct / 100.0
    momentum = {
        "close_above_prev_high": prev_high is not None and close > prev_high,
        "near_ema50": bool(near_ema50),
    }

    quality_checks, quality_score = _quality(df, cfg)
    breakdown = {
        "trend": (
            (cfg.w_trend / 2 if trend["close_above_ema50"] else 0)
            + (cfg.w_trend / 2 if trend["ema50_above_sma200"] else 0)
        ),
        "pullback": (
            (cfg.w_pullback / 2 if pullback["rsi_pullback"] else 0)
            + (cfg.w_pullback / 2 if pullback["rsi_rising"] else 0)
        ),
        "volume": (cfg.w_volume if volume["volume_above_avg"] else 0),
        "bonus": (cfg.vol_bonus if volume["volume_strong"] else 0),
        "momentum": (
            (cfg.w_momentum / 2 if momentum["close_above_prev_high"] else 0)
            + (cfg.w_momentum / 2 if momentum["near_ema50"] else 0)
        ),
        "quality": quality_score,
    }
    score = min(100.0, sum(breakdown.values()))

    signal_ok = (
        liquid
        and trend["close_above_ema50"]
        and trend["ema50_above_sma200"]
        and pullback["rsi_pullback"]
        and pullback["rsi_rising"]
        and volume["volume_above_avg"]
        and _quality_gate(quality_checks)
    )

    if signal_ok and score >= cfg.buy_score:
        signal = "POTENTIAL BUY"
    elif score >= cfg.candidate_score:
        signal = "WATCHLIST"
    else:
        signal = "SKIP"

    swing_low = _f(df["low"].iloc[-cfg.swing_low_bars :].min())
    stop_loss = None
    if swing_low is not None and atr14 is not None:
        stop_loss = min(swing_low, ema50) - cfg.atr_sl_mult * atr14
        stop_loss = max(stop_loss, close * (1 - cfg.swing_max_sl_pct / 100.0))
    risk = close - stop_loss if stop_loss is not None else None
    plan = None
    if risk is not None and risk > 0:
        plan = {
            "entry": _r(close),
            "stop_loss": _r(stop_loss),
            "tp1": _r(close + cfg.tp1_r * risk),
            "tp2": _r(close + cfg.tp2_r * risk),
            "risk_reward": _r(cfg.tp2_r, 1),
            "risk_per_share": _r(risk),
            "swing_low": _r(swing_low),
        }

    return {
        "data_date": last["date"],
        "close": _r(close),
        "rsi": _r(rsi_now),
        "rsi_prev": _r(rsi_prev),
        "ema20": _r(ema20),
        "ema50": _r(ema50),
        "sma200": _r(sma200),
        "vol_avg20": _r(vol_avg, 0),
        "atr14": _r(atr14),
        "value_avg20": _r(value_avg, 0),
        "volume": int(vol),
        "adx14": _r(_num_at(last, "adx14")),
        "di_plus14": _r(_num_at(last, "di_plus14")),
        "di_minus14": _r(_num_at(last, "di_minus14")),
        "macd": _r(_num_at(last, "macd")),
        "macd_signal": _r(_num_at(last, "macd_signal")),
        "macd_hist": _r(_num_at(last, "macd_hist")),
        "bb_bandwidth": _r(_num_at(last, "bb_bandwidth")),
        "bb_pctb": _r(_num_at(last, "bb_pctb")),
        "stoch_k": _r(_num_at(last, "stoch_k")),
        "stoch_d": _r(_num_at(last, "stoch_d")),
        "dist_52w_high": _r(_num_at(last, "dist_52w_high")),
        "atr_pct": _r(_num_at(last, "atr_pct")),
        "rs": _r(_num_at(last, "rs")),
        "obv_slope": _r(_num_at(last, "obv_slope"), 0),
        "liquid": liquid,
        "checks": {**liquidity, **trend, **pullback, **volume, **momentum, **quality_checks},
        "breakdown": breakdown,
        "score": _r(score, 1),
        "signal": signal,
        "plan": plan,
    }


def evaluate_scalp(df: pd.DataFrame, cfg: Settings | None = None) -> dict | None:
    """Short-term momentum profile ("scalping") on daily bars.

    Entry is the last close (executed next session), cut loss is structural
    (under the day's low) but capped at scalp_cl_max_pct from entry.
    """
    cfg = cfg or settings
    if df is None or len(df) < 2:
        return None
    last = df.iloc[-1]
    prev = df.iloc[-2]

    close = _f(last["close"])
    high = _f(last["high"])
    low = _f(last["low"])
    rsi_now = _f(last["rsi14"])
    rsi_prev = _f(prev["rsi14"])
    ema20 = _f(last["ema20"])
    ema50 = _f(last["ema50"])
    vol = _f(last["volume"])
    vol_avg = _f(last["vol_avg20"])
    atr14 = _f(last[f"atr{cfg.atr_period}"])
    value_avg = _f(last["value_avg20"])
    prev_high = _f(prev["high"])

    required = [
        close, high, low, rsi_now, rsi_prev, ema20, ema50,
        vol, vol_avg, atr14, value_avg, prev_high,
    ]
    if any(v is None for v in required):
        return None

    day_range = high - low
    close_pos = (close - low) / day_range if day_range > 0 else 0.0

    liquidity = {
        "price_min": close >= cfg.scalp_min_price,
        "value_avg": value_avg >= cfg.scalp_min_avg_value_20d,
        "vol_avg": vol_avg >= cfg.scalp_min_vol_avg_20d,
    }
    liquid = all(liquidity.values())
    trend = {
        "close_above_ema20": close > ema20,
        "ema20_above_ema50": ema20 > ema50,
    }
    momentum = {
        "close_above_prev_high": close > prev_high,
        "strong_close": close_pos >= cfg.scalp_min_close_pos,
    }
    volume = {
        "volume_above_avg": vol > vol_avg,
        "volume_strong": vol >= vol_avg * cfg.scalp_vol_mult,
    }
    rsi_ok = cfg.scalp_rsi_min <= rsi_now <= cfg.scalp_rsi_max

    quality_checks, quality_score = _quality(df, cfg)
    breakdown = {
        "liquidity": (cfg.scalp_w_liquidity / 2 if liquidity["value_avg"] else 0)
        + (cfg.scalp_w_liquidity / 2 if liquidity["vol_avg"] else 0),
        "trend": (cfg.scalp_w_trend / 2 if trend["close_above_ema20"] else 0)
        + (cfg.scalp_w_trend / 2 if trend["ema20_above_ema50"] else 0),
        "momentum": (cfg.scalp_w_momentum / 2 if momentum["close_above_prev_high"] else 0)
        + (cfg.scalp_w_momentum / 2 if momentum["strong_close"] else 0),
        "volume": (cfg.scalp_w_volume * 0.4 if volume["volume_above_avg"] else 0)
        + (cfg.scalp_w_volume * 0.6 if volume["volume_strong"] else 0),
        "quality": quality_score,
    }
    score = min(100.0, sum(breakdown.values()))

    ready = (
        liquid
        and all(trend.values())
        and all(momentum.values())
        and volume["volume_strong"]
        and rsi_ok
        and _quality_gate(quality_checks)
    )
    if ready and score >= cfg.scalp_ready_score:
        signal = "POTENTIAL SCALP"
    elif score >= cfg.scalp_candidate_score:
        signal = "WATCHLIST"
    else:
        signal = "SKIP"

    stop_loss = max(low - cfg.scalp_cl_atr_mult * atr14, close * (1 - cfg.scalp_cl_max_pct / 100.0))
    risk = close - stop_loss
    plan = None
    if risk > 0:
        plan = {
            "entry": _r(close),
            "stop_loss": _r(stop_loss),
            "tp1": _r(close + cfg.scalp_tp1_r * risk),
            "tp2": _r(close + cfg.scalp_tp2_r * risk),
            "risk_reward": _r(cfg.scalp_tp2_r, 1),
            "risk_per_share": _r(risk),
            "swing_low": _r(low),
        }

    return {
        "score": _r(score, 1),
        "signal": signal,
        "liquid": liquid,
        "checks": {**liquidity, **trend, **momentum, **volume, "rsi_ok": rsi_ok, **quality_checks},
        "breakdown": breakdown,
        "plan": plan,
        "close": _r(close),
        "rsi": _r(rsi_now),
        "rsi_prev": _r(rsi_prev),
    }


def _range_avg20(df: pd.DataFrame, close: float) -> float:
    finite = df["high"] - df["low"]
    value = finite.iloc[-20:].mean()
    if pd.isna(value) or value <= 0:
        return max(close * 0.02, 1.0)
    return float(value)


def trade_block(ev: dict | None) -> dict | None:
    if ev is None:
        return None
    return {
        "score": ev["score"],
        "signal": ev["signal"],
        "checks": ev["checks"],
        "breakdown": ev["breakdown"],
        "plan": ev["plan"],
    }


def evaluate_daytrade(df: pd.DataFrame, cfg: Settings | None = None) -> dict | None:
    """Beli pagi (dekat open), jual sore (dekat close) di hari yang sama.

    Levels are statistical estimates from the 20-bar average daily range.
    """
    cfg = cfg or settings
    if df is None or len(df) < 2:
        return None
    last = df.iloc[-1]
    prev = df.iloc[-2]

    close = _f(last["close"])
    high = _f(last["high"])
    low = _f(last["low"])
    rsi_now = _f(last["rsi14"])
    ema20 = _f(last["ema20"])
    ema50 = _f(last["ema50"])
    vol = _f(last["volume"])
    vol_avg = _f(last["vol_avg20"])
    value_avg = _f(last["value_avg20"])
    prev_high = _f(prev["high"])

    required = [close, high, low, rsi_now, ema20, ema50, vol, vol_avg, value_avg, prev_high]
    if any(v is None for v in required):
        return None

    day_range = high - low
    close_pos = (close - low) / day_range if day_range > 0 else 0.0
    range20 = _range_avg20(df, close)

    liquidity = {
        "price_min": close >= cfg.day_min_price,
        "value_avg": value_avg >= cfg.day_min_avg_value_20d,
        "vol_avg": vol_avg >= cfg.day_min_vol_avg_20d,
    }
    liquid = all(liquidity.values())
    trend = {
        "close_above_ema20": close > ema20,
        "ema20_above_ema50": ema20 > ema50,
    }
    momentum = {
        "close_above_prev_high": close > prev_high,
        "strong_close": close_pos >= cfg.day_min_close_pos,
    }
    volume = {
        "volume_above_avg": vol > vol_avg,
        "volume_strong": vol >= vol_avg * cfg.day_vol_mult,
    }
    rsi_ok = cfg.day_rsi_min <= rsi_now <= cfg.day_rsi_max

    quality_checks, quality_score = _quality(df, cfg)
    breakdown = {
        "liquidity": (cfg.day_w_liquidity / 2 if liquidity["value_avg"] else 0)
        + (cfg.day_w_liquidity / 2 if liquidity["vol_avg"] else 0),
        "trend": (cfg.day_w_trend / 2 if trend["close_above_ema20"] else 0)
        + (cfg.day_w_trend / 2 if trend["ema20_above_ema50"] else 0),
        "momentum": (cfg.day_w_momentum / 2 if momentum["close_above_prev_high"] else 0)
        + (cfg.day_w_momentum / 2 if momentum["strong_close"] else 0),
        "volume": (cfg.day_w_volume * 0.4 if volume["volume_above_avg"] else 0)
        + (cfg.day_w_volume * 0.6 if volume["volume_strong"] else 0),
        "quality": quality_score,
    }
    score = min(100.0, sum(breakdown.values()))

    ready = (
        liquid
        and all(trend.values())
        and all(momentum.values())
        and volume["volume_strong"]
        and rsi_ok
        and _quality_gate(quality_checks)
    )
    if ready and score >= cfg.day_ready_score:
        signal = "POTENTIAL DAY"
    elif score >= cfg.day_candidate_score:
        signal = "WATCHLIST"
    else:
        signal = "SKIP"

    stop_loss = close - cfg.day_cl_range_mult * range20
    risk = close - stop_loss
    plan = None
    if risk > 0:
        plan = {
            "entry": _r(close),
            "stop_loss": _r(stop_loss),
            "tp1": _r(close + cfg.day_tp1_range_mult * range20),
            "tp2": _r(close + cfg.day_tp2_range_mult * range20),
            "risk_reward": _r(cfg.day_tp2_range_mult / cfg.day_cl_range_mult, 1),
            "risk_per_share": _r(risk),
            "swing_low": _r(low),
        }

    return {
        "score": _r(score, 1),
        "signal": signal,
        "liquid": liquid,
        "checks": {**liquidity, **trend, **momentum, **volume, "rsi_ok": rsi_ok, **quality_checks},
        "breakdown": breakdown,
        "plan": plan,
        "close": _r(close),
        "rsi": _r(rsi_now),
        "rsi_prev": _f(prev["rsi14"]),
    }


def evaluate_overnight(df: pd.DataFrame, cfg: Settings | None = None) -> dict | None:
    """Beli sore (di close), jual pagi berikutnya.

    Levels are statistical estimates from the 20-bar average daily range.
    """
    cfg = cfg or settings
    if df is None or len(df) < 2:
        return None
    last = df.iloc[-1]
    prev = df.iloc[-2]

    close = _f(last["close"])
    high = _f(last["high"])
    low = _f(last["low"])
    rsi_now = _f(last["rsi14"])
    ema20 = _f(last["ema20"])
    ema50 = _f(last["ema50"])
    vol = _f(last["volume"])
    vol_avg = _f(last["vol_avg20"])
    value_avg = _f(last["value_avg20"])
    prev_high = _f(prev["high"])

    required = [close, high, low, rsi_now, ema20, ema50, vol, vol_avg, value_avg, prev_high]
    if any(v is None for v in required):
        return None

    day_range = high - low
    close_pos = (close - low) / day_range if day_range > 0 else 0.0
    range20 = _range_avg20(df, close)

    liquidity = {
        "price_min": close >= cfg.overnight_min_price,
        "value_avg": value_avg >= cfg.overnight_min_avg_value_20d,
        "vol_avg": vol_avg >= cfg.overnight_min_vol_avg_20d,
    }
    liquid = all(liquidity.values())
    trend = {
        "close_above_ema20": close > ema20,
        "ema20_above_ema50": ema20 > ema50,
    }
    momentum = {
        "close_above_prev_high": close > prev_high,
        "strong_close": close_pos >= cfg.overnight_min_close_pos,
    }
    volume = {
        "volume_above_avg": vol > vol_avg,
        "volume_strong": vol >= vol_avg * cfg.overnight_vol_mult,
    }
    rsi_ok = cfg.overnight_rsi_min <= rsi_now <= cfg.overnight_rsi_max

    quality_checks, quality_score = _quality(df, cfg)
    breakdown = {
        "liquidity": (cfg.overnight_w_liquidity / 2 if liquidity["value_avg"] else 0)
        + (cfg.overnight_w_liquidity / 2 if liquidity["vol_avg"] else 0),
        "trend": (cfg.overnight_w_trend * 0.6 if trend["close_above_ema20"] else 0)
        + (cfg.overnight_w_trend * 0.4 if trend["ema20_above_ema50"] else 0),
        "momentum": (cfg.overnight_w_momentum / 2 if momentum["close_above_prev_high"] else 0)
        + (cfg.overnight_w_momentum / 2 if momentum["strong_close"] else 0),
        "volume": (cfg.overnight_w_volume * 0.4 if volume["volume_above_avg"] else 0)
        + (cfg.overnight_w_volume * 0.6 if volume["volume_strong"] else 0),
        "quality": quality_score,
    }
    score = min(100.0, sum(breakdown.values()))

    ready = (
        liquid
        and trend["close_above_ema20"]
        and momentum["strong_close"]
        and volume["volume_strong"]
        and rsi_ok
        and _quality_gate(quality_checks)
    )
    if ready and score >= cfg.overnight_ready_score:
        signal = "POTENTIAL OVERNIGHT"
    elif score >= cfg.overnight_candidate_score:
        signal = "WATCHLIST"
    else:
        signal = "SKIP"

    stop_loss = close - cfg.overnight_cl_range_mult * range20
    risk = close - stop_loss
    plan = None
    if risk > 0:
        plan = {
            "entry": _r(close),
            "stop_loss": _r(stop_loss),
            "tp1": _r(close + cfg.overnight_tp1_range_mult * range20),
            "tp2": _r(close + cfg.overnight_tp2_range_mult * range20),
            "risk_reward": _r(cfg.overnight_tp2_range_mult / cfg.overnight_cl_range_mult, 1),
            "risk_per_share": _r(risk),
            "swing_low": _r(low),
        }

    return {
        "score": _r(score, 1),
        "signal": signal,
        "liquid": liquid,
        "checks": {**liquidity, **trend, **momentum, **volume, "rsi_ok": rsi_ok, **quality_checks},
        "breakdown": breakdown,
        "plan": plan,
        "close": _r(close),
        "rsi": _r(rsi_now),
        "rsi_prev": _f(prev["rsi14"]),
    }
