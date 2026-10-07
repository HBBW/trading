import { EMPTY_FILTERS, type Filters } from "../lib/filters";

export interface MinScoreOption {
  value: number;
  label: string;
}

const controlClass =
  "h-9 rounded-sm border border-line bg-surface px-2.5 text-sm text-ink placeholder:text-faint focus-visible:outline-2 focus-visible:outline-accent";

export function FilterBar({
  filters,
  onChange,
  sectors,
  signalOptions,
  minScoreOptions,
  count,
  total,
  onReset,
}: {
  filters: Filters;
  onChange: (next: Filters) => void;
  sectors: string[];
  signalOptions: string[];
  minScoreOptions: MinScoreOption[];
  count: number;
  total: number;
  onReset: () => void;
}) {
  const dirty =
    filters.minScore !== EMPTY_FILTERS.minScore ||
    filters.signal !== EMPTY_FILTERS.signal ||
    filters.sector !== EMPTY_FILTERS.sector ||
    filters.q !== EMPTY_FILTERS.q;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <label className="sr-only" htmlFor="filter-q">
        Cari kode atau nama
      </label>
      <input
        id="filter-q"
        type="search"
        value={filters.q}
        onChange={(e) => onChange({ ...filters, q: e.target.value })}
        placeholder="Cari kode / nama"
        className={`${controlClass} w-44`}
      />

      <label className="sr-only" htmlFor="filter-score">
        Skor minimum
      </label>
      <select
        id="filter-score"
        value={filters.minScore}
        onChange={(e) => onChange({ ...filters, minScore: Number(e.target.value) })}
        className={controlClass}
      >
        {minScoreOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>

      <label className="sr-only" htmlFor="filter-signal">
        Sinyal
      </label>
      <select
        id="filter-signal"
        value={filters.signal}
        onChange={(e) => onChange({ ...filters, signal: e.target.value })}
        className={controlClass}
      >
        <option value="ALL">Semua sinyal</option>
        {signalOptions.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>

      <label className="sr-only" htmlFor="filter-sector">
        Sektor
      </label>
      <select
        id="filter-sector"
        value={filters.sector}
        onChange={(e) => onChange({ ...filters, sector: e.target.value })}
        className={controlClass}
      >
        <option value="ALL">Semua sektor</option>
        {sectors.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>

      {dirty ? (
        <button
          type="button"
          onClick={onReset}
          className="h-9 rounded-sm border border-line px-2.5 text-sm text-muted hover:text-ink"
        >
          Reset filter
        </button>
      ) : null}

      <span className="ml-auto text-xs text-muted" aria-live="polite">
        {count} dari {total} saham
      </span>
    </div>
  );
}
