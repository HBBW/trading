import { fmtScore } from "../lib/format";

const TICKS = 10;

export function ScoreBadge({ score, size = "sm" }: { score: number; size?: "sm" | "lg" }) {
  const filled = Math.round(score / 10);
  const tone = score >= 75 ? "bg-pos" : score >= 60 ? "bg-warn" : "bg-line-strong";
  const number = size === "lg" ? "text-3xl font-semibold" : "text-sm font-medium";
  const tick = size === "lg" ? "h-4 w-1.5" : "h-2.5 w-1";
  return (
    <div className="flex items-center gap-2.5" aria-label={`Skor ${fmtScore(score)} dari 100`}>
      <span className={`font-mono ${number}`}>{fmtScore(score)}</span>
      <span className="flex gap-[3px]" aria-hidden="true">
        {Array.from({ length: TICKS }, (_, i) => (
          <span key={i} className={`${tick} ${i < filled ? tone : "bg-line"}`} />
        ))}
      </span>
    </div>
  );
}
