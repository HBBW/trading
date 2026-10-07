export type Signal = "POTENTIAL BUY" | "WATCHLIST" | "SKIP";

export interface ScanRun {
  run_id: string;
  started_at: string | null;
  finished_at: string | null;
  mode: string | null;
  status: string | null;
  universe_size: number | null;
  fetched: number | null;
  scanned: number | null;
  candidates: number | null;
  errors: number | null;
  message: string | null;
}

export interface ScanResult {
  symbol: string;
  name: string | null;
  sector: string | null;
  score: number;
  signal: string;
  close: number | null;
  rsi: number | null;
  rsi_prev: number | null;
  ema20: number | null;
  ema50: number | null;
  sma200: number | null;
  vol_avg20: number | null;
  atr14: number | null;
  value_avg20: number | null;
  volume: number | null;
  entry: number | null;
  stop_loss: number | null;
  tp1: number | null;
  tp2: number | null;
  risk_reward: number | null;
  data_date: string | null;
  breakdown: Record<string, number> | null;
  scalp_score: number | null;
  scalp_signal: string | null;
  scalp_entry: number | null;
  scalp_stop_loss: number | null;
  scalp_tp1: number | null;
  scalp_tp2: number | null;
  scalp_risk_reward: number | null;
  scalp_breakdown: Record<string, number> | null;
  day_score: number | null;
  day_signal: string | null;
  day_entry: number | null;
  day_stop_loss: number | null;
  day_tp1: number | null;
  day_tp2: number | null;
  day_risk_reward: number | null;
  day_breakdown: Record<string, number> | null;
  overnight_score: number | null;
  overnight_signal: string | null;
  overnight_entry: number | null;
  overnight_stop_loss: number | null;
  overnight_tp1: number | null;
  overnight_tp2: number | null;
  overnight_risk_reward: number | null;
  overnight_breakdown: Record<string, number> | null;
  adx14: number | null;
  di_plus14: number | null;
  di_minus14: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_hist: number | null;
  bb_bandwidth: number | null;
  bb_pctb: number | null;
  stoch_k: number | null;
  stoch_d: number | null;
  dist_52w_high: number | null;
  atr_pct: number | null;
  rs: number | null;
  obv_slope: number | null;
}

export interface ScanLatest {
  run: ScanRun | null;
  results: ScanResult[];
}

export interface MarketStatus {
  now: string;
  timezone: string;
  is_trading_day: boolean;
  is_open: boolean;
  session: string | null;
  next_event: string | null;
}

export interface Bar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface SeriesPoint {
  date: string;
  value: number;
}

export interface Plan {
  entry: number;
  stop_loss: number;
  tp1: number;
  tp2: number;
  risk_reward: number;
  risk_per_share: number;
  swing_low: number;
}

export interface EvaluationBlock {
  score: number;
  signal: string;
  checks: Record<string, boolean>;
  breakdown: Record<string, number>;
  plan: Plan | null;
}

export interface TickerEvaluation {
  score: number | null;
  signal: string | null;
  checks: Record<string, boolean> | null;
  breakdown: Record<string, number> | null;
  plan: Plan | null;
  scalp: EvaluationBlock | null;
  day: EvaluationBlock | null;
  overnight: EvaluationBlock | null;
}

export interface TickerDetail {
  symbol: string;
  name: string | null;
  sector: string | null;
  data_date: string | null;
  bars: Bar[];
  indicators: Record<string, number | null>;
  series: Record<string, SeriesPoint[]>;
  evaluation: TickerEvaluation | null;
  error: string | null;
}
