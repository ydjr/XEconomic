import pandas as pd
from pathlib import Path
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import Dirs, Files, Pipeline


# --- Setup Paths ---
IN_ABSA = Files.ABSA_NEWS_CSV
OUT_CSV = Files.ASPECT_FEATURES

def analyze_and_pivot_sentiment(file_path, output_path):
    try:
        # 1. Load ABSA data
        df = pd.read_csv(file_path, encoding="utf-8-sig")

        # 2. Clean and Format Time
        df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce')
        df = df.dropna(subset=['published_at'])
        df['date'] = df['published_at'].dt.to_period('M').astype(str)

        # 3. Clean Aspects & FILTER OUT OTHERS
        df['Aspect'] = df['Aspect'].astype(str).str.strip()
        df = df[~df['Aspect'].isin(['Others', 'Other'])]

        # 4. Load existing pivot if present (seamless append: keep old months, overwrite new ones)
        if output_path.exists():
            existing = pd.read_csv(output_path, encoding="utf-8-sig")
            existing_months = set(existing['date'].astype(str))
            new_months = set(df['date'].astype(str))
            months_to_rebuild = existing_months | new_months
        else:
            existing = None
            months_to_rebuild = None

        # 5. Build pivot from ALL ABSA data (handles both historical seed + new months)
        pivot_df = df.pivot_table(
            index='date',
            columns='Aspect',
            values='sentiment_score',
            aggfunc='mean'
        ).round(4).reset_index()

        # If existing file had months not present in new ABSA data, keep them too
        if existing is not None:
            old_only = existing[~existing['date'].isin(pivot_df['date'])]
            pivot_df = pd.concat([old_only, pivot_df], ignore_index=True)
            pivot_df = pivot_df.sort_values('date').reset_index(drop=True)

        # 6. Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pivot_df.to_csv(output_path, index=False, encoding="utf-8-sig")

        print("--- Success! ---")
        print(f"Wide-format file saved to: {output_path}")
        print(f"Months: {len(pivot_df)}  |  Columns: {list(pivot_df.columns)}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    analyze_and_pivot_sentiment(IN_ABSA, OUT_CSV)
