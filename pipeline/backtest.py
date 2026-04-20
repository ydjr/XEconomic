import json
import shutil
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from darts import TimeSeries
from darts.metrics import mape as darts_mape, rmse as darts_rmse
from darts.models import XGBModel, BlockRNNModel, NHiTSModel
from darts.dataprocessing.transformers import Scaler as DartsScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.model_selection import ParameterGrid
from tqdm import tqdm

warnings.filterwarnings("ignore")

# ==========================================
# CONFIG
# ==========================================

DATA_CSV      = Path("data/2017-2025.csv")
RESULTS_DIR   = Path("results_backtest_allpoints")
ARTIFACTS_DIR = Path("artifacts_backtest_allpoints")
CACHE_DIR     = Path(".gridsearch_cache_backtest")

DATE_COL    = "date"
TARGET_COL  = "cci"
TRAIN_RATIO = 0.7
STRIDE      = 1
HORIZONS    = list(range(1, 7))

DL_MODELS = {"BlockRNNModel", "NHiTSModel"}

MACRO_COLS = ["cpi", "gdp", "unemployment_rate", "impi", "expi"]
NEWS_COLS  = [
    "การเมือง", "ภัยพิบัติ/โรคระบาด", "มาตรการของรัฐ",
    "ราคาน้ำมันเชื้อเพลิง", "ราคาสินค้าเกษตร", "สังคม/ความมั่นคง",
    "เศรษฐกิจโลก", "เศรษฐกิจไทย"
]

FEATURE_SETS = {
    "cci_only": [],
    "macro": MACRO_COLS,
    "news": NEWS_COLS,
    "macro_plus_news": MACRO_COLS + NEWS_COLS,
}

PARAM_GRIDS = {
    "ARIMAX": {
        "p": list(range(1, 7)),
        "d": [1],
        "q": list(range(1, 7)),
    },
    "XGBModel": {
        "lags": list(range(1, 7)),
        "lags_past_covariates": list(range(1, 7)),
    },
    "BlockRNNModel": {
        "model": ["LSTM", "GRU"],
        "input_chunk_length": list(range(1, 13)),
        "hidden_dim": [16, 32],
        "n_rnn_layers": [1],
        "n_epochs": [30, 50],
        "dropout": [0.1],
        "use_reversible_instance_norm": [True],
        "pl_trainer_kwargs": [{"enable_progress_bar": False, "enable_model_summary": False, "accelerator": "gpu", "devices": [0]}],
        "random_state": [42],
    },
    "NHiTSModel": {
        "input_chunk_length": list(range(1, 13)),
        "layer_widths": [64, 128],
        "n_epochs": [30, 50],
        "dropout": [0.1],
        "use_reversible_instance_norm": [True],
        "pl_trainer_kwargs": [{"enable_progress_bar": False, "enable_model_summary": False, "accelerator": "gpu", "devices": [0]}],
        "random_state": [42],
    },
}

DARTS_MODEL_CLASSES = {
    "XGBModel": XGBModel,
    "BlockRNNModel": BlockRNNModel,
    "NHiTSModel": NHiTSModel,
}

SKIP_KEYS = {"pl_trainer_kwargs", "n_jobs", "random_state"}


def get_param_grid(model_name: str, has_covariates: bool) -> dict:
    grid = dict(PARAM_GRIDS[model_name])
    if model_name == "XGBModel" and not has_covariates:
        grid.pop("lags_past_covariates", None)
    return grid


# ==========================================
# DATA
# ==========================================

def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_CSV)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    df = df.sort_values(DATE_COL).reset_index(drop=True)

    for col in df.columns:
        if col != DATE_COL:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    all_cols = [DATE_COL, TARGET_COL] + MACRO_COLS + NEWS_COLS
    use_cols = [c for c in all_cols if c in df.columns]
    df = df[use_cols].dropna().reset_index(drop=True)

    news_in_df = [c for c in NEWS_COLS if c in df.columns]
    if news_in_df:
        has_news = (df[news_in_df] != 0).any(axis=1)
        df = df[has_news].reset_index(drop=True)

    print(f"Data after filtering: {len(df)} rows | {df[DATE_COL].min().date()} -> {df[DATE_COL].max().date()}")
    return df


def make_series(df: pd.DataFrame, feature_cols: list) -> tuple:
    target = TimeSeries.from_dataframe(
        df, time_col=DATE_COL, value_cols=TARGET_COL, freq="MS"
    )
    past_cov = None
    if feature_cols:
        past_cov = TimeSeries.from_dataframe(
            df, time_col=DATE_COL, value_cols=feature_cols, freq="MS"
        )
    return target, past_cov


def make_numpy(df: pd.DataFrame, feature_cols: list):
    y     = df[TARGET_COL].values.astype(float)
    dates = df[DATE_COL].values
    exog  = df[feature_cols].values.astype(float) if feature_cols else None
    return y, exog, dates


# ==========================================
# EVALUATE — Darts models (last point only)
# ==========================================

def _make_data_transformers(is_dl: bool, has_covariates: bool) -> dict | None:
    if not is_dl:
        return None
    transformers = {"series": DartsScaler()}
    if has_covariates:
        transformers["past_covariates"] = DartsScaler()
    return transformers


def evaluate_darts(model_name, params, target, past_cov, horizon, is_dl=False):
    p = {k: v for k, v in params.items() if k not in SKIP_KEYS}
    p["output_chunk_length"] = horizon

    model     = DARTS_MODEL_CLASSES[model_name](**p)
    split_idx = int(len(target) * TRAIN_RATIO)
    data_transformers = _make_data_transformers(is_dl, past_cov is not None)

    try:
        # Returns a single TimeSeries of last-step predictions (one per window)
        preds_series = model.historical_forecasts(
            series=target,
            past_covariates=past_cov,
            forecast_horizon=horizon,
            stride=STRIDE,
            start=target.time_index[split_idx],
            retrain=True,
            last_points_only=True,              # ← only H-th step per window
            data_transformers=data_transformers,
            verbose=False,
            show_warnings=False,
        )

        hfc_err = model.backtest(
            series=target,
            historical_forecasts=preds_series,
            last_points_only=True,              # ← must match
            metric=[darts_mape, darts_rmse],
            reduction=np.nanmean,
        )

    except Exception as e:
        print(f"    [SKIP] {e}")
        return None

    # preds_series is a single TimeSeries — iterate its time index directly
    actual_slice = target.slice(preds_series.start_time(), preds_series.end_time())
    actual_vals  = actual_slice.univariate_values()
    pred_vals    = preds_series.univariate_values()

    all_rows = []
    for i, timestamp in enumerate(preds_series.time_index):
        if i >= len(actual_vals):
            continue
        all_rows.append({
            "origin_date":    pd.Timestamp(timestamp - horizon * target.freq),  # last known date
            "predicted_date": pd.Timestamp(timestamp),
            "horizon":        horizon,          # always == horizon (last point only)
            "actual":         float(actual_vals[i]),
            "predicted":      float(pred_vals[i]),
        })

    if not all_rows:
        print(f"    [WARN] pred_df is empty — check timestamp alignment")

    metrics = {
        "mape": round(float(hfc_err[0]), 4),
        "rmse": round(float(hfc_err[1]), 4),
    }
    pred_df = pd.DataFrame(all_rows)
    return metrics, pred_df


# ==========================================
# EVALUATE — ARIMAX (last point only, same logic)
# ==========================================

def evaluate_arimax(params, y, exog, dates, horizon):
    p, d, q = params["p"], params["d"], params["q"]
    n_train = int(len(y) * TRAIN_RATIO)

    window_mapes, window_rmses, all_rows = [], [], []

    for t in range(n_train, len(y) - horizon + 1):
        try:
            fit = SARIMAX(
                y[:t],
                exog=exog[:t] if exog is not None else None,
                order=(p, d, q),
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False)

            fc = fit.forecast(
                steps=horizon,
                exog=exog[t:t + horizon] if exog is not None else None,
            )
        except Exception:
            continue

        # Only score the H-th step (last point), matching Darts last_points_only=True
        idx = t + horizon - 1
        if idx >= len(y):
            continue

        actual  = float(y[idx])
        pred    = float(fc[horizon - 1])

        all_rows.append({
            "origin_date":    pd.to_datetime(dates[t - 1]),
            "predicted_date": pd.to_datetime(dates[idx]),
            "horizon":        horizon,
            "actual":         actual,
            "predicted":      pred,
        })

        window_mapes.append(abs((actual - pred) / actual) * 100)
        window_rmses.append((actual - pred) ** 2)

    if not window_mapes:
        return None, None

    metrics = {
        "mape": round(float(np.nanmean(window_mapes)), 4),
        "rmse": round(float(np.sqrt(np.nanmean(window_rmses))), 4),  # ← proper RMSE
    }
    pred_df = pd.DataFrame(all_rows)
    return metrics, pred_df


# ==========================================
# GRIDSEARCH
# ==========================================

def run_gridsearch(df):
    output_rows = []

    for feature_set_name, feature_cols in tqdm(FEATURE_SETS.items(), desc="Feature sets"):
        feature_cols   = [c for c in feature_cols if c in df.columns]
        has_covariates = len(feature_cols) > 0

        for horizon in tqdm(HORIZONS, desc=f"{feature_set_name} horizons", leave=False):
            for model_name in tqdm(PARAM_GRIDS.keys(), desc=f"h{horizon} models", leave=False):
                print(f"\n=== h{horizon} | {model_name} | {feature_set_name} ===")

                param_grid = get_param_grid(model_name, has_covariates)

                best_mape    = float("inf")
                best_metrics = None
                best_params  = None
                best_pred_df = None

                for params in tqdm(list(ParameterGrid(param_grid)), desc="Params", leave=False):
                    params_str = "_".join(f"{k}{v}" for k, v in params.items() if k not in SKIP_KEYS)
                    cache_file = CACHE_DIR / feature_set_name / f"h{horizon}" / model_name / f"{params_str}.json"

                    metrics = None
                    pred_df = None

                    if cache_file.exists():
                        try:
                            metrics = json.loads(cache_file.read_text(encoding="utf-8"))["metrics"]
                        except Exception:
                            print(f"    [CACHE CORRUPT] re-running {cache_file.name}")
                            cache_file.unlink()

                    if metrics is None:
                        if model_name == "ARIMAX":
                            y, exog, dates = make_numpy(df, feature_cols)
                            result = evaluate_arimax(params, y, exog, dates, horizon)
                        else:
                            is_dl  = model_name in DL_MODELS
                            target, past_cov = make_series(df, feature_cols)
                            result = evaluate_darts(model_name, params, target, past_cov, horizon, is_dl)

                        if result is None or result[0] is None:
                            continue

                        metrics, pred_df = result

                        try:
                            cache_file.parent.mkdir(parents=True, exist_ok=True)
                            cache_file.write_text(
                                json.dumps({"metrics": metrics}, ensure_ascii=False), encoding="utf-8"
                            )
                        except Exception as e:
                            print(f"    [CACHE WRITE FAIL] {e}")
                            if cache_file.exists():
                                cache_file.unlink()

                    if metrics["mape"] < best_mape:
                        best_mape    = metrics["mape"]
                        best_metrics = metrics
                        best_params  = {k: v for k, v in params.items() if k not in SKIP_KEYS}

                        if pred_df is not None:
                            best_pred_df = pred_df
                        else:
                            if model_name == "ARIMAX":
                                y, exog, dates = make_numpy(df, feature_cols)
                                _, best_pred_df = evaluate_arimax(params, y, exog, dates, horizon)
                            else:
                                is_dl = model_name in DL_MODELS
                                target, past_cov = make_series(df, feature_cols)
                                rerun = evaluate_darts(model_name, params, target, past_cov, horizon, is_dl)
                                best_pred_df = rerun[1] if rerun is not None else None

                if best_metrics is None:
                    continue

                print(f"Best -> MAPE={best_metrics['mape']:.4f}, RMSE={best_metrics['rmse']:.4f}, params={best_params}")

                out_dir = ARTIFACTS_DIR / feature_set_name / model_name / f"h{horizon}"
                out_dir.mkdir(parents=True, exist_ok=True)

                with open(out_dir / "params.json", "w", encoding="utf-8") as f:
                    json.dump({
                        "model":        model_name,
                        "feature_set":  feature_set_name,
                        "horizon":      horizon,
                        "feature_cols": feature_cols,
                        "best_params":  best_params,
                        "mape":         best_metrics["mape"],
                        "rmse":         best_metrics["rmse"],
                    }, f, ensure_ascii=False, indent=2)

                if best_pred_df is not None:
                    best_pred_df.to_csv(out_dir / "predictions.csv", index=False, encoding="utf-8-sig")

                output_rows.append({
                    "feature_set": feature_set_name,
                    "model":       model_name,
                    "horizon":     horizon,
                    "mape":        best_metrics["mape"],
                    "rmse":        best_metrics["rmse"],
                    "params":      json.dumps(best_params, ensure_ascii=False),
                })

    return output_rows


# ==========================================
# MAIN
# ==========================================

def main():
    for d in (RESULTS_DIR, ARTIFACTS_DIR, CACHE_DIR):
        d.mkdir(parents=True, exist_ok=True)

    df = load_data()
    output_rows = run_gridsearch(df)

    if not output_rows:
        print("No results.")
        return

    results = (
        pd.DataFrame(output_rows)
        .sort_values(["feature_set", "horizon", "model"])
        .reset_index(drop=True)
    )
    results.to_csv(RESULTS_DIR / "results_feature_comparison.csv", index=False, encoding="utf-8-sig")
    print(f"\nSaved -> {RESULTS_DIR / 'results_feature_comparison.csv'}")

    pivot = results.pivot_table(
        index="horizon", columns="feature_set", values="mape", aggfunc="min"
    )
    print("\n--- Best MAPE per feature set & horizon ---")
    print(pivot.to_string())

    shutil.rmtree(CACHE_DIR, ignore_errors=True)
    print("\nCache cleaned up.")


if __name__ == "__main__":
    main()