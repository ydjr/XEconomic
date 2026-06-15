import sys
import pandas as pd
import requests
import math
from pathlib import Path

# --- resolve project root & import config ---
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import Dirs, Files, SupabaseABSA

OUTPUT_FILE = Files.ABSA_NEWS_CSV

HEADERS = {
    "apikey": SupabaseABSA.ANON_KEY,
    "Authorization": f"Bearer {SupabaseABSA.ANON_KEY}",
}
BASE_URL = f"{SupabaseABSA.URL}/rest/v1/{SupabaseABSA.TABLE}"

def fetch_page(offset: int, limit: int) -> tuple:
    params = [
        ("select", "*"),
        ("order", "published_at.asc"),
        ("offset", offset),
        ("limit", limit),
    ]
    for attempt in range(3):
        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=60)
        if resp.status_code in (200, 206):
            return resp.json()
        print(f"  [RETRY {attempt+1}/3] HTTP {resp.status_code}")
    resp.raise_for_status()

def main():
    print("=" * 50)
    print("Step 3.5: Fetch Historical ABSA Results from Supabase")
    print("=" * 50)
    
    all_rows = []
    page_size = 1000
    page = 0
    
    while True:
        offset = page * page_size
        rows = fetch_page(offset, page_size)
        if not rows:
            break
        all_rows.extend(rows)
        print(f"  Fetched {len(rows)} rows (total so far: {len(all_rows)})", flush=True)
        if len(rows) < page_size:
            break
        page += 1
        
    df = pd.DataFrame(all_rows)
    print(f"Total fetched from Supabase: {len(df)} articles")
    
    if df.empty:
        print("No articles found in Supabase absa_results.")
        return
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\nSuccessfully generated {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
