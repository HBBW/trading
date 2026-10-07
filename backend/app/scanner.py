from __future__ import annotations

import argparse
import json
import logging
import uuid
from datetime import datetime

from .config import settings
from .data import store
from .data.fetcher import update_price_cache
from .indicators import add_indicators
from .strategy import evaluate, evaluate_daytrade, evaluate_overnight, evaluate_scalp
from .universe import seed_universe

log = logging.getLogger(__name__)


def run_scan(
    mode: str = "manual",
    symbols: list[str] | None = None,
    limit: int | None = None,
    fetch: bool = True,
) -> dict:
    store.init_db()
    universe = store.get_universe()
    if universe.empty:
        seed_universe()
        universe = store.get_universe()

    target = [s.upper().strip() for s in symbols] if symbols else universe["symbol"].tolist()
    if limit:
        target = target[:limit]

    started = datetime.now(settings.tz)
    run_id = f"{mode}-{started:%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"
    store.create_scan_run(run_id, mode, len(target), started.isoformat())

    fetched = 0
    errors: list[str] = []
    if fetch:
        try:
            fetched, errors = update_price_cache(target)
        except Exception as exc:  # noqa: BLE001
            log.exception("cache update failed")
            errors = list(target)
            store.finish_scan_run(
                run_id,
                finished_at=datetime.now(settings.tz).isoformat(),
                status="error",
                message=str(exc)[:500],
            )
            raise
        try:
            update_price_cache([settings.benchmark_symbol])
        except Exception:  # noqa: BLE001 - benchmark is best-effort
            log.warning("benchmark fetch failed: %s", settings.benchmark_symbol)

    benchmark = store.load_ohlcv(settings.benchmark_symbol, settings.history_days)

    results: list[dict] = []
    scanned = 0
    for sym in target:
        try:
            hist = store.load_ohlcv(sym, settings.history_days)
            if hist.empty or len(hist) < 210:
                continue
            frame = add_indicators(hist, settings, benchmark)
            ev = evaluate(frame, settings)
            if ev is None or not ev["liquid"]:
                continue
            scalp = evaluate_scalp(frame, settings)
            day = evaluate_daytrade(frame, settings)
            overnight = evaluate_overnight(frame, settings)
            scalp_plan = (scalp or {}).get("plan") or {}
            day_plan = (day or {}).get("plan") or {}
            overnight_plan = (overnight or {}).get("plan") or {}
            scanned += 1
            plan = ev["plan"] or {}
            results.append(
                {
                    "run_id": run_id,
                    "symbol": sym,
                    "score": ev["score"],
                    "signal": ev["signal"],
                    "close": ev["close"],
                    "rsi": ev["rsi"],
                    "rsi_prev": ev["rsi_prev"],
                    "ema20": ev["ema20"],
                    "ema50": ev["ema50"],
                    "sma200": ev["sma200"],
                    "vol_avg20": ev["vol_avg20"],
                    "atr14": ev["atr14"],
                    "value_avg20": ev["value_avg20"],
                    "volume": ev["volume"],
                    "entry": plan.get("entry"),
                    "stop_loss": plan.get("stop_loss"),
                    "tp1": plan.get("tp1"),
                    "tp2": plan.get("tp2"),
                    "risk_reward": plan.get("risk_reward"),
                    "data_date": ev["data_date"],
                    "breakdown": json.dumps(ev["breakdown"]),
                    "scalp_score": scalp["score"] if scalp else None,
                    "scalp_signal": scalp["signal"] if scalp else None,
                    "scalp_entry": scalp_plan.get("entry"),
                    "scalp_stop_loss": scalp_plan.get("stop_loss"),
                    "scalp_tp1": scalp_plan.get("tp1"),
                    "scalp_tp2": scalp_plan.get("tp2"),
                    "scalp_risk_reward": scalp_plan.get("risk_reward"),
                    "scalp_breakdown": json.dumps(scalp["breakdown"]) if scalp else None,
                    "day_score": day["score"] if day else None,
                    "day_signal": day["signal"] if day else None,
                    "day_entry": day_plan.get("entry"),
                    "day_stop_loss": day_plan.get("stop_loss"),
                    "day_tp1": day_plan.get("tp1"),
                    "day_tp2": day_plan.get("tp2"),
                    "day_risk_reward": day_plan.get("risk_reward"),
                    "day_breakdown": json.dumps(day["breakdown"]) if day else None,
                    "overnight_score": overnight["score"] if overnight else None,
                    "overnight_signal": overnight["signal"] if overnight else None,
                    "overnight_entry": overnight_plan.get("entry"),
                    "overnight_stop_loss": overnight_plan.get("stop_loss"),
                    "overnight_tp1": overnight_plan.get("tp1"),
                    "overnight_tp2": overnight_plan.get("tp2"),
                    "overnight_risk_reward": overnight_plan.get("risk_reward"),
                    "overnight_breakdown": json.dumps(overnight["breakdown"]) if overnight else None,
                    "adx14": ev.get("adx14"),
                    "di_plus14": ev.get("di_plus14"),
                    "di_minus14": ev.get("di_minus14"),
                    "macd": ev.get("macd"),
                    "macd_signal": ev.get("macd_signal"),
                    "macd_hist": ev.get("macd_hist"),
                    "bb_bandwidth": ev.get("bb_bandwidth"),
                    "bb_pctb": ev.get("bb_pctb"),
                    "stoch_k": ev.get("stoch_k"),
                    "stoch_d": ev.get("stoch_d"),
                    "dist_52w_high": ev.get("dist_52w_high"),
                    "atr_pct": ev.get("atr_pct"),
                    "rs": ev.get("rs"),
                    "obv_slope": ev.get("obv_slope"),
                }
            )
        except Exception:  # noqa: BLE001
            log.exception("scan failed for %s", sym)
            errors.append(sym)

    candidates = sum(1 for r in results if r["score"] >= settings.candidate_score)
    store.save_scan_results(results)
    store.finish_scan_run(
        run_id,
        finished_at=datetime.now(settings.tz).isoformat(),
        status="ok",
        fetched=fetched,
        scanned=scanned,
        candidates=int(candidates),
        errors=len(errors),
        message=f"{len(errors)} symbols failed" if errors else None,
    )
    summary = {
        "run_id": run_id,
        "mode": mode,
        "universe": len(target),
        "rows_fetched": fetched,
        "scanned": scanned,
        "candidates": int(candidates),
        "errors": len(errors),
    }
    log.info("scan done: %s", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="IDX swing screener scan")
    parser.add_argument("--mode", default="manual", help="eod | intraday | manual")
    parser.add_argument("--symbols", default="", help="comma-separated symbols (e.g. BBCA,BBRI)")
    parser.add_argument("--limit", type=int, default=None, help="scan first N tickers")
    parser.add_argument("--no-fetch", action="store_true", help="evaluate cached data only")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
    summary = run_scan(
        mode=args.mode,
        symbols=syms or None,
        limit=args.limit,
        fetch=not args.no_fetch,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
