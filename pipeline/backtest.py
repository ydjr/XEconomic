import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from darts import TimeSeries, concatenate
from darts.metrics import mae, rmse, mape
from darts.models import XGBModel, LightGBMModel, RandomForestModel

warnings.filterwarnings("ignore")

# ─── resolve project root & import config ───
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import Dirs, Files, Pipeline as PipelineCfg

# =========================
# CONFIG
# =========================
DATA_CSV = Files.AVG_SENT_INDI

ART_DIR = Dirs.BACKTEST_ART
MODELS_DIR = Dirs.BACKTEST_MDL
ART_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

DATE_COL = PipelineCfg.DATE_COL
TARGET_COL = PipelineCfg.TARGET_COL

FORECAST_HORIZON = PipelineCfg.FORECAST_HORIZON
STRIDE = PipelineCfg.STRIDE
START = PipelineCfg.BACKTEST_START
SHOW_WARNINGS = False


MODEL_PARAMS = {
    "xgb": {
        "n_estimators": [200],
        "max_depth": [3, 5],
        "learning_rate": [0.05, 0.1],
    },
    "lgbm": {
        "n_estimators": [200],
        "max_depth": [3, 5],
        "learning_rate": [0.05, 0.1],
    },
    "rf": {
        "n_estimators": [200],
        "max_depth": [5, 10],
    },
}

MODELS = [
    (XGBModel, "xgb"),
    (LightGBMModel, "lgbm"),
    (RandomForestModel, "rf"),
]


# =========================
# HELPERS
# =========================
def load_series():
    df = pd.read_csv(DATA_CSV)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    df = df.sort_values(DATE_COL).reset_index(drop=True)

    # force numeric (except date)
    for c in df.columns:
        if c != DATE_COL:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=[TARGET_COL]).copy()

    target = TimeSeries.from_dataframe(df, time_col=DATE_COL, value_cols=TARGET_COL, freq="MS")

    cov_cols = [c for c in df.columns if c not in [DATE_COL, TARGET_COL]]
    past_cov = None
    if cov_cols:
        past_cov = TimeSeries.from_dataframe(df, time_col=DATE_COL, value_cols=cov_cols, freq="MS")

    return target, past_cov, cov_cols


def direction_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) < 2:
        return 0.0
    a = np.diff(y_true)
    p = np.diff(y_pred)
    return float((np.sign(a) == np.sign(p)).mean() * 100.0)


def evaluate_from_historical_forecasts(target: TimeSeries, hf_list):
    # hf_list is a list[TimeSeries]; each element is 1-step (if last_points_only=True)
    preds = concatenate(hf_list)
    actual = target.slice(preds.start_time(), preds.end_time())

    out = {
        "mae": float(mae(actual, preds)),
        "rmse": float(rmse(actual, preds)),
        "mape": float(mape(actual, preds)),
        "direction_accuracy": direction_accuracy(
            actual.values(copy=False).flatten(),
            preds.values(copy=False).flatten()
        ),
    }
    return out, actual, preds


def save_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# =========================
# MAIN
# =========================
def main():
    target, past_cov, cov_cols = load_series()

    results = []

    for ModelCls, name in MODELS:
        if past_cov is None:
            raise ValueError("No past covariates found in CSV, but you requested using past_covariates.")
        
        PARAMS = {
            "lags": [1,2,3,6],
            "lags_past_covariates": [1,2,3,6],
            "output_chunk_length": [1],
            "random_state": [42],
            **MODEL_PARAMS[name],
        }

        # 1) gridsearch picks best params (includes lags + cov lags)
        best_model, best_params, best_score = ModelCls.gridsearch(
            parameters=PARAMS,
            series=target,
            past_covariates=past_cov,
            forecast_horizon=FORECAST_HORIZON,
            stride=STRIDE,
            start=START,
            metric=mape,
            verbose=False,
            show_warnings=SHOW_WARNINGS,
        )

        # 2) run a clean historical_forecasts for saving predictions + metrics
        hf = best_model.historical_forecasts(
            series=target,
            past_covariates=past_cov,
            start=START,
            forecast_horizon=FORECAST_HORIZON,
            stride=STRIDE,
            retrain=True,
            last_points_only=True,
            verbose=False,
            show_warnings=SHOW_WARNINGS,
        )

        metrics, actual, preds = evaluate_from_historical_forecasts(target, hf)

        # save per-model artifacts
        model_path = MODELS_DIR / f"{name}_best.pkl"
        best_model.save(str(model_path))

        pred_df = preds.to_dataframe().reset_index()
        pred_df.columns = ["date", "y_pred"]

        actual_df = actual.to_dataframe().reset_index()
        actual_df.columns = ["date", "y_true"]

        # merge
        pred_df = pred_df.merge(actual_df, on="date", how="inner")
        pred_df = pred_df[["date", "y_true", "y_pred"]]

        pred_df.to_csv(ART_DIR / f"{name}_predictions.csv", index=False)

        save_json(ART_DIR / f"{name}_best_params.json", best_params)
        save_json(ART_DIR / f"{name}_metrics.json", metrics)

        results.append({
            "model": name,
            "mape_gridsearch": float(best_score),
            "metrics": metrics,
            "best_params": best_params,
            "model_path": str(model_path),
        })

    # comparison table
    comp_rows = []
    for r in results:
        row = {"model": r["model"], **r["metrics"], **r["best_params"]}
        comp_rows.append(row)
    df_comp = pd.DataFrame(comp_rows).sort_values("mape")
    df_comp.to_csv(ART_DIR / "model_comparison.csv", index=False)
    save_json(ART_DIR / "model_comparison.json", comp_rows)

    # save best overall (by mape)
    best_overall = min(results, key=lambda x: x["metrics"]["mape"])
    save_json(MODELS_DIR / "best_overall.json", best_overall)

    print("Saved to:")
    print("  ", ART_DIR)
    print("  ", MODELS_DIR)
    print("Best overall:", best_overall["model"], "MAPE:", best_overall["metrics"]["mape"])


if __name__ == "__main__":
    main()
