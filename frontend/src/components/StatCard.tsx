import type { ReactNode } from "react";

export function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
}) {
  return (
    <div className="border border-line bg-surface px-3 py-2.5">
      <div className="text-[11px] font-medium text-faint">{label}</div>
      <div className="mt-1 font-mono text-base leading-none">{value}</div>
      {hint ? <div className="mt-1.5 text-[11px] text-muted">{hint}</div> : null}
    </div>
  );
}
