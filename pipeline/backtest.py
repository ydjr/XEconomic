# ============================================================
# pipeline/backtest.py
# ------------------------------------------------------------
# PURPOSE (Evaluation):
# - Rolling-origin backtest for Darts XGBModel
# - For each origin month:
#     train on history up to origin
#     predict next H months
#     compare with ground truth
# - Save artifacts in BOTH CSV + JSON formats
#
# OUTPUT (artifacts/)
# - backtest_forecasts.csv, backtest_forecasts.json
# - backtest_metrics.csv,   backtest_metrics.json
# ============================================================

import os
import numpy as np
import pandas as pd

from darts import TimeSeries
from darts.models import XGBModel

from utils import ensure_dir, save_csv, save_json, mae, rmse, mape

# =====================
# CONFIG
# =====================
INPUT_CSV = "./data/macro_monthly_overlapv2.csv"
ART_DIR = "artifacts/backtest"

DATE_COL = "date"
TARGET_COL = "cci_overall"

HORIZON = 3

LAGS_TARGET = 3
LAGS_PAST_COVS = 3

MIN_TRAIN_POINTS = 12
USE_LOG_GDP = True

XGB_PARAMS = dict(
    n_estimators=800,
    learning_rate=0.03,
    max_depth=4,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    random_state=42,
    n_jobs=-1,
    tree_method="hist",
)

# =====================
# JSON CONVERTERS
# =====================
def forecasts_df_to_json(df_fc: pd.DataFrame) -> dict:
    # store as list of records (easy for frontend)
    return {
        "model": "darts_xgb",
        "horizon": int(df_fc["horizon"].max()) if not df_fc.empty else HORIZON,
        "records": df_fc.to_dict(orient="records"),
    }


def metrics_df_to_json(df_metrics: pd.DataFrame) -> dict:
    return {
        "model": "darts_xgb",
        "records": df_metrics.to_dict(orient="records"),
    }

# =====================
# MAIN
# =====================
def main():
    ensure_dir(ART_DIR)

    df = pd.read_csv(INPUT_CSV)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    df = df.sort_values(DATE_COL).reset_index(drop=True)

    for c in df.columns:
        if c != DATE_COL:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if USE_LOG_GDP and "gdp" in df.columns:
        if (df["gdp"] <= 0).any():
            raise ValueError("gdp has non-positive values; cannot apply log(gdp).")
        df["gdp"] = np.log(df["gdp"])

    df = df.dropna(subset=[TARGET_COL]).copy()

    y = TimeSeries.from_dataframe(df, time_col=DATE_COL, value_cols=TARGET_COL)

    cov_cols = [c for c in df.columns if c not in [DATE_COL, TARGET_COL]]
    past_covs = None
    if len(cov_cols) > 0:
        past_covs = TimeSeries.from_dataframe(df, time_col=DATE_COL, value_cols=cov_cols)

    rows = []

    total_len = len(y)
    start_idx = max(MIN_TRAIN_POINTS, LAGS_TARGET)

    # origin i: train on y[:i], predict next H
    for i in range(start_idx, total_len - HORIZON + 1):
        y_train = y[:i]
        cov_train = past_covs[:i] if past_covs is not None else None

        model = XGBModel(
            lags=LAGS_TARGET,
            lags_past_covariates=LAGS_PAST_COVS if cov_train is not None else None,
            output_chunk_length=HORIZON,
            **XGB_PARAMS,
        )
        model.fit(y_train, past_covariates=cov_train)

        cov_for_pred = past_covs[: i + HORIZON] if past_covs is not None else None
        fc = model.predict(n=HORIZON, past_covariates=cov_for_pred)

        origin_month = y_train.end_time()

        y_true = y[i : i + HORIZON]

        pred_df = fc.to_dataframe().reset_index().rename(columns={"index": DATE_COL})
        true_df = y_true.to_dataframe().reset_index().rename(columns={"index": DATE_COL})

        merged = pred_df.merge(true_df, on=DATE_COL, suffixes=("_pred", "_true"))

        for step in range(len(merged)):
            forecast_month = pd.to_datetime(merged.loc[step, DATE_COL])
            y_pred = float(merged.loc[step, f"{TARGET_COL}_pred"])
            y_t = float(merged.loc[step, f"{TARGET_COL}_true"])

            rows.append({
                "origin_month": origin_month.strftime("%Y-%m-%d"),
                "forecast_month": forecast_month.strftime("%Y-%m-%d"),
                "horizon": int(step + 1),
                "y_true": round(y_t, 6),
                "y_pred": round(y_pred, 6),
                "error": round(y_pred - y_t, 6),
            })

    df_fc = pd.DataFrame(rows)

    # Make sure these columns exist even if df_fc is empty
    required_cols = ["origin_month", "forecast_month", "horizon", "y_true", "y_pred", "error"]
    for c in required_cols:
        if c not in df_fc.columns:
            df_fc[c] = pd.Series(dtype="float" if c in ["y_true", "y_pred", "error"] else "object")

    # Save forecasts CSV + JSON
    save_csv(df_fc, os.path.join(ART_DIR, "backtest_forecasts.csv"))
    save_json(forecasts_df_to_json(df_fc), os.path.join(ART_DIR, "backtest_forecasts.json"))

    # Metrics per horizon + overall
    metrics_rows = []

    for h in range(1, HORIZON + 1):
        part = df_fc[df_fc["horizon"] == h].copy()
        if part.empty:
            continue
        err = part["error"].values.astype(float)
        metrics_rows.append({
            "horizon": int(h),
            "n": int(len(part)),
            "MAE": round(mae(err), 6),
            "RMSE": round(rmse(err), 6),
            "MAPE": round(mape(part["y_true"].values, part["y_pred"].values), 6),
        })

    if not df_fc.empty:
        err = df_fc["error"].values.astype(float)
        metrics_rows.append({
            "horizon": "overall",
            "n": int(len(df_fc)),
            "MAE": round(mae(err), 6),
            "RMSE": round(rmse(err), 6),
            "MAPE": round(mape(df_fc["y_true"].values, df_fc["y_pred"].values), 6),
        })

    df_metrics = pd.DataFrame(metrics_rows)

    # Save metrics CSV + JSON
    save_csv(df_metrics, os.path.join(ART_DIR, "backtest_metrics.csv"))
    save_json(metrics_df_to_json(df_metrics), os.path.join(ART_DIR, "backtest_metrics.json"))

    print("\nDone.")
    print("Backtest forecasts:", os.path.join(ART_DIR, "backtest_forecasts.csv"), "and .json")
    print("Backtest metrics  :", os.path.join(ART_DIR, "backtest_metrics.csv"), "and .json")


if __name__ == "__main__":
    main()
