import { useQuery } from "@tanstack/react-query";
import { Link, NavLink, Route, Routes } from "react-router-dom";
import { api } from "./lib/api";
import { useTheme } from "./lib/theme-context";
import Scanner from "./pages/Scanner";
import TickerDetail from "./pages/TickerDetail";
import { btnGhost } from "./lib/ui";

function SunIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />
    </svg>
  );
}

function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={theme === "dark" ? "Aktifkan tema terang" : "Aktifkan tema gelap"}
      className="grid h-9 w-9 place-items-center rounded-sm border border-line text-muted hover:text-ink"
    >
      {theme === "dark" ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}

function MarketChip() {
  const { data } = useQuery({
    queryKey: ["market"],
    queryFn: api.marketStatus,
    refetchInterval: 60_000,
  });

  if (!data) {
    return <span className="hidden text-xs text-faint sm:inline">Memuat status market…</span>;
  }

  const label = !data.is_trading_day ? "Libur" : data.is_open ? "Buka" : "Tutup";
  const tone = data.is_open ? "text-pos" : "text-muted";

  return (
    <span className="hidden items-center gap-1.5 text-xs sm:inline-flex">
      {data.is_open ? (
        <span className="h-1.5 w-1.5 rounded-full bg-pos" aria-hidden="true" />
      ) : null}
      <span className={`font-medium ${tone}`}>{label}</span>
      <span className="text-faint">{data.next_event ?? ""}</span>
    </span>
  );
}

function NotFound() {
  return (
    <section className="border border-line bg-surface p-8 text-center">
      <h1 className="font-serif text-lg">Halaman tidak ditemukan</h1>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted">
        Alamat yang dibuka tidak ada di aplikasi ini.
      </p>
      <div className="mt-4 flex justify-center">
        <Link to="/" className={btnGhost}>
          Kembali ke Scanner
        </Link>
      </div>
    </section>
  );
}

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded-sm focus:bg-elevated focus:px-3 focus:py-2 focus:text-sm"
      >
        Lewati ke konten
      </a>

      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex h-14 w-full max-w-[1200px] items-center gap-4 px-4">
          <Link to="/" className="flex items-baseline gap-2">
            <span className="font-serif text-lg leading-none">Screener Swing</span>
            <span className="rounded-sm border border-line-strong px-1 font-mono text-[10px] leading-4 text-muted">
              IDX
            </span>
          </Link>
          <nav className="text-sm" aria-label="Navigasi utama">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `rounded-sm px-2 py-1 ${isActive ? "text-ink" : "text-muted hover:text-ink"}`
              }
            >
              Scanner
            </NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-4">
            <MarketChip />
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main id="main" className="mx-auto w-full max-w-[1200px] flex-1 px-4 py-6">
        <Routes>
          <Route path="/" element={<Scanner />} />
          <Route path="/ticker/:symbol" element={<TickerDetail />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>

      <footer className="border-t border-line">
        <div className="mx-auto w-full max-w-[1200px] px-4 py-4 text-[11px] text-faint">
          Sumber data: Yahoo Finance (EOD, plus refresh intraday tiap 30 menit saat sesi). Bukan
          saran investasi.
        </div>
      </footer>
    </div>
  );
}
