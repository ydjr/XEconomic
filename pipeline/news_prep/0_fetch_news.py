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
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta

import requests
import pandas as pd

# --- resolve project root & import config ---
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from config import Dirs, Supabase, Pipeline

OUTPUT_DIR = Dirs.NEWS_SUM
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Supabase REST API helpers
HEADERS = {
    "apikey": Supabase.ANON_KEY,
    "Authorization": f"Bearer {Supabase.ANON_KEY}",
    "Prefer": "count=exact",
}
BASE_URL = f"{Supabase.URL}/rest/v1/{Supabase.TABLE}"


def fetch_page(offset: int, limit: int, start_date: str, end_date: str) -> tuple:
    """Fetch a single page of articles from Supabase."""
    params = {
        "select": "id,agency,url,article_id,section,subtype,headline,summary,content,published_at,fetched_at",
        "order": "published_at.asc",
        "offset": offset,
        "limit": limit,
    }
    
    if start_date and end_date:
        # Use PostgREST 'and' syntax for multiple conditions on the same column
        params["and"] = f"(published_at.gte.{start_date},published_at.lte.{end_date})"
    elif start_date:
        params["published_at"] = f"gte.{start_date}"

    resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)

    resp.raise_for_status()

    # Get total count from content-range header
    content_range = resp.headers.get("content-range", "")
    total = 0
    if "/" in content_range:
        total = int(content_range.split("/")[-1])

    return resp.json(), total


def fetch_all_articles(start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch all articles in the date range with pagination."""
    print(f"  Fetching articles: {start_date} to {end_date or 'latest'}")

    # First call to get total count
    _, total = fetch_page(0, 1, start_date, end_date)
    print(f"  Total articles in range: {total}")

    if total == 0:
        return pd.DataFrame()

    all_rows = []
    page_size = Supabase.PAGE_SIZE
    n_pages = math.ceil(total / page_size)

    for page in range(n_pages):
        offset = page * page_size
        rows, _ = fetch_page(offset, page_size, start_date, end_date)
        all_rows.extend(rows)
        pct = min(100, int((len(all_rows) / total) * 100))
        print(f"    Page {page+1}/{n_pages} ... {len(all_rows)}/{total} ({pct}%)")

    df = pd.DataFrame(all_rows)
    print(f"  Fetched {len(df)} articles total")
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
    # Determine output filename from date range
    s_label = pd.to_datetime(start_date).strftime("%Y-%m")
    e_label = pd.to_datetime(end_date).strftime("%Y-%m") if end_date else "latest"
    out_file = OUTPUT_DIR / f"articles_{s_label}_to_{e_label}.csv"

    df.to_csv(out_file, index=False, encoding="utf-8-sig")
    print(f"\n  Saved: {out_file}")
    print(f"  Articles: {len(df)}")
    print(f"  Agencies: {df['agency'].value_counts().to_dict()}")
    print(f"  Date range: {df['published_at'].min()} to {df['published_at'].max()}")

    print("\n" + "=" * 50)
    print("Fetch complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
