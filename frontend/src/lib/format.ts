const priceFmt = new Intl.NumberFormat("id-ID", { maximumFractionDigits: 2 });
const intFmt = new Intl.NumberFormat("id-ID", { maximumFractionDigits: 0 });
const compactFmt = new Intl.NumberFormat("id-ID", {
  notation: "compact",
  maximumFractionDigits: 1,
});
const dateFmt = new Intl.DateTimeFormat("id-ID", {
  day: "numeric",
  month: "short",
  year: "numeric",
});
const dateTimeFmt = new Intl.DateTimeFormat("id-ID", {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "Asia/Jakarta",
});

export function fmtPrice(value: number | null | undefined): string {
  return value === null || value === undefined ? "–" : priceFmt.format(value);
}

export function fmtInt(value: number | null | undefined): string {
  return value === null || value === undefined ? "–" : intFmt.format(value);
}

export function fmtCompact(value: number | null | undefined): string {
  return value === null || value === undefined ? "–" : compactFmt.format(value);
}

export function fmtScore(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

export function fmtPct(value: number, digits = 1): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(digits)}%`;
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "–";
  return dateFmt.format(new Date(`${iso}T00:00:00`));
}

export function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return "–";
  return dateTimeFmt.format(new Date(iso));
}

export function volRatio(volume: number | null, volAvg: number | null): number | null {
  if (!volume || !volAvg || volAvg <= 0) return null;
  return volume / volAvg;
}
