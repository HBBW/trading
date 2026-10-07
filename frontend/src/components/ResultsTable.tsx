import { Link } from "react-router-dom";
import { fmtPrice, volRatio } from "../lib/format";
import { rowFields, type Category, type SortKey, type SortState } from "../lib/rows";
import type { ScanResult } from "../lib/types";
import { ScoreBadge } from "./ScoreBadge";
import { SignalBadge } from "./SignalBadge";

function Th({
  label,
  k,
  sort,
  onSort,
  align = "left",
}: {
  label: string;
  k: SortKey;
  sort: SortState;
  onSort: (key: SortKey) => void;
  align?: "left" | "right";
}) {
  const active = sort.key === k;
  return (
    <th
      scope="col"
      aria-sort={active ? (sort.dir === "asc" ? "ascending" : "descending") : "none"}
      className={`border-b border-line-strong pb-2 pr-3 font-medium text-muted ${
        align === "right" ? "text-right" : "text-left"
      }`}
    >
      <button
        type="button"
        onClick={() => onSort(k)}
        className="inline-flex items-center gap-1 rounded-sm text-xs hover:text-ink"
      >
        {label}
        {active ? (
          <span aria-hidden="true" className="text-accent">
            {sort.dir === "asc" ? "↑" : "↓"}
          </span>
        ) : null}
      </button>
    </th>
  );
}

export function ResultsTable({
  rows,
  sort,
  onSort,
  category,
}: {
  rows: ScanResult[];
  sort: SortState;
  onSort: (key: SortKey) => void;
  category: Category;
}) {
  return (
    <div className="overflow-x-auto border-y border-line-strong">
      <table className="w-full min-w-[1020px] border-collapse text-sm">
        <caption className="sr-only">
          Hasil scan {category === "scalp" ? "scalping" : "swing"}, dengan level entry, cut loss,
          dan target
        </caption>
        <thead>
          <tr>
            <Th label="Kode" k="symbol" sort={sort} onSort={onSort} />
            <Th label="Sektor" k="sector" sort={sort} onSort={onSort} />
            <Th label="Skor" k="score" sort={sort} onSort={onSort} />
            <th
              scope="col"
              className="border-b border-line-strong pb-2 pr-3 text-left text-xs font-medium text-muted"
            >
              Sinyal
            </th>
            <Th label="Close" k="close" sort={sort} onSort={onSort} align="right" />
            <Th label="RSI" k="rsi" sort={sort} onSort={onSort} align="right" />
            <Th label="Vol" k="vol" sort={sort} onSort={onSort} align="right" />
            <Th label="Entry" k="entry" sort={sort} onSort={onSort} align="right" />
            <Th label="CL" k="cl" sort={sort} onSort={onSort} align="right" />
            <Th label="TP1" k="tp1" sort={sort} onSort={onSort} align="right" />
            <Th label="TP2" k="tp2" sort={sort} onSort={onSort} align="right" />
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const f = rowFields(r, category);
            const vr = volRatio(r.volume, r.vol_avg20);
            return (
              <tr key={r.symbol} className="border-b border-line last:border-b-0 hover:bg-surface-2">
                <td className="py-2.5 pr-3">
                  <Link
                    to={`/ticker/${r.symbol}`}
                    className="font-mono text-sm font-medium hover:text-accent"
                  >
                    {r.symbol}
                  </Link>
                  <div className="max-w-[200px] truncate text-xs text-muted">{r.name ?? "–"}</div>
                </td>
                <td className="py-2.5 pr-3 text-xs text-muted">{r.sector ?? "–"}</td>
                <td className="py-2.5 pr-3">
                  {f.score === null ? (
                    <span className="text-sm text-faint">–</span>
                  ) : (
                    <ScoreBadge score={f.score} />
                  )}
                </td>
                <td className="py-2.5 pr-3">
                  {f.signal === null ? (
                    <span className="text-sm text-faint">–</span>
                  ) : (
                    <SignalBadge signal={f.signal} />
                  )}
                </td>
                <td className="py-2.5 pr-3 text-right font-mono text-sm">{fmtPrice(r.close)}</td>
                <td className="py-2.5 pr-3 text-right font-mono text-sm">
                  {r.rsi === null ? "–" : r.rsi.toFixed(1)}
                </td>
                <td
                  className={`py-2.5 pr-3 text-right font-mono text-sm ${
                    vr !== null && vr >= 1.5 ? "text-pos" : "text-ink"
                  }`}
                >
                  {vr === null ? "–" : `${vr.toFixed(1)}x`}
                </td>
                <td className="py-2.5 pr-3 text-right font-mono text-sm font-medium">
                  {fmtPrice(f.entry)}
                </td>
                <td className="py-2.5 pr-3 text-right font-mono text-sm text-neg">
                  {fmtPrice(f.cl)}
                </td>
                <td className="py-2.5 pr-3 text-right font-mono text-sm text-pos">
                  {fmtPrice(f.tp1)}
                </td>
                <td className="py-2.5 pr-3 text-right font-mono text-sm text-pos">
                  {fmtPrice(f.tp2)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
