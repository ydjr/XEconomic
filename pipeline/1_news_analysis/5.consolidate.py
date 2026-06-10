import argparse
import pickle
import pandas as pd
from darts import TimeSeries, concatenate
from darts.dataprocessing.transformers import MissingValuesFiller
from pathlib import Path
import warnings
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import Dirs, Files, Pipeline

warnings.filterwarnings("ignore")


def load_indicator(filepath, value_col, rename, freq="MS", resample_method=None):
    print(f"Loading {filepath.name}...")
    df = pd.read_csv(filepath, parse_dates=["date"]).set_index("date")

    if value_col not in df.columns:
        raise ValueError(f"Column '{value_col}' not found in {filepath.name}")

    df = df[[value_col]].rename(columns={value_col: rename})

    ts = TimeSeries.from_dataframe(
        df,
        freq=freq,
        fill_missing_dates=True,
    )

    if resample_method:
        ts = ts.resample(resample_method)

    return ts


def load_all_indicators(indicators_dir: Path):
    indicators = {}

    # target
    cci_ts = load_indicator(
        indicators_dir / "cci.csv",
        value_col="cci_overall",
        rename="cci",
        freq="MS",
    )

    # covariates
    indicators["cpi"] = load_indicator(
        indicators_dir / "cpi.csv",
        value_col="value",
        rename="cpi",
        freq="MS",
    )

    indicators["gdp"] = load_indicator(
        indicators_dir / "gdp_monthly.csv",
        value_col="value",
        rename="gdp",
        freq="MS",
    )

    # indicators["exchange_rate"] = load_indicator(
    #     indicators_dir / "exchange_rate.csv",
    #     value_col="value",
    #     rename="exchange_rate",
    #     freq="MS",
    # )

    # indicators["policy_rate"] = load_indicator(
    #     indicators_dir / "policy_rate.csv",
    #     value_col="value",
    #     rename="policy_rate",
    #     freq="MS",
    # )

    # indicators["export_vol"] = load_indicator(
    #     indicators_dir / "export_vol.csv",
    #     value_col="value",
    #     rename="export_vol",
    #     freq="MS",
    # )

    # indicators["tourist_arrivals"] = load_indicator(
    #     indicators_dir / "tourist_arrivals.csv",
    #     value_col="value",
    #     rename="tourist_arrivals",
    #     freq="MS",
    # )

    indicators["unemployment_rate"] = load_indicator(
        indicators_dir / "unemployment_rate.csv",
        value_col="value",
        rename="unemployment_rate",
        freq="MS",
    )

    indicators["impi"] = load_indicator(
        indicators_dir / "impi.csv",
        value_col="value",
        rename="impi",
        freq="MS",
    )

    indicators["expi"] = load_indicator(
        indicators_dir / "expi.csv",
        value_col="value",
        rename="expi",
        freq="MS",
    )

    return cci_ts, indicators


def load_sentiment_features(features_path):
    """
    Load sentiment features as multivariate TimeSeries.

    Expects: a CSV with 'date' + feature columns
    Example features: 'เศรษฐกิจไทย_avg_sentiment', 'เศรษฐกิจไทย_news_count', ...
    """
    print(f"Loading {features_path.name}...")
    df = pd.read_csv(features_path, parse_dates=["date"]).set_index("date")

    feat_cols = [c for c in df.columns if c != "date"]
    if not feat_cols:
        raise ValueError(f"No feature columns found in {features_path}")

    # Fill missing numeric values
    df[feat_cols] = df[feat_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

    sentiment_ts = TimeSeries.from_dataframe(
        df[feat_cols],
        freq="MS",
        fill_missing_dates=True,
        fillna_value=0,
    )

    print(f"  Loaded {len(feat_cols)} features")
    return sentiment_ts

def align_and_merge(cci_ts, indicators, sentiment_ts, emb_ts=None, mode="full"):
    print("\n=== Aligning Time Series (CCI as base timeline) ===")

    indicator_list = list(indicators.values())

    start_time = cci_ts.start_time()
    end_time   = cci_ts.end_time()
    full_idx   = pd.date_range(start_time, end_time, freq="MS")

    print(f"Base time range (CCI): {start_time} to {end_time}")

    cci_aligned = cci_ts.slice(start_time, end_time)

    # Align sentiment
    sent_df = sentiment_ts.slice(start_time, end_time).to_dataframe(copy=True)
    sent_df = sent_df.reindex(full_idx).fillna(0)
    sentiment_aligned = TimeSeries.from_dataframe(sent_df, freq="MS")

    # Align indicators
    indicators_aligned = []
    for ind in indicator_list:
        ind_df = ind.to_dataframe(copy=True).reindex(full_idx).ffill().bfill()
        indicators_aligned.append(TimeSeries.from_dataframe(ind_df, freq="MS"))
        
    covariates_aligned = concatenate(indicators_aligned + [sentiment_aligned], axis=1)

    print(f"Target shape: {cci_aligned.values().shape}")
    print(f"Covariates shape: {covariates_aligned.values().shape}")
    print(f"  {covariates_aligned.n_components} total features")

    return cci_aligned, covariates_aligned

def handle_missing_values(cci_ts, covariates_ts):
    print("\n=== Handling Missing Values ===")
    filler = MissingValuesFiller(fill="auto")

    cci_missing = pd.isna(cci_ts.to_dataframe()).sum().sum()
    cov_missing = pd.isna(covariates_ts.to_dataframe()).sum().sum()
    print(f"Missing values - Target: {cci_missing}, Covariates: {cov_missing}")

    if cci_missing > 0:
        cci_ts = filler.transform(cci_ts)
        print("  Filled target missing values")

    if cov_missing > 0:
        covariates_ts = filler.transform(covariates_ts)
        print("  Filled covariates missing values")

    return cci_ts, covariates_ts


def save_dataset(cci_ts, covariates_ts, output_path, save_csv=True):
    print("\n=== Saving Dataset ===")
    with open(output_path, "wb") as f:
        pickle.dump(
            {
                "target": cci_ts,
                "covariates": covariates_ts,
                "target_name": "cci_overall",
                "covariate_names": covariates_ts.components.tolist(),
            },
            f,
        )

    print(f"Saved Darts dataset to: {output_path}")

    if save_csv:
        csv_path = output_path.with_suffix(".csv")
        combined_df = pd.concat(
            [cci_ts.to_dataframe(copy=True), covariates_ts.to_dataframe(copy=True)], axis=1
        )
        combined_df.to_csv(csv_path, index_label="date")
        print(f"Saved CSV for inspection: {csv_path}")
        print("\nDataset Summary:")
        print(f"  Time range: {combined_df.index[0]} to {combined_df.index[-1]}")
        print(f"  Total months: {len(combined_df)}")
        print(f"  Target: cci_overall")
        print(f"  Covariates: {len(covariates_ts.components)} features")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(Files.ASPECT_FEATURES))
    parser.add_argument("--output", default=str(Files.AVG_SENT_INDI).replace('.csv', '.pkl'))
    args = parser.parse_args()

    indicators_dir = Dirs.INDICATORS
    features_path  = Path(args.input)
    output_path    = Path(args.output)

    print("=" * 60)
    print("Creating Darts Dataset")
    print("=" * 60)

    print("\n### Step 1: Loading Data ###")
    cci_ts, indicators = load_all_indicators(indicators_dir)
    sentiment_ts = load_sentiment_features(features_path)

    print("\n### Step 2: Aligning Data ###")
    cci_aligned, covariates_aligned = align_and_merge(
        cci_ts, indicators, sentiment_ts
    )

    print("\n### Step 3: Handling Missing Values ###")
    cci_final, covariates_final = handle_missing_values(cci_aligned, covariates_aligned)

    print("\n### Step 4: Saving ###")
    save_dataset(cci_final, covariates_final, output_path)

    print("\n" + "=" * 60)
    print("Dataset Creation Complete")
    print("=" * 60)

    return cci_final, covariates_final


if __name__ == "__main__":
    main()
