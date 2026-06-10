"""
Fetch macroeconomic indicators from Ministry of Commerce open data API.
=========================================================================
Source : https://dataapi.moc.go.th  (TPSO / กรมการค้าภายใน publishes here)
Output : data/indicators_api/{cpi,impi,expi}.csv

Schema written: date,value   (matches existing public/data/indicators/*.csv)

NOTE on base years:
  - cpig-indexes (CPI):    base_year = 2019
  - imi-indexes  (IMPI):   base_year = 2012
  - exi-indexes  (EXPI):   base_year = 2012

The existing public/data/indicators/{cpi,impi,expi}.csv use different base
years, so values won't line up numerically. This script writes to a
separate folder (indicators_api/) on purpose — operator decides when /
how to merge with the historical series.
"""

import sys
import time
from pathlib import Path
from typing import List, Dict

import requests
import pandas as pd

# --- resolve project root & import config ---
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import Dirs


# Ministry of Commerce open data — same host, different paths per index
API_HOST = "https://dataapi.moc.go.th"

INDICATORS = [
    {
        "name":     "cpi",
        "endpoint": "cpig-indexes",
        "params":   {"region_id": 0, "index_id": "0000000000000000"},
        "label":    "Consumer Price Index (nationwide, ทั่วประเทศ, base=2019)",
    },
    {
        "name":     "impi",
        "endpoint": "imi-indexes",
        "params":   {"index_id": "0000000000000000"},
        "label":    "Import Price Index (รวมทุกรายการ, base=2012)",
    },
    {
        "name":     "expi",
        "endpoint": "exi-indexes",
        "params":   {"index_id": "0000000000000000"},
        "label":    "Export Price Index (รวมทุกรายการ, base=2012)",
    },
]

START_YEAR  = 2010                      # API has data from 2010 onwards
END_YEAR    = pd.Timestamp.today().year # Through current year
REQ_TIMEOUT = 120                       # Server is slow on cold cache
MAX_RETRIES = 3
RETRY_WAIT  = 10                        # Seconds between retries

OUT_DIR = Dirs.ROOT / "data" / "indicators_api"


def fetch_year(endpoint: str, params: Dict, year: int) -> List[Dict]:
    """Fetch one year of data from a given endpoint, with retry on 5xx."""
    url = f"{API_HOST}/{endpoint}"
    full_params = {**params, "from_year": year, "to_year": year}

    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, params=full_params, timeout=REQ_TIMEOUT)
            if r.status_code == 200:
                return r.json()
            if r.status_code >= 500:
                print(f"    [retry {attempt+1}/{MAX_RETRIES}] HTTP {r.status_code} for {year}, "
                      f"waiting {RETRY_WAIT}s...")
                time.sleep(RETRY_WAIT)
                continue
            print(f"    [error] HTTP {r.status_code} for {year}: {r.text[:200]}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"    [retry {attempt+1}/{MAX_RETRIES}] {type(e).__name__} for {year}")
            time.sleep(RETRY_WAIT)

    print(f"    [give up] could not fetch {year} after {MAX_RETRIES} attempts")
    return []


def fetch_indicator(spec: Dict) -> pd.DataFrame:
    """Fetch all years for one indicator -> DataFrame with date+value columns."""
    name     = spec["name"]
    endpoint = spec["endpoint"]
    params   = spec["params"]
    label    = spec["label"]

    print(f"\n--- {name.upper()} ({label}) ---")
    rows = []
    for year in range(START_YEAR, END_YEAR + 1):
        records = fetch_year(endpoint, params, year)
        if records:
            rows.extend(records)
            print(f"  {year}: {len(records)} records")
        else:
            print(f"  {year}: (no data)")

    if not rows:
        return pd.DataFrame(columns=["date", "value"])

    df = pd.DataFrame(rows)
    df["date"]  = df.apply(lambda r: f"{int(r['year']):04d}-{int(r['month']):02d}", axis=1)
    df["value"] = pd.to_numeric(df["price_index"], errors="coerce")
    df = df[["date", "value"]].dropna().sort_values("date").reset_index(drop=True)
    return df


def merge_into_existing(name: str, df_api: pd.DataFrame) -> None:
    """Append new months from the API series into the canonical indicator file.

    The API and the historical files may sit on different base years, so the
    API values are rebased by a factor derived from overlapping months
    (median ratio for robustness). Only months strictly newer than the
    existing series are appended — historical rows are never modified.
    """
    target = Dirs.INDICATORS / f"{name}.csv"
    if not target.exists():
        print(f"  [merge] {name}: no existing file at {target}, skipping merge")
        return

    df_ex = pd.read_csv(target)
    if "date" not in df_ex.columns or "value" not in df_ex.columns:
        print(f"  [merge] {name}: existing file has unexpected columns, skipping merge")
        return

    overlap = df_ex.merge(df_api, on="date", suffixes=("_ex", "_api"))
    if overlap.empty:
        print(f"  [merge] {name}: no overlapping months — cannot derive rebase factor, skipping")
        return

    # Robust rebase factor: median of existing/api over the last 12 overlapping months
    tail = overlap.tail(12)
    ratios = tail["value_ex"] / tail["value_api"].replace(0, pd.NA)
    factor = float(ratios.median())

    last_existing_date = df_ex["date"].max()
    new_rows = df_api[df_api["date"] > last_existing_date].copy()
    if new_rows.empty:
        print(f"  [merge] {name}: no months newer than {last_existing_date} - nothing to append "
              f"(rebase factor would be {factor:.4f})")
        return

    new_rows["value"] = (new_rows["value"] * factor).round(2)
    combined = pd.concat([df_ex, new_rows[["date", "value"]]], ignore_index=True)
    combined = combined.drop_duplicates(subset=["date"], keep="last").sort_values("date")
    combined.to_csv(target, index=False, encoding="utf-8-sig")
    print(f"  [merge] {name}: appended {len(new_rows)} new months "
          f"({new_rows['date'].min()}..{new_rows['date'].max()}) "
          f"rebased x{factor:.4f} -> {target}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Fetching indicators from {API_HOST} ({START_YEAR} -> {END_YEAR})")
    print(f"Output: {OUT_DIR}")

    summary = []
    for spec in INDICATORS:
        df = fetch_indicator(spec)
        if df.empty:
            print(f"  [!] {spec['name']}: no data fetched, skipping save")
            summary.append((spec["name"], 0, None, None))
            continue

        out = OUT_DIR / f"{spec['name']}.csv"
        df.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"  Saved {len(df)} rows to {out}")
        print(f"    Range: {df['date'].min()} -> {df['date'].max()}")
        summary.append((spec["name"], len(df), df["date"].min(), df["date"].max()))

        # Rebase + append any new months into the canonical training input
        merge_into_existing(spec["name"], df)

    # Final report
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"{'indicator':<8} {'rows':>6}  {'first':<10}  {'last':<10}")
    for name, rows, first, last in summary:
        print(f"{name:<8} {rows:>6}  {first or '-':<10}  {last or '-':<10}")


if __name__ == "__main__":
    main()
