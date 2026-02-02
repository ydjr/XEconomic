# ============================================================
# pipeline/backtest.py
# ------------------------------------------------------------
# PURPOSE (Model Selection):
# - Rolling-origin backtest for Darts XGBModel
# - Optional grid search over XGB params (time-series safe)
# - Uses past_covariates (all cols except date + target)
# - Saves artifacts in BOTH CSV + JSON formats
#
# OUTPUT (artifacts/backtest/)
# - backtest_metrics.csv, backtest_metrics.json
# - backtest_forecasts_best.csv, backtest_forecasts_best.json
# - best_params_xgb.csv, best_params_xgb.json
# ============================================================

import json
import os
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from darts import TimeSeries
from darts.models import XGBModel

from utils import save_csv, save_json, mae, rmse, mape

# =====================
# CONFIG
# =====================
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
INPUT_CSV = DATA_DIR / "indicators/cci.csv"

ART_DIR = BASE_DIR / "artifacts" / "backtest"
ART_DIR.mkdir(parents=True, exist_ok=True)

DATE_COL = "date"
TARGET_COL = "cci_overall"

HORIZON = 3

# keep these fixed (problem formulation)
LAGS_TARGET = 3
LAGS_PAST_COVS = 3

# backtest windowing
MIN_TRAIN_POINTS = 24     # must be >= max(lags) + buffer; adjust if your series is short
STRIDE = 1                # 1 month step
RETRAIN = True            # re-train at each origin (good for tuning)

# dataset transforms
USE_LOG_GDP = True

# optionally remove covariates you don't want to include
DROP_COVARIATES = [
    # "cpi", "unemployment", "policy_rate", "import_price", "export_price", "gdp",
]

# grid search toggle
DO_GRIDSEARCH = True

# a small, strong grid (12 combos). adjust freely.
PARAM_GRID = {
    "max_depth": [3, 4, 5],
    "learning_rate": [0.03, 0.05],
    "n_estimators": [400, 800],
    "subsample": [0.8],
    "colsample_bytree": [0.8],
}

# fixed params (not searched)
XGB_FIXED = dict(
    objective="reg:squarederror",
    random_state=42,
    n_jobs=-1,
    tree_method="hist",
)


# =====================
# METRICS
# =====================

def direction_accuracy(y_true: np.ndarray, y_pred: np.ndarray, y_prev: np.ndarray) -> float:
    """
    Direction compares (current - previous actual) sign vs (pred - previous actual) sign.
    y_prev is previous actual value for each forecasted point.
    """
    true_dir = np.sign(y_true - y_prev)
    pred_dir = np.sign(y_pred - y_prev)
    return float(np.mean(true_dir == pred_dir))


# =====================
# UTILS
# =====================

def grid_to_param_list(grid: dict) -> list[dict]:
    keys = list(grid.keys())
    combos = []
    for vals in product(*[grid[k] for k in keys]):
        combos.append(dict(zip(keys, vals)))
    return combos


def to_month_str(ts) -> str:
    # ts is pandas Timestamp-like
    return pd.to_datetime(ts).strftime("%Y-%m-%d")


# =====================
# BACKTEST CORE
# =====================
def run_backtest_for_params(
    y: TimeSeries,
    past_covs: TimeSeries | None,
    params: dict,
) -> tuple[pd.DataFrame, dict]:
    """
    Returns:
      - df_forecasts: one row per origin+horizon
      - metrics: dict with aggregate metrics (overall + per-horizon)
    """

    model = XGBModel(
        lags=LAGS_TARGET,
        lags_past_covariates=LAGS_PAST_COVS if past_covs is not None else None,
        output_chunk_length=HORIZON,
        **XGB_FIXED,
        **params,
    )

    # choose deterministic start point based on MIN_TRAIN_POINTS
    if len(y) <= MIN_TRAIN_POINTS + HORIZON:
        raise ValueError(
            f"Series too short. len(y)={len(y)} but need > MIN_TRAIN_POINTS({MIN_TRAIN_POINTS}) + HORIZON({HORIZON})."
        )

    start_time = y.time_index[MIN_TRAIN_POINTS]

    forecasts = model.historical_forecasts(
        series=y,
        past_covariates=past_covs,
        start=start_time,
        forecast_horizon=HORIZON,
        stride=STRIDE,
        retrain=RETRAIN,
        last_points_only=False,   # keep full paths
        verbose=False,
    )

    rows = []

    # Each element f is a TimeSeries forecast path of length HORIZON
    for f in forecasts:
        f_df = f.to_dataframe().reset_index()
        f_time_col = f_df.columns[0]
        f_df = f_df.rename(columns={f_time_col: "forecast_month", TARGET_COL: "y_pred"})
        f_df["forecast_month"] = pd.to_datetime(f_df["forecast_month"])

        origin_time = f.start_time()  # first forecasted timestamp
        # The origin's "last actual" is one step before the first forecast point
        # We use it to compute direction accuracy per point.
        prev_time = y.time_index[y.time_index.get_loc(origin_time) - 1]
        prev_actual = float(y[prev_time].values().squeeze())

        # Ground truth slice for the same window
        truth = y.slice(f.start_time(), f.end_time())
        t_df = truth.to_dataframe().reset_index()
        t_time_col = t_df.columns[0]
        t_df = t_df.rename(columns={t_time_col: "forecast_month", TARGET_COL: "y_true"})
        t_df["forecast_month"] = pd.to_datetime(t_df["forecast_month"])

        merged = pd.merge(f_df, t_df, on="forecast_month", how="inner").sort_values("forecast_month")
        merged["horizon"] = np.arange(1, len(merged) + 1, dtype=int)
        merged["origin_last_actual_month"] = to_month_str(prev_time)
        merged["origin_last_actual_value"] = prev_actual

        for _, r in merged.iterrows():
            rows.append(
                {
                    "origin_last_actual_month": r["origin_last_actual_month"],
                    "forecast_month": to_month_str(r["forecast_month"]),
                    "horizon": int(r["horizon"]),
                    "y_true": float(r["y_true"]),
                    "y_pred": float(r["y_pred"]),
                    "prev_actual": float(r["origin_last_actual_value"]),
                }
            )

    df_forecasts = pd.DataFrame(rows)
    if df_forecasts.empty:
        raise RuntimeError("No forecasts produced by historical_forecasts(). Check start/stride settings.")

    # aggregate metrics
    y_true = df_forecasts["y_true"].to_numpy(dtype=float)
    y_pred = df_forecasts["y_pred"].to_numpy(dtype=float)
    y_prev = df_forecasts["prev_actual"].to_numpy(dtype=float)

    metrics = {
        "mae": mae(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "mape": mape(y_true, y_pred),
        "dir_acc": direction_accuracy(y_true, y_pred, y_prev),
    }

    # per-horizon metrics
    per_h = []
    for h in sorted(df_forecasts["horizon"].unique()):
        g = df_forecasts[df_forecasts["horizon"] == h]
        yt = g["y_true"].to_numpy(dtype=float)
        yp = g["y_pred"].to_numpy(dtype=float)
        ypv = g["prev_actual"].to_numpy(dtype=float)
        per_h.append(
            {
                "horizon": int(h),
                "mae": mae(yt, yp),
                "rmse": rmse(yt, yp),
                "mape": mape(yt, yp),
                "dir_acc": direction_accuracy(yt, yp, ypv),
            }
        )
    metrics["per_horizon"] = per_h

    return df_forecasts, metrics


def main():
    df = pd.read_csv(INPUT_CSV)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    df = df.sort_values(DATE_COL).reset_index(drop=True)

    # numeric coercion
    for c in df.columns:
        if c != DATE_COL:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # log(gdp) optional
    if USE_LOG_GDP and "gdp" in df.columns:
        if (df["gdp"] <= 0).any():
            raise ValueError("gdp has non-positive values; cannot apply log(gdp).")
        df["gdp"] = np.log(df["gdp"])

    # keep rows where target exists
    df = df.dropna(subset=[TARGET_COL]).copy()

    # build target
    y = TimeSeries.from_dataframe(df, time_col=DATE_COL, value_cols=TARGET_COL)

    # build past covariates (all other cols except dropped)
    cov_cols = [
        c for c in df.columns
        if c not in [DATE_COL, TARGET_COL]
        and c not in DROP_COVARIATES
    ]
    past_covs = None
    if len(cov_cols) > 0:
        past_covs = TimeSeries.from_dataframe(df, time_col=DATE_COL, value_cols=cov_cols)

    # param list
    if DO_GRIDSEARCH:
        param_list = grid_to_param_list(PARAM_GRID)
    else:
        # single run with fixed-ish defaults
        param_list = [dict(max_depth=4, learning_rate=0.03, n_estimators=800, subsample=0.8, colsample_bytree=0.8)]

    metrics_rows = []
    best = {"score": float("inf"), "params": None, "metrics": None, "forecasts": None}

    for i, params in enumerate(param_list, start=1):
        df_fc, m = run_backtest_for_params(y=y, past_covs=past_covs, params=params)

        # choose selection metric (stable): MAE overall
        score = m["mae"]

        row = {
            "model": "darts_xgb",
            "run_id": i,
            **params,
            "mae": m["mae"],
            "rmse": m["rmse"],
            "mape": m["mape"],
            "dir_acc": m["dir_acc"],
        }
        metrics_rows.append(row)

        if score < best["score"]:
            best = {"score": score, "params": params, "metrics": m, "forecasts": df_fc}

    df_metrics = pd.DataFrame(metrics_rows).sort_values("mae", ascending=True).reset_index(drop=True)

    # save all metrics
    save_csv(df_metrics, ART_DIR / "backtest_metrics.csv")
    save_json(
        {
            "model": "darts_xgb",
            "selection_metric": "mae",
            "runs": df_metrics.to_dict(orient="records"),
        },
        ART_DIR / "backtest_metrics.json",
    )

    # save best params
    df_best_params = pd.DataFrame([{**best["params"], "selection_metric": "mae", "best_mae": best["score"]}])
    save_csv(df_best_params, ART_DIR / "best_params_xgb.csv")
    save_json(df_best_params.iloc[0].to_dict(), ART_DIR / "best_params_xgb.json")

    # save best forecasts (full backtest forecast table)
    df_best_fc = best["forecasts"].copy()
    # nice rounding for readability
    df_best_fc["y_true"] = df_best_fc["y_true"].round(4)
    df_best_fc["y_pred"] = df_best_fc["y_pred"].round(4)

    save_csv(df_best_fc, ART_DIR / "backtest_forecasts_best.csv")
    save_json(
        {
            "model": "darts_xgb",
            "selection_metric": "mae",
            "best_params": best["params"],
            "forecasts": df_best_fc.to_dict(orient="records"),
            "metrics": {
                "overall": {
                    "mae": best["metrics"]["mae"],
                    "rmse": best["metrics"]["rmse"],
                    "mape": best["metrics"]["mape"],
                    "dir_acc": best["metrics"]["dir_acc"],
                },
                "per_horizon": best["metrics"]["per_horizon"],
            },
        },
        ART_DIR / "backtest_forecasts_best.json",
    )

    print("Done.")
    print("Best params:", best["params"])
    print("Best MAE:", best["score"])


if __name__ == "__main__":
    main()
