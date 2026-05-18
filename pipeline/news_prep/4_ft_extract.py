import pandas as pd
from pathlib import Path

# --- Setup Paths ---
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

IN_ABSA = DATA_DIR / "2017-2026.csv"

# Output folder and file
OUT_DIR = DATA_DIR / "4_absa_features"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "aspect_monthly_features_pcafilter.csv"

def analyze_and_pivot_sentiment(file_path, output_path):
    try:
        # 1. Load data
        df = pd.read_csv(file_path)
        
        # 2. Clean and Format Time
        df['published_at'] = pd.to_datetime(df['published_at'], errors='coerce')
        df = df.dropna(subset=['published_at']) 
        df['date'] = df['published_at'].dt.to_period('M').astype(str)

        # 3. Clean Aspects & FILTER OUT OTHERS
        df['Aspect'] = df['Aspect'].astype(str).str.strip()
        df = df[~df['Aspect'].isin(['Others', 'Other'])]

        # 4. Create Wide Format (Pivot Table)
        pivot_df = df.pivot_table(
            index='date',
            columns='Aspect',
            values='sentiment_score',
            aggfunc='mean'
        )

        # 5. Clean up the DataFrame
        pivot_df = pivot_df.round(4).reset_index()

        # 6. Save to CSV 
        pivot_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        
        print(f"--- Success! ---")
        print(f"Wide-format file saved to: {output_path}")
        print(f"Columns created: {list(pivot_df.columns)}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    analyze_and_pivot_sentiment(IN_ABSA, OUT_CSV)
