import type { ReactNode } from "react";
import { fmtPrice } from "../lib/format";
import type { Plan } from "../lib/types";

function LevelRow({
  label,
  value,
  tone = "ink",
  note,
}: {
  label: string;
  value: number;
  tone?: "ink" | "neg" | "pos";
  note?: string;
}) {
  const toneClass = tone === "neg" ? "text-neg" : tone === "pos" ? "text-pos" : "text-ink";
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-line py-2 last:border-b-0">
      <span className="text-xs text-muted">
        {label}
        {note ? <span className="ml-1.5 text-faint">{note}</span> : null}
      </span>
      <span className={`font-mono text-sm font-medium ${toneClass}`}>{fmtPrice(value)}</span>
    </div>
  );
}

export function RRCard({
  plan,
  title = "Rencana trade",
  stopLabel = "Stop loss",
  tp1Note = "+2R",
  tp2Note = "+3R",
  note,
}: {
  plan: Plan;
  title?: string;
  stopLabel?: string;
  tp1Note?: string;
  tp2Note?: string;
  note?: ReactNode;
}) {
  const riskPct = plan.entry > 0 ? ((plan.entry - plan.stop_loss) / plan.entry) * 100 : 0;
  return (
    <section className="border border-line bg-surface p-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-xs font-medium text-muted">{title}</h2>
        <span className="font-mono text-sm text-accent">1 : {plan.risk_reward}</span>
      </div>

      <div className="mt-3">
        <LevelRow label="Entry" value={plan.entry} />
        <LevelRow label={stopLabel} value={plan.stop_loss} tone="neg" note={`-${riskPct.toFixed(1)}%`} />
        <LevelRow label="Target 1" value={plan.tp1} tone="pos" note={tp1Note} />
        <LevelRow label="Target 2" value={plan.tp2} tone="pos" note={tp2Note} />
      </div>

      <div className="mt-3 text-[11px] leading-relaxed text-muted">
        {note ?? (
          <>
            Risiko per lembar {fmtPrice(plan.risk_per_share)}. Stop di bawah{" "}
            {fmtPrice(plan.swing_low)} (low 10 bar) dan EMA50, dikurangi 0,5 ATR, dibatasi
            maksimal 12% dari entry.
          </>
        )}
      </div>
    </section>
  );
}
