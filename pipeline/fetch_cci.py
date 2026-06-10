"""
Fetch the UTCC Consumer Confidence Index (CCI) — the project's forecast
target — from the University of the Thai Chamber of Commerce.
=========================================================================
UTCC publishes the CCI only as monthly press-release articles (no API,
no CSV). This script reaches them through the site's WordPress REST API
and parses the headline index value out of the article text.

Verified: the July 2025 article reports 51.7, which matches the existing
public/data/indicators/cci.csv exactly — same index.

Only `cci_overall` is parsed: it is the sole value present in the article
TEXT (the current/future sub-indices live inside an infographic image),
and it is the only column the pipeline actually consumes
(5.consolidate.py loads cci.csv with value_col="cci_overall").

The fetched series is written to its OWN file —
public/data/indicators/cci_utcc.csv — and is kept separate from the
canonical cci.csv on purpose: cci.csv stays untouched and operator-
controlled, while cci_utcc.csv is the auto-refreshed UTCC view that
the dashboard / a future merge step can consume.

Set WRITE_CANONICAL=True to also append verified new months into cci.csv.
"""

import re
import sys
import time
from pathlib import Path

import requests
import pandas as pd

# --- resolve project root & import config ---
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import Dirs, Files

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

WP_API   = "https://www.utcc.ac.th/wp-json/wp/v2/posts"
SEARCH   = "ดัชนีความเชื่อมั่นผู้บริโภค"
PER_PAGE = 30                       # ~2.5 years of monthly posts
HEADERS  = {"User-Agent": "Mozilla/5.0 (XEconomic pipeline)"}
TIMEOUT  = 60
RETRIES  = 3

OUT_CSV         = Files.CCI_UTCC_CSV     # dedicated file, separate from cci.csv
WRITE_CANONICAL = True                   # also append verified new months into cci.csv

THAI_MONTHS = {
    "มกราคม": 1, "กุมภาพันธ์": 2, "มีนาคม": 3, "เมษายน": 4,
    "พฤษภาคม": 5, "มิถุนายน": 6, "กรกฎาคม": 7, "สิงหาคม": 8,
    "กันยายน": 9, "ตุลาคม": 10, "พฤศจิกายน": 11, "ธันวาคม": 12,
}
_MONTH_RE = "|".join(THAI_MONTHS)


def strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = re.sub(r"&[a-z#0-9]+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_month(title: str, text: str):
    """Data month — taken from the consistently-formatted
    'ประจำเดือน<month> 25YY' phrase (title first, then body)."""
    for src in (title, text):
        m = re.search(r"ประจำเดือน\s*(" + _MONTH_RE + r")\s*(25\d\d)", src)
        if m:
            return THAI_MONTHS[m.group(1)], int(m.group(2)) - 543  # BE -> CE
    return None


def parse_value(text: str):
    """Headline consumer-confidence value — the first number right after
    'ดัชนีความเชื่อมั่น(ของ)ผู้บริโภค ... อยู่ที่[ระดับ]'. Anchoring on
    'ผู้บริโภค' avoids the Thai Chamber of Commerce index (หอการค้าไทย),
    a different number in the same article."""
    m = re.search(
        r"ดัชนีความเชื่อมั่น(?:ของ)?ผู้บริโภค.{0,70}?"
        r"อยู่ที่\s*(?:ระดับ\s*)?(\d{2,3}(?:\.\d)?)",
        text,
    )
    if not m:
        return None
    value = float(m.group(1))
    return value if 20 < value < 90 else None   # CCI realistically sits here


def parse_article(title: str, text: str):
    """Pull (YYYY-MM, cci_overall) out of one article."""
    month = parse_month(title, text)
    value = parse_value(text)
    if month is None or value is None:
        return None
    return f"{month[1]:04d}-{month[0]:02d}", value


def fetch_posts():
    params = {"search": SEARCH, "per_page": PER_PAGE,
              "orderby": "date", "order": "desc"}
    for attempt in range(RETRIES):
        try:
            r = requests.get(WP_API, params=params, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json()
            print(f"  [retry {attempt+1}/{RETRIES}] HTTP {r.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  [retry {attempt+1}/{RETRIES}] {type(e).__name__}")
        time.sleep(8)
    return []


def main():
    print("Fetching UTCC Consumer Confidence Index posts...")
    posts = fetch_posts()
    if not posts:
        print("  [!] No posts fetched — aborting.")
        return

    rows = {}
    for p in posts:
        title = strip_html(p.get("title", {}).get("rendered", ""))
        text  = strip_html(p.get("content", {}).get("rendered", ""))
        parsed = parse_article(title, text)
        if parsed:
            date, value = parsed
            rows.setdefault(date, value)   # dedup by month, keep newest post
        else:
            print(f"  [warn] could not parse post dated {p.get('date', '?')[:10]}")

    if not rows:
        print("  [!] Parsed 0 articles — the article wording may have changed.")
        return

    df = pd.DataFrame(sorted(rows.items()), columns=["date", "cci_overall"])
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\nsaved {len(df)} months to {OUT_CSV}")
    print(f"        range {df['date'].iloc[0]} -> {df['date'].iloc[-1]}")

    # Compare with the canonical series
    cci = Files.CCI_CSV
    if cci.exists():
        ex = pd.read_csv(cci)
        ex["date"] = ex["date"].astype(str).str[:7]
        merged = ex.merge(df, on="date", suffixes=("_canon", "_utcc"))
        if not merged.empty:
            merged["diff"] = (merged["cci_overall_canon"]
                              - merged["cci_overall_utcc"]).abs()
            print(f"\nVerification on {len(merged)} overlapping months:")
            print(merged[["date", "cci_overall_canon",
                          "cci_overall_utcc", "diff"]].to_string(index=False))
            print(f"  max abs diff: {merged['diff'].max():.3f}")

        last_canon = ex["date"].max()
        new = df[df["date"] > last_canon]
        print(f"\ncanonical cci.csv ends at {last_canon}")
        if new.empty:
            print("  no newer months available from UTCC")
        else:
            print(f"  {len(new)} new month(s) available to append:")
            print(new.to_string(index=False))

        if WRITE_CANONICAL and not new.empty:
            out = pd.concat([ex, new], ignore_index=True)
            out = out.drop_duplicates(subset=["date"], keep="last").sort_values("date")
            out.to_csv(cci, index=False, encoding="utf-8-sig")
            print(f"\n[canonical] appended {len(new)} month(s) into {cci}")


if __name__ == "__main__":
    # Best-effort scraper: never abort the monthly pipeline if UTCC's
    # WordPress changes wording or the WP API is unreachable. Log and
    # exit 0 — cci_utcc.csv from the previous successful run stays as-is.
    try:
        main()
    except Exception as exc:
        print(f"[soft-fail] fetch_cci aborted: {type(exc).__name__}: {exc}")
        sys.exit(0)
