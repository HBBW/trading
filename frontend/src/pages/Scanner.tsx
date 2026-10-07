import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { FilterBar, type MinScoreOption } from "../components/FilterBar";
import { ResultsTable } from "../components/ResultsTable";
import { api } from "../lib/api";
import { EMPTY_FILTERS, type Filters } from "../lib/filters";
import { fmtDate, fmtDateTime, volRatio } from "../lib/format";
import { rowFields, type Category, type SortKey, type SortState } from "../lib/rows";
import type { ScanResult } from "../lib/types";
import { btnPrimary } from "../lib/ui";

const MODE_LABEL: Record<string, string> = {
  eod: "EOD",
  intraday: "Intraday",
  manual: "Manual",
};

const MIN_SCORE_OPTIONS: Record<Category, MinScoreOption[]> = {
  swing: [
    { value: 0, label: "Semua skor" },
    { value: 60, label: "Skor ≥ 60 (kandidat)" },
    { value: 75, label: "Skor ≥ 75 (potential)" },
  ],
  scalp: [
    { value: 0, label: "Semua skor" },
    { value: 65, label: "Skor ≥ 65 (kandidat)" },
    { value: 80, label: "Skor ≥ 80 (potential)" },
  ],
  day: [
    { value: 0, label: "Semua skor" },
    { value: 65, label: "Skor ≥ 65 (kandidat)" },
    { value: 80, label: "Skor ≥ 80 (potential)" },
  ],
  overnight: [
    { value: 0, label: "Semua skor" },
    { value: 65, label: "Skor ≥ 65 (kandidat)" },
    { value: 80, label: "Skor ≥ 80 (potential)" },
  ],
};

const CATEGORY_NOTE: Record<Category, string> = {
  swing: "Tren + pullback RSI, target 2R dan 3R, horizon beberapa hari sampai minggu.",
  scalp: "Momentum harian (breakout + volume), target 1R dan 2R, cut loss maksimal 2% dari entry.",
  day: "Beli pagi dekat open, jual sore dekat close di hari yang sama. Level dari rata-rata range 20 hari.",
  overnight: "Beli sore di close, jual sesi pagi besok. Level dari rata-rata range 20 hari.",
};

const CATEGORY_FOOTNOTE: Record<Category, string> = {
  swing:
    "Skor 60+ kandidat. POTENTIAL BUY hanya untuk skor 75+ dengan tren, pullback RSI, dan volume terpenuhi. Entry dari close terakhir, CL di bawah low 10 bar dan EMA50 minus 0,5 ATR, dibatasi maksimal 12% dari entry.",
  scalp:
    "Skor 65+ kandidat. POTENTIAL SCALP hanya untuk skor 80+ dengan breakout, close kuat, volume ≥1,5x, dan RSI 50 sampai 72. CL di bawah low hari ini, dibatasi maksimal 2% dari entry.",
  day:
    "Skor 65+ kandidat. POTENTIAL DAY untuk skor 80+ dengan breakout, close kuat, volume ≥1,5x, dan RSI 40 sampai 78. Entry acuan open pagi (pakai close terakhir sebagai proxy), CL -0,45 range, TP +0,5 dan +0,8 range; jual sore di close (time exit).",
  overnight:
    "Skor 65+ kandidat. POTENTIAL OVERNIGHT untuk skor 80+ dengan close kuat (≥70% range), volume ≥1,2x, dan RSI 50 sampai 80. Entry di close sore (harga real), jual pagi besok; CL -0,3 range.",
};

const SIGNAL_ORDER = [
  "POTENTIAL SCALP",
  "POTENTIAL DAY",
  "POTENTIAL OVERNIGHT",
  "POTENTIAL BUY",
  "WATCHLIST",
  "SKIP",
];

function compare(a: ScanResult, b: ScanResult, key: SortKey, category: Category): number {
  const fa = rowFields(a, category);
  const fb = rowFields(b, category);
  switch (key) {
    case "symbol":
      return a.symbol.localeCompare(b.symbol);
    case "sector":
      return (a.sector ?? "").localeCompare(b.sector ?? "");
    case "score":
      return (fa.score ?? -1) - (fb.score ?? -1);
    case "close":
      return (a.close ?? 0) - (b.close ?? 0);
    case "rsi":
      return (a.rsi ?? 0) - (b.rsi ?? 0);
    case "adx":
      return (a.adx14 ?? -1) - (b.adx14 ?? -1);
    case "rs":
      return (a.rs ?? -1) - (b.rs ?? -1);
    case "vol":
      return (volRatio(a.volume, a.vol_avg20) ?? 0) - (volRatio(b.volume, b.vol_avg20) ?? 0);
    case "entry":
      return (fa.entry ?? 0) - (fb.entry ?? 0);
    case "cl":
      return (fa.cl ?? 0) - (fb.cl ?? 0);
    case "tp1":
      return (fa.tp1 ?? 0) - (fb.tp1 ?? 0);
    case "tp2":
      return (fa.tp2 ?? 0) - (fb.tp2 ?? 0);
  }
}

function TableSkeleton() {
  return (
    <div className="border-y border-line-strong py-1">
      <span className="sr-only">Memuat hasil scan…</span>
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className="flex items-center gap-6 px-2 py-3.5">
          <div className="h-4 w-14 rounded-sm bg-surface-2 motion-safe:animate-pulse" />
          <div className="h-4 w-28 rounded-sm bg-surface-2 motion-safe:animate-pulse" />
          <div className="h-4 w-20 rounded-sm bg-surface-2 motion-safe:animate-pulse" />
          <div className="ml-auto h-4 w-16 rounded-sm bg-surface-2 motion-safe:animate-pulse" />
          <div className="h-4 w-16 rounded-sm bg-surface-2 motion-safe:animate-pulse" />
        </div>
      ))}
    </div>
  );
}

function CategoryToggle({
  value,
  onChange,
}: {
  value: Category;
  onChange: (c: Category) => void;
}) {
  const options: { key: Category; label: string }[] = [
    { key: "swing", label: "Swing" },
    { key: "scalp", label: "Scalping" },
    { key: "day", label: "Pagi-Sore" },
    { key: "overnight", label: "Sore-Pagi" },
  ];
  return (
    <div
      role="group"
      aria-label="Kategori strategi"
      className="inline-flex flex-wrap rounded-sm border border-line bg-surface p-0.5"
    >
      {options.map((opt) => (
        <button
          key={opt.key}
          type="button"
          aria-pressed={value === opt.key}
          onClick={() => onChange(opt.key)}
          className={`h-8 rounded-[3px] px-3 text-sm ${
            value === opt.key ? "bg-surface-2 font-medium text-ink" : "text-muted hover:text-ink"
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

export default function Scanner() {
  const [category, setCategory] = useState<Category>("swing");
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [sort, setSort] = useState<SortState>({ key: "score", dir: "desc" });
  const [scanRequestedAt, setScanRequestedAt] = useState<number | null>(null);

  const market = useQuery({
    queryKey: ["market"],
    queryFn: api.marketStatus,
    refetchInterval: 60_000,
  });

  const scan = useQuery({
    queryKey: ["scan", "latest"],
    queryFn: () => api.latestScan(1000),
    refetchInterval: () => {
      if (scanRequestedAt && Date.now() - scanRequestedAt < 5 * 60_000) return 15_000;
      return market.data?.is_open ? 30 * 60_000 : false;
    },
  });

  const runScan = useMutation({
    mutationFn: () => api.runScan("manual"),
    onSuccess: () => setScanRequestedAt(Date.now()),
  });

  const results = useMemo(() => scan.data?.results ?? [], [scan.data]);
  const run = scan.data?.run ?? null;

  const changeCategory = (c: Category) => {
    setCategory(c);
    setFilters((f) => ({ ...f, minScore: 0, signal: "ALL" }));
    setSort({ key: "score", dir: "desc" });
  };

  const sectors = useMemo(
    () => [...new Set(results.map((r) => r.sector).filter((s): s is string => Boolean(s)))].sort(),
    [results],
  );

  const signalOptions = useMemo(() => {
    const seen = new Set<string>();
    for (const r of results) {
      const s = rowFields(r, category).signal;
      if (s) seen.add(s);
    }
    const order = SIGNAL_ORDER;
    return [...seen].sort((a, b) => order.indexOf(a) - order.indexOf(b));
  }, [results, category]);

  const filtered = useMemo(() => {
    const q = filters.q.trim().toLowerCase();
    return results.filter((r) => {
      const f = rowFields(r, category);
      if ((f.score ?? -1) < filters.minScore) return false;
      if (filters.signal !== "ALL" && (f.signal ?? "SKIP") !== filters.signal) return false;
      if (filters.sector !== "ALL" && r.sector !== filters.sector) return false;
      if (q && !r.symbol.toLowerCase().includes(q) && !(r.name ?? "").toLowerCase().includes(q)) {
        return false;
      }
      return true;
    });
  }, [results, filters, category]);

  const sorted = useMemo(() => {
    const rows = [...filtered];
    rows.sort((a, b) =>
      sort.dir === "asc" ? compare(a, b, sort.key, category) : compare(b, a, sort.key, category),
    );
    return rows;
  }, [filtered, sort, category]);

  const onSort = (key: SortKey) => {
    setSort((s) =>
      s.key === key
        ? { key, dir: s.dir === "asc" ? "desc" : "asc" }
        : { key, dir: key === "symbol" || key === "sector" ? "asc" : "desc" },
    );
  };

  const dataDate = results[0]?.data_date ?? null;
  const runInfo = run
    ? `${MODE_LABEL[run.mode ?? ""] ?? run.mode} · ${run.scanned ?? 0} lolos likuiditas · ${
        run.candidates ?? 0
      } kandidat${run.errors ? ` · ${run.errors} gagal` : ""}`
    : null;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-serif text-2xl">Hasil scan</h1>
          {run ? (
            <p className="mt-1 text-sm text-muted">
              {runInfo}
              {dataDate ? ` · data per ${fmtDate(dataDate)}` : ""} · selesai{" "}
              {fmtDateTime(run.finished_at)} WIB
            </p>
          ) : (
            <p className="mt-1 text-sm text-muted">
              Screener harian saham IDX: tren, pullback RSI, dan konfirmasi volume.
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={() => runScan.mutate()}
          disabled={runScan.isPending}
          className={btnPrimary}
        >
          {runScan.isPending ? "Menjadwalkan…" : "Scan manual"}
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <CategoryToggle value={category} onChange={changeCategory} />
        <p className="text-xs text-muted">{CATEGORY_NOTE[category]}</p>
      </div>

      {runScan.isSuccess ? (
        <p className="text-xs text-muted" aria-live="polite">
          Scan manual masuk antrean. Hasil muncul setelah proses selesai, biasanya beberapa menit
          untuk seluruh universe.
        </p>
      ) : null}
      {runScan.isError ? (
        <p className="text-xs text-neg" aria-live="polite">
          Gagal menjadwalkan scan. Pastikan backend berjalan di port 8000.
        </p>
      ) : null}

      {results.length > 0 ? (
        <FilterBar
          filters={filters}
          onChange={setFilters}
          sectors={sectors}
          signalOptions={signalOptions}
          minScoreOptions={MIN_SCORE_OPTIONS[category]}
          count={sorted.length}
          total={results.length}
          onReset={() => setFilters(EMPTY_FILTERS)}
        />
      ) : null}

      {scan.isPending ? <TableSkeleton /> : null}

      {scan.isError ? (
        <section className="border border-line bg-surface p-8 text-center">
          <h2 className="font-serif text-lg">Gagal memuat hasil scan</h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-muted">
            Tidak bisa menghubungi API. Pastikan backend berjalan di port 8000, lalu coba lagi.
          </p>
          <button type="button" onClick={() => scan.refetch()} className={`${btnPrimary} mt-4`}>
            Coba lagi
          </button>
        </section>
      ) : null}

      {!scan.isPending && !scan.isError && run === null ? (
        <section className="border border-line bg-surface p-8 text-center">
          <h2 className="font-serif text-lg">Belum ada hasil scan</h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-muted">
            Scan EOD berjalan otomatis setiap hari kerja pukul 16:15 WIB, dan refresh intraday tiap
            30 menit saat sesi. Untuk mengisi tabel sekarang, jalankan scan manual.
          </p>
          <button
            type="button"
            onClick={() => runScan.mutate()}
            disabled={runScan.isPending}
            className={`${btnPrimary} mt-4`}
          >
            {runScan.isPending ? "Menjadwalkan…" : "Jalankan scan manual"}
          </button>
        </section>
      ) : null}

      {!scan.isPending && !scan.isError && run !== null && results.length === 0 ? (
        <section className="border border-line bg-surface p-8 text-center">
          <h2 className="font-serif text-lg">Tidak ada saham yang lolos likuiditas</h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-muted">
            Run terakhir tidak menghasilkan kandidat yang melewati pre-filter. Coba scan ulang saat
            data harian sudah terisi.
          </p>
        </section>
      ) : null}

      {results.length > 0 && sorted.length === 0 ? (
        <section className="border border-line bg-surface p-8 text-center">
          <h2 className="font-serif text-lg">Tidak ada hasil yang cocok</h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-muted">
            Longgarkan filter skor, sinyal, atau sektor untuk melihat kandidat lainnya.
          </p>
          <button type="button" onClick={() => setFilters(EMPTY_FILTERS)} className={`${btnPrimary} mt-4`}>
            Reset filter
          </button>
        </section>
      ) : null}

      {sorted.length > 0 ? (
        <>
          <ResultsTable rows={sorted} sort={sort} onSort={onSort} category={category} />
          <p className="text-xs text-faint">
            {CATEGORY_FOOTNOTE[category]} Bukan saran investasi.
          </p>
        </>
      ) : null}
    </div>
  );
}
