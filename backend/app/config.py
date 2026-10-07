from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRADING_", env_file=".env", extra="ignore")

    # paths
    db_path: Path = BASE_DIR / "data" / "screener.duckdb"
    universe_csv: Path = BASE_DIR / "data" / "idx_universe.csv"

    # market / provider
    timezone: str = "Asia/Jakarta"
    ticker_suffix: str = ".JK"
    provider: str = "yfinance"

    # schedule (WIB)
    eod_hour: int = 16
    eod_minute: int = 15
    intraday_minutes: int = 30
    session_morning: str = "09:00-12:00"
    session_afternoon: str = "13:30-15:50"

    # data fetching
    history_days: int = 400
    min_history_bars: int = 220
    batch_size: int = 50
    fetch_retries: int = 3
    fetch_backoff: float = 2.0
    cache_overlap_days: int = 5

    # liquidity pre-filter
    min_price: float = 25.0
    min_avg_value_20d: float = 1_000_000_000.0  # Rp 1 miliar/day avg turnover
    min_vol_avg_20d: float = 100_000.0

    # signal params
    rsi_period: int = 14
    rsi_pullback_max: float = 45.0
    pullback_lookback: int = 3
    near_ema50_pct: float = 5.0
    vol_bonus_mult: float = 1.5
    swing_low_bars: int = 10
    atr_period: int = 14
    atr_sl_mult: float = 0.5
    swing_max_sl_pct: float = 12.0
    tp1_r: float = 2.0
    tp2_r: float = 3.0

    # scoring
    w_trend: float = 30.0
    w_pullback: float = 30.0
    w_volume: float = 20.0
    w_momentum: float = 20.0
    vol_bonus: float = 10.0
    candidate_score: float = 60.0
    buy_score: float = 75.0

    # scalping profile (short-term momentum on daily bars)
    scalp_min_price: float = 100.0
    scalp_min_avg_value_20d: float = 5_000_000_000.0
    scalp_min_vol_avg_20d: float = 500_000.0
    scalp_min_close_pos: float = 0.66
    scalp_rsi_min: float = 50.0
    scalp_rsi_max: float = 72.0
    scalp_vol_mult: float = 1.5
    scalp_cl_max_pct: float = 2.0
    scalp_cl_atr_mult: float = 0.25
    scalp_tp1_r: float = 1.0
    scalp_tp2_r: float = 2.0
    scalp_w_liquidity: float = 20.0
    scalp_w_trend: float = 25.0
    scalp_w_momentum: float = 30.0
    scalp_w_volume: float = 25.0
    scalp_candidate_score: float = 65.0
    scalp_ready_score: float = 80.0

    # day trade profile (buy morning, sell afternoon; levels from 20d avg range)
    day_min_price: float = 100.0
    day_min_avg_value_20d: float = 5_000_000_000.0
    day_min_vol_avg_20d: float = 500_000.0
    day_min_close_pos: float = 0.6
    day_rsi_min: float = 40.0
    day_rsi_max: float = 78.0
    day_vol_mult: float = 1.5
    day_cl_range_mult: float = 0.45
    day_tp1_range_mult: float = 0.5
    day_tp2_range_mult: float = 0.8
    day_w_liquidity: float = 20.0
    day_w_trend: float = 25.0
    day_w_momentum: float = 30.0
    day_w_volume: float = 25.0
    day_candidate_score: float = 65.0
    day_ready_score: float = 80.0

    # overnight profile (buy at close, sell next morning session)
    overnight_min_price: float = 50.0
    overnight_min_avg_value_20d: float = 1_000_000_000.0
    overnight_min_vol_avg_20d: float = 100_000.0
    overnight_min_close_pos: float = 0.7
    overnight_rsi_min: float = 50.0
    overnight_rsi_max: float = 80.0
    overnight_vol_mult: float = 1.2
    overnight_cl_range_mult: float = 0.3
    overnight_tp1_range_mult: float = 0.35
    overnight_tp2_range_mult: float = 0.6
    overnight_w_liquidity: float = 20.0
    overnight_w_trend: float = 25.0
    overnight_w_momentum: float = 30.0
    overnight_w_volume: float = 25.0
    overnight_candidate_score: float = 65.0
    overnight_ready_score: float = 80.0

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    def sessions(self) -> list[tuple[time, time]]:
        out: list[tuple[time, time]] = []
        for spec in (self.session_morning, self.session_afternoon):
            start_s, end_s = spec.split("-")
            out.append((time.fromisoformat(start_s.strip()), time.fromisoformat(end_s.strip())))
        return out

    def in_market_hours(self, dt: datetime | None = None) -> bool:
        now = dt.astimezone(self.tz) if dt is not None else datetime.now(self.tz)
        if now.weekday() >= 5:
            return False
        t = now.time()
        return any(start <= t <= end for start, end in self.sessions())

    def is_trading_day(self, d: date | None = None) -> bool:
        d = d or datetime.now(self.tz).date()
        return d.weekday() < 5


settings = Settings()
