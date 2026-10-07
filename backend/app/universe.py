from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pandas as pd

from .config import settings
from .data import store

_IDX_URL = (
    "https://www.idx.co.id/primary/ListedCompany/GetCompanyProfiles"
    "?start=0&length=9999&sortField=Code&sortOrder=asc"
)


def load_bundled(csv_path: Path | None = None) -> pd.DataFrame:
    path = csv_path or settings.universe_csv
    if not path.exists():
        return pd.DataFrame(columns=["symbol", "name", "sector"])
    df = pd.read_csv(path, dtype=str).fillna("")
    df["symbol"] = df["symbol"].str.upper().str.strip()
    return df[["symbol", "name", "sector"]]


def fetch_yahoo_universe(batch: int = 250) -> pd.DataFrame:
    """All IDX-listed tickers via the Yahoo Finance screener (region: id).

    Returns an empty frame on any failure; caller should fall back.
    """
    empty = pd.DataFrame(columns=["symbol", "name", "sector"])
    try:
        import yfinance as yf
        from yfinance import EquityQuery
    except Exception:  # noqa: BLE001
        return empty

    rows: list[dict] = []
    try:
        query = EquityQuery("eq", ["region", "id"])
        offset = 0
        total: int | None = None
        while True:
            result = yf.screen(query, size=batch, offset=offset)
            quotes = result.get("quotes") or []
            if total is None:
                total = int(result.get("total") or len(quotes))
            for item in quotes:
                sym = str(item.get("symbol") or "").upper()
                if not sym.endswith(".JK"):
                    continue
                rows.append(
                    {
                        "symbol": sym[:-3],
                        "name": str(item.get("shortName") or item.get("longName") or "").strip(),
                        "sector": str(item.get("sector") or "").strip(),
                    }
                )
            offset += len(quotes)
            if not quotes or offset >= total:
                break
    except Exception:  # noqa: BLE001
        if not rows:
            return empty
    df = pd.DataFrame(rows, columns=["symbol", "name", "sector"])
    return df.drop_duplicates(subset="symbol").reset_index(drop=True)


def fetch_idx_universe(timeout: float = 20.0) -> pd.DataFrame:
    """Best-effort refresh from the IDX company-profile endpoint (often Cloudflare-blocked)."""
    req = urllib.request.Request(
        _IDX_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            ),
            "Referer": "https://www.idx.co.id/en/listed-companies/company-profiles",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return pd.DataFrame(columns=["symbol", "name", "sector"])

    rows = payload.get("data") or payload.get("Results") or []
    out: list[dict] = []
    for item in rows:
        code = (item.get("Code") or item.get("KodeEmiten") or "").strip().upper()
        if not code:
            continue
        out.append(
            {
                "symbol": code,
                "name": (item.get("CompanyName") or item.get("NamaEmiten") or "").strip(),
                "sector": (
                    item.get("Sector") or item.get("Sektor") or item.get("SubSector") or ""
                ).strip(),
            }
        )
    return pd.DataFrame(out, columns=["symbol", "name", "sector"])


def refresh_universe() -> pd.DataFrame:
    """Full IDX list with sectors backfilled from the curated bundled CSV."""
    bundled = load_bundled()
    online = fetch_yahoo_universe()
    if online.empty:
        online = fetch_idx_universe()
    if online.empty:
        return bundled

    known = bundled.set_index("symbol")
    sectors = []
    for sym, sector in zip(online["symbol"], online["sector"], strict=False):
        if sym in known.index:
            curated = str(known.loc[sym, "sector"]).strip()
            sectors.append(curated or sector)
        else:
            sectors.append(sector)
    online["sector"] = sectors

    missing = bundled[~bundled["symbol"].isin(online["symbol"])]
    full = (
        pd.concat([online, missing], ignore_index=True)
        .drop_duplicates(subset="symbol")
        .sort_values("symbol")
        .reset_index(drop=True)
    )
    return full


def seed_universe(refresh: bool = False, write_csv: bool = False) -> int:
    df = refresh_universe() if refresh else load_bundled()
    if df.empty:
        df = load_bundled()
    if refresh and write_csv and not df.empty:
        df.to_csv(settings.universe_csv, index=False)
    store.init_db()
    return store.upsert_universe(df)


if __name__ == "__main__":
    import sys

    refresh = "--refresh" in sys.argv
    count = seed_universe(refresh=refresh, write_csv=refresh)
    print(f"seeded {count} tickers")
