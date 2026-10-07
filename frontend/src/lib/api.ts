import type { MarketStatus, ScanLatest, TickerDetail } from "./types";

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

type Params = Record<string, string | number | undefined | null>;

async function request<T>(path: string, init?: RequestInit, params?: Params): Promise<T> {
  let url = `${BASE}${path}`;
  if (params) {
    const qs = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") qs.set(key, String(value));
    }
    const s = qs.toString();
    if (s) url += `?${s}`;
  }
  const res = await fetch(url, init);
  if (!res.ok) {
    throw new Error(`Permintaan gagal (${res.status})`);
  }
  return (await res.json()) as T;
}

export const api = {
  marketStatus: () => request<MarketStatus>("/market/status"),
  latestScan: (limit = 200) => request<ScanLatest>("/scan/latest", undefined, { limit }),
  ticker: (symbol: string, days = 180) =>
    request<TickerDetail>(`/ticker/${encodeURIComponent(symbol)}`, undefined, { days }),
  runScan: (mode = "manual") =>
    request<{ status: string; job_id?: string }>("/scan/run", { method: "POST" }, { mode }),
};
