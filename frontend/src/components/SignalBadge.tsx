function tone(signal: string): string {
  if (signal.startsWith("POTENTIAL")) return "border-pos-line bg-pos-bg text-pos";
  if (signal === "WATCHLIST") return "border-warn-line bg-warn-bg text-warn";
  return "border-line bg-surface-2 text-muted";
}

export function SignalBadge({ signal }: { signal: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-sm border px-1.5 py-0.5 text-[11px] font-semibold ${tone(signal)}`}
    >
      {signal}
    </span>
  );
}
