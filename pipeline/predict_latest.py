import warnings
from pathlib import Path

import pandas as pd
import numpy as np

from darts import TimeSeries
from darts.models import XGBModel
from darts.metrics import mape
from darts.explainability import ShapExplainer

from backtest import make_series

warnings.filterwarnings("ignore")


DATA = Path('data/2017-2025.csv')
DATE = "date"
TARGET = "cci"
HORIZON = 3

MACRO_COLS = ["cpi", "gdp", "unemployment_rate", "impi", "expi"]
NEWS_COLS  = [
    "การเมือง", "ภัยพิบัติ/โรคระบาด", "มาตรการของรัฐ",
    "ราคาน้ำมันเชื้อเพลิง", "ราคาสินค้าเกษตร", "สังคม/ความมั่นคง",
    "เศรษฐกิจโลก", "เศรษฐกิจไทย"
]

FEATURE_COLS = MACRO_COLS + NEWS_COLS

PARAMS = {
    "lags": list(range(1, 13)),
    "lags_past_covariates": list(range(1, 13)),
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

    OUT_PATH = Path("predict_outputs_h3")
    OUT_PATH.mkdir(exist_ok=True)

    best_model, best_params, metrics = XGBModel.gridsearch(
        parameters=PARAMS,
        series=target,
        past_covariates=past_cov,
        forecast_horizon=HORIZON,
        stride=1,
        start=0.7,
        last_points_only=True,
        metric=mape,
        verbose=True
    )

    print(f"\nBest params: {best_params}")
    print(f"Best MAPE: {metrics:.4f}")

    print("Train on full dataset")
    model = XGBModel(**best_params)
    model.fit(series=target, past_covariates=past_cov)

    pred = model.predict(
        n=HORIZON,
        series=target,
        past_covariates= past_cov
    )

    print(f"\nForecast for {HORIZON} months ahead:")
    pred_df = pd.DataFrame({
        "date": pred.time_index,
        "horizon": HORIZON,
        "cci_pred": pred.to_series().values,
    })

    print(pred_df.to_string(index=False))
    pred_df.to_csv(OUT_PATH / "pred_latest.csv", index=False, encoding="utf-8-sig")
    print("saved pred_latest.csv")

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
 
    all_importance = []
    for h in range(1, HORIZON + 1):
        shap_exp = explaination.get_shap_explanation_object(horizon=h)
        shap_df = pd.DataFrame(
            shap_exp.values,
            columns=shap_exp.feature_names
        )
        imp = shap_df.abs().mean().reset_index()
        imp.columns = ["feature", "mean_abs_shap"]
        imp["horizon"] = h
        all_importance.append(imp)

    importance = pd.concat(all_importance, ignore_index=True)
    importance = importance.sort_values(["horizon", "mean_abs_shap"], ascending=[True, False])
    importance.to_csv(OUT_PATH / "shap_importance.csv", index=False, encoding="utf-8-sig")

    print("\nTop features by SHAP importance (per horizon):")
    print(importance.head(10).to_string(index=False))
    print("Saved shap_importance.csv")

    all_rows = []
    for h in range(1, HORIZON + 1):
        shap_exp = explaination.get_shap_explanation_object(horizon=h)
        shap_df = pd.DataFrame(
            shap_exp.values,
            columns=shap_exp.feature_names
        )
        shap_df["horizon"] = h
        all_rows.append(shap_df)

    shap_all = pd.concat(all_rows, ignore_index=True)
    shap_all.to_csv(OUT_PATH / "shap_values.csv", index=False, encoding="utf-8-sig")
    print("Saved shap_values.csv")
 
if __name__ == "__main__":
    main()