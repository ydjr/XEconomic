"""
Step 0: Fetch News from Supabase
=================================
Downloads news articles from the Supabase `articles` table
and saves them as CSV files for the preprocessing pipeline.

Usage:
    python pipeline/news_prep/0_fetch_news.py                    # auto (previous month)
    python pipeline/news_prep/0_fetch_news.py --start 2025-01 --end 2025-06
    python pipeline/news_prep/0_fetch_news.py --all              # fetch all available
"""

import argparse
import sys
import math
import time
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta

import requests
import pandas as pd

# --- resolve project root & import config ---
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from config import Dirs, Supabase, Pipeline, Files

OUTPUT_DIR = Dirs.NEWS_SUM
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Supabase REST API helpers
HEADERS = {
    "apikey": Supabase.ANON_KEY,
    "Authorization": f"Bearer {Supabase.ANON_KEY}",
}
BASE_URL = f"{Supabase.URL}/rest/v1/{Supabase.TABLE}"


def fetch_page(offset: int, limit: int, start_date: str, end_date: str) -> tuple:
    """Fetch a single page of articles from Supabase."""
    # Use date-only format (YYYY-MM-DD) — more stable than full ISO timestamp
    start_d = start_date[:10] if start_date else None
    end_d   = end_date[:10]   if end_date   else None

    # Use list of tuples to allow duplicate param keys (requests supports this)
    params = [
        ("select", "id,agency,url,article_id,section,subtype,headline,summary,content,published_at"),
        ("order", "published_at.asc"),
        ("offset", offset),
        ("limit", limit),
    ]
    if start_d:
        params.append(("published_at", f"gte.{start_d}"))
    if end_d:
        params.append(("published_at", f"lte.{end_d}"))

    for attempt in range(3):
        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=90)
        if resp.status_code in (200, 206):
            break
        if resp.status_code >= 500 and attempt < 2:
            wait = 15 * (attempt + 1)
            print(f"  [RETRY {attempt+1}/3] HTTP {resp.status_code}, waiting {wait}s...", flush=True)
            time.sleep(wait)
        else:
            print(f"  [ERROR] HTTP {resp.status_code}")
            print(f"  [ERROR] URL: {resp.url}")
            print(f"  [ERROR] Body: {resp.text[:2000]}", flush=True)
            resp.raise_for_status()

    content_range = resp.headers.get("content-range", "")
    total = 0
    if "/" in content_range:
        total_str = content_range.split("/")[-1]
        if total_str != "*":
            total = int(total_str)

    return resp.json(), total


def fetch_all_articles(start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch all articles month-by-month to avoid Supabase statement timeout.

    Splitting into monthly windows keeps each query small enough to finish
    within the free-tier 2-second statement timeout even with the large
    `content` column selected.
    """
    start_d = datetime.strptime(start_date[:10], "%Y-%m-%d")
    end_d   = datetime.strptime(end_date[:10], "%Y-%m-%d") if end_date else datetime.now()

    all_rows = []
    page_size = Supabase.PAGE_SIZE
    current = start_d.replace(day=1)

    while current <= end_d:
        next_month = current + relativedelta(months=1)
        month_end  = min(next_month - relativedelta(days=1), end_d)

        m_start = current.strftime("%Y-%m-%d")
        m_end   = month_end.strftime("%Y-%m-%d")

        print(f"  Fetching {m_start} -> {m_end} ...", flush=True)
        page = 0
        month_count = 0

        while True:
            offset = page * page_size
            rows, _ = fetch_page(offset, page_size, m_start, m_end)
            if not rows:
                break
            all_rows.extend(rows)
            month_count += len(rows)
            if len(rows) < page_size:
                break
            page += 1

        print(f"    -> {month_count} articles this month (total so far: {len(all_rows)})", flush=True)
        current = next_month

    df = pd.DataFrame(all_rows)
    print(f"  Total fetched: {len(df)} articles")
    return df


def determine_date_range(start: str = None, end: str = None):
    """Determine start/end dates for fetching."""
    now = datetime.now()

    if start and end:
        # Explicit range given
        s = pd.to_datetime(start).strftime("%Y-%m-%dT00:00:00")
        e = pd.to_datetime(end)
        # If end is just a month like "2025-06", go to end of that month
        if len(end) <= 7:  # "YYYY-MM"
            e = e + relativedelta(months=1) - relativedelta(days=1)
        e = e.strftime("%Y-%m-%dT23:59:59")
        return s, e

    if start and not end:
        # From start to now
        s = pd.to_datetime(start).strftime("%Y-%m-%dT00:00:00")
        return s, None

    # Auto mode: previous month
    prev_month = now - relativedelta(months=1)
    s = prev_month.replace(day=1).strftime("%Y-%m-%dT00:00:00")
    e = (prev_month.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%dT23:59:59")
    return s, e


def main():
    parser = argparse.ArgumentParser(description="Fetch news articles from Supabase")
    parser.add_argument("--start", type=str, default=None,
                        help="Start date (e.g. 2025-01 or 2025-01-01)")
    parser.add_argument("--end", type=str, default=None,
                        help="End date (e.g. 2025-06 or 2025-06-30)")
    parser.add_argument("--all", action="store_true",
                        help="Fetch all available articles (from NEWS_START in config)")
    args = parser.parse_args()

    print("=" * 50)
    print("Step 0: Fetch News from Supabase")
    print("=" * 50)

    if args.all:
        start_date, end_date = determine_date_range(start=Pipeline.NEWS_START)
        print(f"  Mode: ALL (from {Pipeline.NEWS_START})")
    elif args.start:
        start_date, end_date = determine_date_range(args.start, args.end)
        print(f"  Mode: CUSTOM range")
    else:
        start_date, end_date = determine_date_range()
        print(f"  Mode: AUTO (previous month)")

    print(f"  Range: {start_date} -> {end_date or 'latest'}")

    # Fetch
    df = fetch_all_articles(start_date, end_date)

    if df.empty:
        print("  No articles found in this range.")
        return

    # Save
    out_file = Files.RAW_NEWS_CSV
    file_exists = out_file.exists()

    # Dedup: skip articles already in the existing file
    if file_exists:
        try:
            existing_ids = pd.read_csv(out_file, usecols=['id'])['id'].tolist()
            before = len(df)
            df = df[~df['id'].isin(existing_ids)]
            if before != len(df):
                print(f"  Dedup: removed {before - len(df)} already-fetched articles, {len(df)} new")
        except Exception as e:
            print(f"  [WARN] Dedup check failed ({e}), appending all")

    if df.empty:
        print("  No new articles to append (all already fetched).")
        return

    # Append to the existing raw news dataset
    df.to_csv(out_file, mode='a', header=not file_exists, index=False, encoding="utf-8-sig")
    print(f"\n  Saved (Appended): {out_file}")
    print(f"  Articles: {len(df)}")
    print(f"  Agencies: {df['agency'].value_counts().to_dict()}")
    print(f"  Date range: {df['published_at'].min()} to {df['published_at'].max()}")

    print("\n" + "=" * 50)
    print("Fetch complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
