import type { ScanResult } from "./types";

export type Category = "swing" | "scalp" | "day" | "overnight";
export type SortKey =
  | "symbol"
  | "sector"
  | "score"
  | "close"
  | "rsi"
  | "vol"
  | "entry"
  | "cl"
  | "tp1"
  | "tp2";
export interface SortState {
  key: SortKey;
  dir: "asc" | "desc";
}

export interface RowFields {
  score: number | null;
  signal: string | null;
  entry: number | null;
  cl: number | null;
  tp1: number | null;
  tp2: number | null;
}

export const CATEGORIES: Category[] = ["swing", "scalp", "day", "overnight"];

export function rowFields(r: ScanResult, category: Category): RowFields {
  switch (category) {
    case "scalp":
      return {
        score: r.scalp_score,
        signal: r.scalp_signal,
        entry: r.scalp_entry,
        cl: r.scalp_stop_loss,
        tp1: r.scalp_tp1,
        tp2: r.scalp_tp2,
      };
    case "day":
      return {
        score: r.day_score,
        signal: r.day_signal,
        entry: r.day_entry,
        cl: r.day_stop_loss,
        tp1: r.day_tp1,
        tp2: r.day_tp2,
      };
    case "overnight":
      return {
        score: r.overnight_score,
        signal: r.overnight_signal,
        entry: r.overnight_entry,
        cl: r.overnight_stop_loss,
        tp1: r.overnight_tp1,
        tp2: r.overnight_tp2,
      };
    default:
      return {
        score: r.score,
        signal: r.signal,
        entry: r.entry,
        cl: r.stop_loss,
        tp1: r.tp1,
        tp2: r.tp2,
      };
  }
}
