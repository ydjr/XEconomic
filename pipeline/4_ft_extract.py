import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

IN_ABSA = DATA_DIR / "3_absa" / "news_sentiment_summary_all.csv"

OUT_DIR = DATA_DIR / "4_absa_features"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "aspect_monthly_features.csv"


DATE_COL = "published_at"
ASPECT_COL = "aspects"
SENTIMENT_COL = "impact_type"


def month_start(s):
    return pd.to_datetime(s, errors="coerce").dt.to_period("M").dt.to_timestamp()


def extract_news_count(df: pd.DataFrame) -> pd.DataFrame:
    """Total news count per (month, aspect)."""
    tmp = df.copy()
    tmp["date"] = month_start(tmp[DATE_COL])

    out = (
        tmp.groupby(["date", ASPECT_COL])
        .size()
        .reset_index(name="news_count")
        .rename(columns={ASPECT_COL: "aspect"})
    )
    return out


def extract_sentiment_count(df: pd.DataFrame) -> pd.DataFrame:
    """Sentiment counts per (month, aspect)."""
    tmp = df.copy()
    tmp["date"] = month_start(tmp[DATE_COL])

    pivot = (
        tmp.groupby(["date", ASPECT_COL, SENTIMENT_COL])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={ASPECT_COL: "aspect"})
    )

    for c in ["Positive", "Negative", "Neutral"]:
        if c not in pivot.columns:
            pivot[c] = 0

    pivot = pivot.rename(columns={"Positive": "pos_count", "Negative": "neg_count", "Neutral": "neu_count"})

    return pivot[["date", "aspect", "pos_count", "neg_count", "neu_count"]]


def main():
    df = pd.read_csv(IN_ABSA)
    df = df[df[ASPECT_COL] != "Other"].copy()

    for c in [DATE_COL, ASPECT_COL, SENTIMENT_COL]:
        if c not in df.columns:
            raise ValueError(f"Missing column '{c}' in {IN_ABSA}. Found: {df.columns.tolist()}")

    sent_df = extract_sentiment_count(df)
    news_df = extract_news_count(df)

    # Merge into ONE table
    feat = news_df.merge(sent_df, on=["date", "aspect"], how="left")

    # Fill missing sentiment counts with 0
    for c in ["pos_count", "neg_count", "neu_count"]:
        feat[c] = feat[c].fillna(0).astype(int)

    feat["news_count"] = feat["news_count"].fillna(0).astype(int)

    wide = feat.pivot_table(
        index="date",
        columns="aspect",
        values=["pos_count", "neg_count"],
        aggfunc="sum",
        fill_value=0,
    )

    # flatten columns
    wide.columns = [f"{aspect}_{metric}" for metric, aspect in wide.columns]
    wide = wide.reset_index().sort_values("date")

    wide.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print("Saved:", OUT_CSV)
    print("Columns:", len(wide.columns))
    print(wide.tail(5).to_string(index=False))


if __name__ == "__main__":
    main()
