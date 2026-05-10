import sys
import pandas as pd
from pathlib import Path

# ─── resolve project root & import config ───
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from config import Dirs, Files

IN_ABSA = Dirs.PIPELINE_DATA / "3_absa_results"   # directory of monthly CSVs from step 3

OUT_DIR = Dirs.ABSA_FEAT
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = Files.ASPECT_FEATURES

DATE_COL = "published_at"
ASPECT_COL = "Aspect"
SENTIMENT_SCORE_COL = "sentiment_score"


def month_start(s):
    return pd.to_datetime(s, errors="coerce").dt.to_period("M").dt.to_timestamp()


def main():
    # IN_ABSA can be a directory (of monthly CSVs from step 3) or a single CSV
    if IN_ABSA.is_dir():
        csv_files = sorted(IN_ABSA.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {IN_ABSA}")
        df = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)
        print(f"Loaded {len(csv_files)} CSV files from {IN_ABSA}")
    else:
        df = pd.read_csv(IN_ABSA)
        print(f"Loaded {IN_ABSA}")

    # Validate required columns
    for c in [DATE_COL, ASPECT_COL, SENTIMENT_SCORE_COL]:
        if c not in df.columns:
            raise ValueError(f"Missing column '{c}'. Found: {df.columns.tolist()}")

    # Clean
    df = df.copy()
    df["date"] = month_start(df[DATE_COL])
    df[ASPECT_COL] = df[ASPECT_COL].astype(str).str.strip()
    df[SENTIMENT_SCORE_COL] = pd.to_numeric(df[SENTIMENT_SCORE_COL], errors="coerce")

    # Drop invalid rows
    df = df.dropna(subset=["date", ASPECT_COL, SENTIMENT_SCORE_COL])
    df = df[df[ASPECT_COL] != "Other"]

    # Compute average sentiment per (month, aspect)
    avg_df = (
        df.groupby(["date", ASPECT_COL])[SENTIMENT_SCORE_COL]
        .mean()
        .reset_index()
    )

    # Wide format: one column per aspect
    wide = avg_df.pivot_table(
        index="date",
        columns=ASPECT_COL,
        values=SENTIMENT_SCORE_COL,
        aggfunc="mean",
    )

    # Rename columns -> {aspect}_avg_sentiment
    wide.columns = [f"{asp}" for asp in wide.columns]

    wide = wide.reset_index().sort_values("date")

    # MERGE with existing historical features to prevent overwriting
    if OUT_CSV.exists():
        try:
            old_wide = pd.read_csv(OUT_CSV)
            old_wide["date"] = pd.to_datetime(old_wide["date"])
            wide["date"] = pd.to_datetime(wide["date"])
            
            # Combine, keeping the new data for any overlapping dates
            combined = pd.concat([old_wide[~old_wide["date"].isin(wide["date"])], wide], ignore_index=True)
            wide = combined.sort_values("date")
        except Exception as e:
            print(f"Warning: Could not merge with existing {OUT_CSV}: {e}")

    # Format date back to string YYYY-MM for saving
    wide["date"] = wide["date"].dt.strftime("%Y-%m")
    wide.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    print("Saved:", OUT_CSV)
    print("Columns:", len(wide.columns))
    print(wide.tail(5).to_string(index=False))


if __name__ == "__main__":
    main()