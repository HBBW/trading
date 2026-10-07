export type ChecklistVariant = "swing" | "scalp" | "day" | "overnight";

interface Group {
  title: string;
  items: { key: string; label: string }[];
}

const SWING_GROUPS: Group[] = [
  {
    title: "Likuiditas",
    items: [
      { key: "price_min", label: "Harga ≥ Rp25" },
      { key: "value_avg", label: "Nilai transaksi 20h ≥ Rp1 M" },
      { key: "vol_avg", label: "Volume rata-rata ≥ 100.000 lembar" },
    ],
  },
  {
    title: "Tren",
    items: [
      { key: "close_above_ema50", label: "Close di atas EMA50" },
      { key: "ema50_above_sma200", label: "EMA50 di atas SMA200" },
    ],
  },
  {
    title: "Pullback",
    items: [
      { key: "rsi_pullback", label: "RSI ≤ 45 dalam 3 bar terakhir" },
      { key: "rsi_rising", label: "RSI naik dari bar sebelumnya" },
    ],
  },
  {
    title: "Volume",
    items: [
      { key: "volume_above_avg", label: "Volume di atas rata-rata 20h" },
      { key: "volume_strong", label: "Volume ≥ 1,5x rata-rata" },
    ],
  },
  {
    title: "Momentum",
    items: [
      { key: "close_above_prev_high", label: "Close di atas high kemarin" },
      { key: "near_ema50", label: "Jarak ke EMA50 ≤ 5%" },
    ],
  },
];

const SCALP_GROUPS: Group[] = [
  {
    title: "Likuiditas",
    items: [
      { key: "price_min", label: "Harga ≥ Rp100" },
      { key: "value_avg", label: "Nilai transaksi 20h ≥ Rp5 M" },
      { key: "vol_avg", label: "Volume rata-rata ≥ 500.000 lembar" },
    ],
  },
  {
    title: "Tren pendek",
    items: [
      { key: "close_above_ema20", label: "Close di atas EMA20" },
      { key: "ema20_above_ema50", label: "EMA20 di atas EMA50" },
    ],
  },
  {
    title: "Momentum",
    items: [
      { key: "close_above_prev_high", label: "Close di atas high kemarin (breakout)" },
      { key: "strong_close", label: "Close di 1/3 atas range harian" },
    ],
  },
  {
    title: "Volume",
    items: [
      { key: "volume_above_avg", label: "Volume di atas rata-rata 20h" },
      { key: "volume_strong", label: "Volume ≥ 1,5x rata-rata" },
    ],
  },
  {
    title: "RSI",
    items: [{ key: "rsi_ok", label: "RSI14 antara 50 dan 72" }],
  },
];

const DAY_GROUPS: Group[] = [
  {
    title: "Likuiditas",
    items: [
      { key: "price_min", label: "Harga ≥ Rp100" },
      { key: "value_avg", label: "Nilai transaksi 20h ≥ Rp5 M" },
      { key: "vol_avg", label: "Volume rata-rata ≥ 500.000 lembar" },
    ],
  },
  {
    title: "Tren",
    items: [
      { key: "close_above_ema20", label: "Close di atas EMA20" },
      { key: "ema20_above_ema50", label: "EMA20 di atas EMA50" },
    ],
  },
  {
    title: "Momentum",
    items: [
      { key: "close_above_prev_high", label: "Close di atas high kemarin" },
      { key: "strong_close", label: "Close minimal 60% dari range harian" },
    ],
  },
  {
    title: "Volume",
    items: [
      { key: "volume_above_avg", label: "Volume di atas rata-rata 20h" },
      { key: "volume_strong", label: "Volume ≥ 1,5x rata-rata" },
    ],
  },
  {
    title: "RSI",
    items: [{ key: "rsi_ok", label: "RSI14 antara 40 dan 78" }],
  },
];

const OVERNIGHT_GROUPS: Group[] = [
  {
    title: "Likuiditas",
    items: [
      { key: "price_min", label: "Harga ≥ Rp50" },
      { key: "value_avg", label: "Nilai transaksi 20h ≥ Rp1 M" },
      { key: "vol_avg", label: "Volume rata-rata ≥ 100.000 lembar" },
    ],
  },
  {
    title: "Tren",
    items: [
      { key: "close_above_ema20", label: "Close di atas EMA20" },
      { key: "ema20_above_ema50", label: "EMA20 di atas EMA50" },
    ],
  },
  {
    title: "Close kuat",
    items: [
      { key: "strong_close", label: "Close minimal 70% dari range harian" },
      { key: "close_above_prev_high", label: "Close di atas high kemarin" },
    ],
  },
  {
    title: "Volume",
    items: [
      { key: "volume_above_avg", label: "Volume di atas rata-rata 20h" },
      { key: "volume_strong", label: "Volume ≥ 1,2x rata-rata" },
    ],
  },
  {
    title: "RSI",
    items: [{ key: "rsi_ok", label: "RSI14 antara 50 dan 80" }],
  },
];

const QUALITY_GROUP: Group = {
  title: "Kualitas tren & momentum",
  items: [
    { key: "adx_strong", label: "ADX ≥ 20 (tren tidak sideways)" },
    { key: "rs_positive", label: "Outperform IHSG (RS ≥ 0)" },
    { key: "macd_bull", label: "MACD histogram positif" },
    { key: "stoch_bull", label: "Stochastic bullish (%K ≥ %D)" },
    { key: "bb_above_mid", label: "Harga di atas mid Bollinger" },
    { key: "near_52w_high", label: "Dalam 5% dari high 52 minggu" },
    { key: "obv_rising", label: "OBV naik 10 bar" },
  ],
};

const GROUPS: Record<ChecklistVariant, Group[]> = {
  swing: [...SWING_GROUPS, QUALITY_GROUP],
  scalp: [...SCALP_GROUPS, QUALITY_GROUP],
  day: [...DAY_GROUPS, QUALITY_GROUP],
  overnight: [...OVERNIGHT_GROUPS, QUALITY_GROUP],
};

const TITLES: Record<ChecklistVariant, string> = {
  swing: "Checklist sinyal swing",
  scalp: "Checklist sinyal scalping",
  day: "Checklist sinyal pagi-sore",
  overnight: "Checklist sinyal sore-pagi",
};

export function SignalChecklist({
  checks,
  variant = "swing",
}: {
  checks: Record<string, boolean>;
  variant?: ChecklistVariant;
}) {
  const groups = GROUPS[variant];
  return (
    <section className="border border-line bg-surface p-4">
      <h2 className="text-xs font-medium text-muted">{TITLES[variant]}</h2>
      <div className="mt-3 space-y-3">
        {groups.map((group) => (
          <div key={group.title}>
            <div className="text-[11px] font-semibold text-faint">{group.title}</div>
            <ul className="mt-1.5 space-y-1.5">
              {group.items.map((item) => {
                const ok = checks[item.key] === true;
                return (
                  <li key={item.key} className="flex items-start gap-2 text-sm">
                    <span aria-hidden="true" className={`mt-0.5 font-mono text-xs ${ok ? "text-pos" : "text-faint"}`}>
                      {ok ? "✓" : "✕"}
                    </span>
                    <span className={ok ? "text-ink" : "text-muted"}>
                      {item.label}
                      <span className="sr-only">{ok ? " terpenuhi" : " tidak terpenuhi"}</span>
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
