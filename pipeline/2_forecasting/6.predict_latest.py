import warnings
import json
from pathlib import Path

import pandas as pd
import numpy as np

from darts import TimeSeries
from darts.models import XGBModel
from darts.metrics import mape
from darts.explainability import ShapExplainer

import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
# backtest.py lives alongside this script (dir starts with digit, not importable as package)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backtest import make_series
from config import Dirs, Files, Pipeline


warnings.filterwarnings("ignore")


DATA = Files.AVG_SENT_INDI
DATE = "date"
TARGET = "cci"
HORIZON = Pipeline.PREDICT_HORIZON

MACRO_COLS = ["cpi", "gdp", "unemployment_rate", "impi", "expi"]
NEWS_COLS  = [
    "การเมือง", "ภัยพิบัติ/โรคระบาด", "มาตรการของรัฐ",
    "ราคาน้ำมันเชื้อเพลิง", "ราคาสินค้าเกษตร", "สังคม/ความมั่นคง",
    "เศรษฐกิจโลก", "เศรษฐกิจไทย"
]

FEATURE_COLS = MACRO_COLS + NEWS_COLS

PARAMS = {
    "lags": list(range(-1, -13, -1)),
    "lags_past_covariates": list(range(-1, -13, -1)),
    "n_estimators": [100, 200],
    "max_depth": [3, 4],
    "learning_rate": [0.05, 0.1],
    "output_chunk_length": [HORIZON]
}

def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA)
    df[DATE] = pd.to_datetime(df[DATE])
    df = df.sort_values(DATE).reset_index(drop=True)

    for col in df.columns:
        if col != DATE:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    all_cols = [DATE, TARGET] + MACRO_COLS + NEWS_COLS
    use_cols = [c for c in all_cols if c in df.columns]
    df = df[use_cols].dropna().reset_index(drop=True)

    news_in_df = [c for c in NEWS_COLS if c in df.columns]
    if news_in_df:
        has_news = (df[news_in_df] != 0).any(axis=1)
        df = df[has_news].reset_index(drop=True)

    print(f"Data: {len(df)} rows | {df[DATE].min().date()} -> {df[DATE].max().date()}")
    return df

def main():
    df = load_data()
    feature_cols = [c for c in FEATURE_COLS if c in df.columns]
    target, past_cov = make_series(df, feature_cols)

    OUT_PATH = Dirs.ARTIFACTS
    OUT_PATH.mkdir(parents=True, exist_ok=True)

    PARAMS_FILE = Files.XGB_BEST_PARAMS
    PARAMS_FILE.parent.mkdir(parents=True, exist_ok=True)

    data_end = str(df[DATE].max().date())
    best_params = None

    if PARAMS_FILE.exists():
        cache = json.loads(PARAMS_FILE.read_text())
        if cache.get("data_end") == data_end:
            best_params = cache["params"]
            print(f"Loaded cached best params (data_end={data_end}) — skipping gridsearch")
            print(f"Best params: {best_params}")

    if best_params is None:
        print("Running gridsearch...")
        _, best_params, metrics = XGBModel.gridsearch(
            parameters=PARAMS,
            series=target,
            past_covariates=past_cov,
            forecast_horizon=HORIZON,
            stride=1,
            start=0.8,
            last_points_only=True,
            metric=mape,
            verbose=True
        )
        print(f"\nBest params: {best_params}")
        print(f"Best MAPE: {metrics:.4f}")
        PARAMS_FILE.write_text(json.dumps({"params": best_params, "data_end": data_end}, indent=2))
        print(f"Saved best params to {PARAMS_FILE}")

    print("Train on full dataset")
    model = XGBModel(**best_params)
    model.fit(series=target, past_covariates=past_cov)

    pred = model.predict(
        n=HORIZON,
        series=target,
        past_covariates= past_cov
    )

    print(f"\nForecast for {HORIZON} months ahead:")
    pred_vals = pred.to_series().values
    last_known = float(target.last_value())

    prev_vals = [last_known] + list(pred_vals[:-1])
    directions = []
    for cur, prev in zip(pred_vals, prev_vals):
        diff = cur - prev
        if diff > 0.5:
            directions.append("เพิ่มขึ้น")
        elif diff < -0.5:
            directions.append("ลดลง")
        else:
            directions.append("ทรงตัว")

    pred_df = pd.DataFrame({
        "date":      [d.strftime("%Y-%m") for d in pred.time_index],
        "predicted": pred_vals,
        "direction": directions,
    })
    print(pred_df.to_string(index=False))
    pred_df.to_csv(Files.PRED_LATEST_CSV, index=False, encoding="utf-8-sig")
    print(f"saved {Files.PRED_LATEST_CSV}")

    print("\n Shap Explainer")
    explainer = ShapExplainer(
        model=model,
        background_series=target,
        background_past_covariates=past_cov
    )

    explaination = explainer.explain(
        foreground_series=target,
        foreground_past_covariates=past_cov
    )
 
    # Per-predicted-month SHAP in long format (date, feature, SHAP_Value, ABS_SHAP)
    # Use SHAP of the last training point at each horizon → that explains pred month T+h
    shap_long_rows = []
    for h in range(1, HORIZON + 1):
        shap_exp = explaination.get_shap_explanation_object(horizon=h)
        last_shap = shap_exp.values[-1]  # last training point
        pred_month = (target.end_time() + pd.DateOffset(months=h)).strftime("%Y-%m")
        for feat, val in zip(shap_exp.feature_names, last_shap):
            shap_long_rows.append({
                "date":       pred_month,
                "feature":    feat,
                "SHAP_Value": float(val),
                "ABS_SHAP":   abs(float(val)),
            })

    new_shap = pd.DataFrame(shap_long_rows)

    # Append strategy: keep historical months, add/overwrite new predicted months
    if Files.SHAP_RANK_CSV.exists():
        old_shap = pd.read_csv(Files.SHAP_RANK_CSV, encoding="utf-8-sig")
        old_shap["date"] = old_shap["date"].astype(str).str[:7]
        old_only = old_shap[~old_shap["date"].isin(new_shap["date"])]
        shap_rank_df = pd.concat([old_only, new_shap], ignore_index=True)
    else:
        shap_rank_df = new_shap

    shap_rank_df.to_csv(Files.SHAP_RANK_CSV, index=False, encoding="utf-8-sig")
    print(f"\nSaved SHAP rank: {Files.SHAP_RANK_CSV}")
    print(f"  Predicted months: {sorted(new_shap['date'].unique())}")
    top3 = new_shap.sort_values("ABS_SHAP", ascending=False).groupby("date").head(3)[["date", "feature", "ABS_SHAP"]]
    print(top3.to_string(index=False))
 
if __name__ == "__main__":
    main()
