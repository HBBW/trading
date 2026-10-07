import { useQuery } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { PriceChart } from "../components/PriceChart";
import { RRCard } from "../components/RRCard";
import { ScoreBadge } from "../components/ScoreBadge";
import { SignalBadge } from "../components/SignalBadge";
import { SignalChecklist } from "../components/SignalChecklist";
import { StatCard } from "../components/StatCard";
import { api } from "../lib/api";
import { fmtCompact, fmtDate, fmtPct, fmtPrice } from "../lib/format";
import { CATEGORIES, type Category } from "../lib/rows";
import { btnGhost, btnPrimary } from "../lib/ui";
import type { EvaluationBlock } from "../lib/types";

const SWING_BREAKDOWN = [
  { key: "trend", label: "Tren", max: 30 },
  { key: "pullback", label: "Pullback", max: 30 },
  { key: "volume", label: "Volume", max: 20 },
  { key: "bonus", label: "Bonus volume ≥1,5x", max: 10 },
  { key: "momentum", label: "Momentum", max: 20 },
];

const RANGE_BREAKDOWN = [
  { key: "liquidity", label: "Likuiditas", max: 20 },
  { key: "trend", label: "Tren", max: 25 },
  { key: "momentum", label: "Momentum", max: 30 },
  { key: "volume", label: "Volume", max: 25 },
];

const PLAN_LABELS: Record<Category, string> = {
  swing: "Swing",
  scalp: "Scalping",
  day: "Pagi-Sore",
  overnight: "Sore-Pagi",
};

const SCORE_TITLES: Record<Category, string> = {
  swing: "Skor sinyal swing",
  scalp: "Skor sinyal scalping",
  day: "Skor sinyal pagi-sore",
  overnight: "Skor sinyal sore-pagi",
};

function CenteredPanel({
  title,
  body,
  action,
}: {
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <section className="border border-line bg-surface p-8 text-center">
      <h1 className="font-serif text-lg">{title}</h1>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted">{body}</p>
      {action ? <div className="mt-4 flex justify-center gap-2">{action}</div> : null}
    </section>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-4">
      <span className="sr-only">Memuat detail ticker…</span>
      <div className="h-8 w-48 rounded-sm bg-surface-2 motion-safe:animate-pulse" />
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="h-[480px] rounded-sm border border-line bg-surface motion-safe:animate-pulse" />
        <div className="space-y-4">
          <div className="h-40 rounded-sm border border-line bg-surface motion-safe:animate-pulse" />
          <div className="h-56 rounded-sm border border-line bg-surface motion-safe:animate-pulse" />
        </div>
      </div>
    </div>
  );
}

function PlanToggle({ value, onChange }: { value: Category; onChange: (c: Category) => void }) {
  return (
    <div
      role="group"
      aria-label="Kategori rencana"
      className="inline-flex w-full flex-wrap rounded-sm border border-line bg-surface p-0.5"
    >
      {CATEGORIES.map((cat) => (
        <button
          key={cat}
          type="button"
          aria-pressed={value === cat}
          onClick={() => onChange(cat)}
          className={`h-8 flex-1 rounded-[3px] px-2 text-sm ${
            value === cat ? "bg-surface-2 font-medium text-ink" : "text-muted hover:text-ink"
          }`}
        >
          {PLAN_LABELS[cat]}
        </button>
      ))}
    </div>
  );
}

function ActivePlanCard({ category, block }: { category: Category; block: EvaluationBlock }) {
  const plan = block.plan;
  if (!plan) return null;
  if (category === "scalp") {
    return (
      <RRCard
        plan={plan}
        title="Rencana scalping"
        stopLabel="Cut loss"
        tp1Note="+1R"
        tp2Note="+2R"
        note={
          <>
            Entry dari close terakhir, eksekusi sesi berikutnya. Cut loss di bawah low hari ini (
            {fmtPrice(plan.swing_low)}), dibatasi maksimal 2% dari entry. Risiko per lembar{" "}
            {fmtPrice(plan.risk_per_share)}.
          </>
        }
      />
    );
  }
  if (category === "day") {
    return (
      <RRCard
        plan={plan}
        title="Rencana beli pagi, jual sore"
        stopLabel="Cut loss"
        tp1Note="+0,5 range"
        tp2Note="+0,8 range"
        note={
          <>
            Beli dekat harga open pagi (level entry = acuan dari close terakhir), jual dekat close
            di hari yang sama (time exit). Cut loss -0,45 range harian; risiko per lembar{" "}
            {fmtPrice(plan.risk_per_share)}. Level dari rata-rata range 20 hari.
          </>
        }
      />
    );
  }
  if (category === "overnight") {
    return (
      <RRCard
        plan={plan}
        title="Rencana beli sore, jual pagi"
        stopLabel="Cut loss"
        tp1Note="+0,35 range"
        tp2Note="+0,6 range"
        note={
          <>
            Beli di close sore (harga real), jual di sesi pagi besok. Kalau pagi buka di bawah CL{" "}
            {fmtPrice(plan.stop_loss)}, cut langsung; kalau tidak, jual pagi. Risiko per lembar{" "}
            {fmtPrice(plan.risk_per_share)}. Level dari rata-rata range 20 hari.
          </>
        }
      />
    );
  }
  return <RRCard plan={plan} />;
}

export default function TickerDetail() {
  const { symbol = "" } = useParams();
  const [planCat, setPlanCat] = useState<Category>("swing");

  const market = useQuery({
    queryKey: ["market"],
    queryFn: api.marketStatus,
    refetchInterval: 60_000,
  });
  const q = useQuery({
    queryKey: ["ticker", symbol],
    queryFn: () => api.ticker(symbol, 180),
    refetchInterval: market.data?.is_open ? 30 * 60_000 : false,
    enabled: symbol.length > 0,
  });

  if (q.isPending) return <DetailSkeleton />;

  if (q.isError) {
    return (
      <CenteredPanel
        title="Gagal memuat data"
        body="Tidak bisa menghubungi API. Pastikan backend berjalan di port 8000, lalu coba lagi."
        action={
          <>
            <button type="button" onClick={() => q.refetch()} className={btnPrimary}>
              Coba lagi
            </button>
            <Link to="/" className={btnGhost}>
              Kembali ke scan
            </Link>
          </>
        }
      />
    );
  }

  const data = q.data;
  if (!data || data.error || data.bars.length === 0) {
    return (
      <CenteredPanel
        title={`Data tidak tersedia untuk ${symbol}`}
        body="Tidak ada riwayat harga untuk kode ini. Cek kembali ejaan kodenya, atau kode mungkin baru tercatat dan belum punya riwayat cukup."
        action={
          <Link to="/" className={btnGhost}>
            Kembali ke scan
          </Link>
        }
      />
    );
  }

  const last = data.bars[data.bars.length - 1];
  const prev = data.bars[data.bars.length - 2];
  const change = prev ? last.close - prev.close : null;
  const changePct = prev && prev.close > 0 ? ((last.close - prev.close) / prev.close) * 100 : null;
  const rsiSeries = data.series.rsi14 ?? [];
  const rsiRising =
    rsiSeries.length >= 2 &&
    rsiSeries[rsiSeries.length - 1].value > rsiSeries[rsiSeries.length - 2].value;

  const swingBlock: EvaluationBlock | null =
    data.evaluation && data.evaluation.score !== null && data.evaluation.signal !== null
      ? {
          score: data.evaluation.score,
          signal: data.evaluation.signal,
          checks: data.evaluation.checks ?? {},
          breakdown: data.evaluation.breakdown ?? {},
          plan: data.evaluation.plan,
        }
      : null;
  const blocks: Record<Category, EvaluationBlock | null> = {
    swing: swingBlock,
    scalp: data.evaluation?.scalp ?? null,
    day: data.evaluation?.day ?? null,
    overnight: data.evaluation?.overnight ?? null,
  };
  const availableCats = CATEGORIES.filter((cat) => blocks[cat] !== null);
  const activeCat: Category = blocks[planCat] ? planCat : availableCats[0] ?? "swing";
  const active = blocks[activeCat];
  const breakdownRows = activeCat === "swing" ? SWING_BREAKDOWN : RANGE_BREAKDOWN;

  return (
    <div>
      <Link to="/" className="text-xs text-muted hover:text-ink">
        ← Semua hasil scan
      </Link>

      <div className="mt-3 flex flex-wrap items-baseline gap-x-4 gap-y-1">
        <h1 className="font-mono text-3xl font-semibold">{data.symbol}</h1>
        <span className="text-sm text-muted">{data.name ?? "Nama tidak tercatat"}</span>
        {data.sector ? (
          <span className="rounded-sm border border-line px-1.5 py-0.5 text-[11px] text-muted">
            {data.sector}
          </span>
        ) : null}
        <span className="ml-auto flex items-baseline gap-2 font-mono">
          <span className="text-xl font-medium">Rp {fmtPrice(last.close)}</span>
          {change !== null && changePct !== null ? (
            <span className={`text-sm ${change >= 0 ? "text-pos" : "text-neg"}`}>
              {change >= 0 ? "+" : ""}
              {fmtPrice(change)} ({fmtPct(changePct)})
            </span>
          ) : null}
        </span>
      </div>
      <p className="mt-1 text-xs text-faint">Data per {fmtDate(data.data_date)} (harian, EOD).</p>

      <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="min-w-0 space-y-3">
          <div className="border border-line bg-surface p-3">
            <PriceChart symbol={data.symbol} bars={data.bars} series={data.series} />
          </div>

          <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
            <StatCard
              label="RSI14"
              value={data.indicators.rsi14?.toFixed(1) ?? "–"}
              hint={rsiRising ? "naik dari bar sebelumnya" : "turun dari bar sebelumnya"}
            />
            <StatCard label="EMA20" value={fmtPrice(data.indicators.ema20)} />
            <StatCard label="EMA50" value={fmtPrice(data.indicators.ema50)} />
            <StatCard label="SMA200" value={fmtPrice(data.indicators.sma200)} />
            <StatCard label="ATR14" value={fmtPrice(data.indicators.atr14)} hint="volatilitas harian" />
            <StatCard
              label="Volume rata-rata 20h"
              value={fmtCompact(data.indicators.vol_avg20)}
              hint="lembar/hari"
            />
            <StatCard
              label="Nilai transaksi 20h"
              value={`Rp${fmtCompact(data.indicators.value_avg20)}`}
              hint="per hari"
            />
            <StatCard label="Volume terakhir" value={fmtCompact(last.volume)} hint="lembar" />
          </div>
        </div>

        <div className="space-y-4">
          {availableCats.length > 1 ? <PlanToggle value={planCat} onChange={setPlanCat} /> : null}

          {active ? (
            <section className="border border-line bg-surface p-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xs font-medium text-muted">{SCORE_TITLES[activeCat]}</h2>
                <SignalBadge signal={active.signal} />
              </div>
              <div className="mt-3">
                <ScoreBadge score={active.score} size="lg" />
              </div>
              <div className="mt-4 space-y-2.5">
                {breakdownRows.map((row) => {
                  const value = active.breakdown[row.key] ?? 0;
                  const pct = Math.min(100, (value / row.max) * 100);
                  return (
                    <div key={row.key}>
                      <div className="flex items-baseline justify-between text-xs">
                        <span className="text-muted">{row.label}</span>
                        <span className="font-mono text-muted">
                          {value}/{row.max}
                        </span>
                      </div>
                      <div className="mt-1 h-1 w-full bg-line">
                        <div className="h-1 bg-line-strong" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          ) : (
            <section className="border border-line bg-surface p-4">
              <h2 className="text-xs font-medium text-muted">Skor sinyal</h2>
              <p className="mt-2 text-sm text-muted">
                Riwayat harga belum cukup untuk menilai sinyal. Swing butuh ±210 bar, kategori lain
                ±60 bar.
              </p>
            </section>
          )}

          {active ? <ActivePlanCard category={activeCat} block={active} /> : null}

          {active ? <SignalChecklist checks={active.checks} variant={activeCat} /> : null}
        </div>
      </div>
    </div>
  );
}
