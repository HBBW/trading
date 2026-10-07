from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger

from .config import settings
from .scanner import run_scan
from .universe import seed_universe

log = logging.getLogger(__name__)


def _intraday_triggers() -> OrTrigger:
    slots: set[tuple[int, int]] = set()
    for start, end in settings.sessions():
        minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        while minutes <= end_minutes:
            slots.add((minutes // 60, minutes % 60))
            minutes += settings.intraday_minutes
    triggers = [
        CronTrigger(day_of_week="mon-fri", hour=h, minute=m, timezone=settings.timezone)
        for h, m in sorted(slots)
    ]
    return OrTrigger(triggers)


def intraday_job() -> None:
    if not settings.in_market_hours():
        return
    try:
        run_scan(mode="intraday")
    except Exception:  # noqa: BLE001
        log.exception("intraday scan failed")


def eod_job() -> None:
    try:
        run_scan(mode="eod")
    except Exception:  # noqa: BLE001
        log.exception("EOD scan failed")


def universe_job() -> None:
    try:
        count = seed_universe(refresh=True)
        log.info("universe refreshed: %s tickers", count)
    except Exception:  # noqa: BLE001
        log.exception("universe refresh failed")


def build_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone=settings.timezone)
    sched.add_job(
        eod_job,
        CronTrigger(
            day_of_week="mon-fri",
            hour=settings.eod_hour,
            minute=settings.eod_minute,
            timezone=settings.timezone,
        ),
        id="eod_scan",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    sched.add_job(
        intraday_job,
        _intraday_triggers(),
        id="intraday_scan",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=600,
    )
    sched.add_job(
        universe_job,
        CronTrigger(day_of_week="sun", hour=8, minute=0, timezone=settings.timezone),
        id="universe_refresh",
        max_instances=1,
        coalesce=True,
    )
    return sched
