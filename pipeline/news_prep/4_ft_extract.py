import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

IN_ABSA = DATA_DIR / "absa_2024-2025.csv"

OUT_DIR = DATA_DIR / "4_absa_features"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "aspect_monthly_features.csv"

DATE_COL = "published_at"
ASPECT_COL = "Aspect"
SENTIMENT_SCORE_COL = "sentiment_score"


def month_start(s):
    return pd.to_datetime(s, errors="coerce").dt.to_period("M").dt.to_timestamp()


def main():
    df = pd.read_csv(IN_ABSA)

    # Validate required columns
    for c in [DATE_COL, ASPECT_COL, SENTIMENT_SCORE_COL]:
        if c not in df.columns:
            raise ValueError(f"Missing column '{c}' in {IN_ABSA}. Found: {df.columns.tolist()}")

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

    wide.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    print("Saved:", OUT_CSV)
    print("Columns:", len(wide.columns))
    print(wide.tail(5).to_string(index=False))


if __name__ == "__main__":
    main()