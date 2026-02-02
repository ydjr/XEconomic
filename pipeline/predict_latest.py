# ============================================================
# pipeline/predict_latest.py
# ------------------------------------------------------------
# PURPOSE (Production Forecast):
# - Train on all available data (where target exists)
# - Predict next H months (path forecast)
# - Explain each horizon with Darts SHAP
# - Save artifacts in BOTH CSV + JSON formats
#
# OUTPUT (artifacts/)
# - latest_forecast.csv, latest_forecast.json
# - latest_explain.csv,  latest_explain.json
# ============================================================

import os
import numpy as np
import pandas as pd
from pathlib import Path

from darts import TimeSeries
from darts.models import XGBModel
from darts.explainability.shap_explainer import ShapExplainer

from utils import ensure_dir, save_csv, save_json

# =====================
# CONFIG
# =====================
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
INPUT_CSV = DATA_DIR / "indicators/cci.csv"
ART_DIR = BASE_DIR / "artifacts_v1"

DATE_COL = "date"
TARGET_COL = "cci_overall"

HORIZON = 3
TOPK_LOCAL = 15

LAGS_TARGET = 3
LAGS_PAST_COVS = 3

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

DROP_COVARIATES = [
    "export_price",
    "import_price",
    "cpi",
    "unemployment",
    "policy_rate",
    "gdp",
]

# =====================
# JSON CONVERTERS
# =====================
def forecast_df_to_json(df_forecast: pd.DataFrame) -> dict:
    last_actual_month = str(df_forecast["last_actual_month"].iloc[0])
    horizon = int(df_forecast["horizon"].max())

    forecast_path = []
    for _, r in df_forecast.sort_values("horizon").iterrows():
        forecast_path.append({
            "horizon": int(r["horizon"]),
            "forecast_month": str(r["forecast_month"]),
            "y_pred": float(r["y_pred"]),
        })

    return {
        "model": "darts_xgb",
        "last_actual_month": last_actual_month,
        "horizon": horizon,
        "forecast_path": forecast_path,
    }


def explain_df_to_json(df_explain: pd.DataFrame) -> dict:
    last_actual_month = str(df_explain["last_actual_month"].iloc[0])
    horizon = int(df_explain["horizon"].max())

    explain_path = []
    for h, g in df_explain.groupby("horizon"):
        g = g.sort_values("rank")
        explain_path.append({
            "horizon": int(h),
            "forecast_month": str(g["forecast_month"].iloc[0]),
            "topk": int(g["rank"].max()),
            "explanations": [
                {
                    "feature": str(r["feature"]),
                    "value": float(r["feature_value"]),
                    "shap_value": float(r["shap_value"]),
                }
                for _, r in g.iterrows()
            ]
        })

    explain_path = sorted(explain_path, key=lambda x: x["horizon"])

    return {
        "model": "darts_xgb",
        "last_actual_month": last_actual_month,
        "horizon": horizon,
        "explain_path": explain_path,
    }

# =====================
# MAIN
# =====================
def main():
    ensure_dir(ART_DIR)

    df = pd.read_csv(INPUT_CSV)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    df = df.sort_values(DATE_COL).reset_index(drop=True)

    # Ensure numeric
    for c in df.columns:
        if c != DATE_COL:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=[TARGET_COL])

    # Target series
    y = TimeSeries.from_dataframe(df, time_col=DATE_COL, value_cols=TARGET_COL)
    last_actual_month = y.end_time()

    cov_cols = [c for c in df.columns if c not in [DATE_COL, TARGET_COL] and c not in DROP_COVARIATES]
    past_covs = TimeSeries.from_dataframe(df, time_col=DATE_COL, value_cols=cov_cols) if cov_cols else None

    # Train model
    model = XGBModel(
        lags=LAGS_TARGET,
        lags_past_covariates=LAGS_PAST_COVS if past_covs is not None else None,
        output_chunk_length=HORIZON,
        **XGB_PARAMS,
    )
    model.fit(y, past_covariates=past_covs)

    fc = model.predict(n=HORIZON, past_covariates=past_covs)
    df_fc = fc.to_dataframe().reset_index()
    time_col = df_fc.columns[0]
    df_fc = df_fc.rename(columns={time_col: "forecast_month"})

    df_fc["forecast_month"] = pd.to_datetime(df_fc["forecast_month"]).dt.strftime("%Y-%m-%d")
    df_fc["horizon"] = np.arange(1, HORIZON + 1, dtype=int)
    df_fc["last_actual_month"] = last_actual_month.strftime("%Y-%m-%d")
    df_fc = df_fc.rename(columns={TARGET_COL: "y_pred"})

    df_latest_forecast = df_fc[["last_actual_month", "forecast_month", "horizon", "y_pred"]].copy()
    df_latest_forecast["y_pred"] = df_latest_forecast["y_pred"].round(1)

    # Save forecast CSV + JSON
    save_csv(df_latest_forecast, os.path.join(ART_DIR, "latest_forecast_sent.csv"))
    save_json(forecast_df_to_json(df_latest_forecast), os.path.join(ART_DIR, "latest_forecast_sent.json"))

    # Forecast path metadata for SHAP CSV/JSON
    forecast_path = df_latest_forecast.sort_values("horizon")[["forecast_month", "horizon"]].to_dict(orient="records")

    # =========================
    # SHAP (Darts)
    # =========================
    explainer = ShapExplainer(model)
    horizons = list(range(1, HORIZON + 1))

    explain_results = explainer.explain(
        foreground_series=y,
        foreground_past_covariates=past_covs,
        foreground_future_covariates=None,
        horizons=horizons,
    )

    rows = []

    for h in horizons:
        shap_ts = explain_results.get_explanation(horizon=h)      # TimeSeries of SHAP values
        feat_ts = explain_results.get_feature_values(horizon=h)   # TimeSeries of feature values

        shap_df = shap_ts.to_dataframe()
        feat_df = feat_ts.to_dataframe()

        # latest explainable timestamp
        shap_last = shap_df.iloc[-1]
        feat_last = feat_df.iloc[-1]

        local = pd.DataFrame({
            "feature": shap_last.index.astype(str),
            "feature_value": feat_last.values.astype(float),
            "shap_value": shap_last.values.astype(float),
        })
        local["abs_shap"] = np.abs(local["shap_value"])
        local = local.sort_values("abs_shap", ascending=False).head(TOPK_LOCAL)
        local["rank"] = range(1, len(local) + 1)

        for _, r in local.iterrows():
            rows.append({
                "last_actual_month": last_actual_month.strftime("%Y-%m-%d"),
                "forecast_month": forecast_path[h - 1]["forecast_month"],
                "horizon": h,
                "feature": str(r["feature"]),
                "feature_value": float(r["feature_value"]),
                "shap_value": float(r["shap_value"]),
                "abs_shap": float(r["abs_shap"]),
                "rank": int(r["rank"]),
            })

    df_latest_explain = pd.DataFrame(rows)

    save_csv(df_latest_explain, os.path.join(ART_DIR, "latest_explain_sent.csv"))
    save_json(explain_df_to_json(df_latest_explain), os.path.join(ART_DIR, "latest_explain_sent.json"))

if __name__ == "__main__":
    main()
