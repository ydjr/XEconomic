# =============================================================================
# train.py
#
# Fit XGBoost on full data using params from best_overall.json.
# Writes: models_xgb/final_model.pkl
#
# Usage:
#   python train.py
# =============================================================================

import json
import warnings
import pandas as pd
from pathlib import Path
from darts import TimeSeries
from darts.models import XGBModel
from xgb_backtest import load_data, make_series
warnings.filterwarnings("ignore")

# =============================================================================
# CONFIG
# =============================================================================

MODELS_DIR        = Path("models_l22h3")
BEST_OVERALL_JSON = MODELS_DIR / "macro_plus_news.json"
FINAL_MODEL_PATH  = MODELS_DIR / "final_model.pkl"

DATE_COL   = "date"
TARGET_COL = "cci"


# =============================================================================
# MAIN
# =============================================================================

def main():
    if not BEST_OVERALL_JSON.exists():
        raise FileNotFoundError(f"{BEST_OVERALL_JSON} not found. Run backtest.py first.")

    with open(BEST_OVERALL_JSON, encoding="utf-8") as f:
        info = json.load(f)

    feature_cols = info["feature_cols"]
    params       = dict(info["used_params"])

    df           = load_data()
    target, past_cov = make_series(df, feature_cols)

    print(f"Data     : {len(df)} months")
    print(f"Features : {feature_cols or 'baseline'}")
    print(f"Params   : {params}")

    model = XGBModel(**params)
    model.fit(target, past_covariates=past_cov)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model.save(str(FINAL_MODEL_PATH))
    print(f"Saved {FINAL_MODEL_PATH}")


if __name__ == "__main__":
    main()

    # =============================================================================
# predict.py
#
# Load saved model and predict next N months.
# Run every month when new data arrives — no retraining needed.
#
# Reads:  models_xgb/final_model.pkl + models_xgb/best_overall.json
# Writes: artifacts/pred_latest.csv, shap.csv, shap_rank.csv
#
# Usage:
#   python predict.py
# =============================================================================

import json
import warnings
import pandas as pd
from pathlib import Path
from darts import TimeSeries
from darts.models import XGBModel
from darts.explainability.shap_explainer import ShapExplainer
from xgb_backtest import load_data, make_series


warnings.filterwarnings("ignore")

# =============================================================================
# CONFIG
# =============================================================================

ARTIFACTS_DIR     = Path("artifacts")
MODELS_DIR        = Path("models_l22h3")
BEST_OVERALL_JSON = MODELS_DIR / "macro_plus_news.json"
FINAL_MODEL_PATH  = MODELS_DIR / "final_model.pkl"

DATE_COL         = "date"
TARGET_COL       = "cci"
FORECAST_HORIZON = 3


# =============================================================================
# MAIN
# =============================================================================

def main():
    for path in [BEST_OVERALL_JSON, FINAL_MODEL_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"{path} not found. Run backtest.py then train.py first.")

    with open(BEST_OVERALL_JSON, encoding="utf-8") as f:
        info = json.load(f)

    feature_cols = info["feature_cols"]

    df               = load_data()
    target, past_cov = make_series(df, feature_cols)

    print(f"Data     : {len(df)} months")
    print(f"Features : {feature_cols or 'baseline'}")

    model    = XGBModel.load(str(FINAL_MODEL_PATH))
    forecast = model.predict(n=FORECAST_HORIZON, series=target, past_covariates=past_cov)

    pred_df = forecast.to_dataframe().reset_index()
    pred_df.columns = ["date", "cci_pred"]
    pred_df["horizon"] = range(1, FORECAST_HORIZON + 1)
    pred_df = pred_df[["date", "horizon", "cci_pred"]]

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    pred_df.to_csv(ARTIFACTS_DIR / "pred_2024-2025.csv", mode='a', header=False, index=False)
    print(f"\nPredictions:\n{pred_df.to_string(index=False)}")

    if past_cov is None:
        return

    # ── SHAP ──────────────────────────────────────────────────────────────────
    explainer = ShapExplainer(model)
    horizons  = list(range(1, FORECAST_HORIZON + 1))
    explain   = explainer.explain(
        foreground_series          = target,
        foreground_past_covariates = past_cov,
        horizons                   = horizons,
    )

    rows = []
    for h in horizons:
        row = explain.get_explanation(horizon=h).to_dataframe().iloc[-1].to_dict()
        row["horizon"] = h
        row["forecast_date"] = str(pred_df.loc[pred_df["horizon"] == h, "date"].iloc[0].date())
        rows.append(row)

    shap_df   = pd.DataFrame(rows)
    meta_cols = ["forecast_date", "horizon"]
    feat_cols = [c for c in shap_df.columns if c not in meta_cols]
    shap_df[meta_cols + feat_cols].to_csv(ARTIFACTS_DIR / "shap_2024-2025.csv", mode='a', header=False, index=False)

    shap_rank = (
        shap_df[feat_cols].abs().mean()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"index": "feature", 0: "mean_abs_shap"})
    )
    shap_rank.to_csv(ARTIFACTS_DIR / "shap_rank.csv", index=False)
    print(f"\nTop features:\n{shap_rank.head(10).to_string(index=False)}")


if __name__ == "__main__":
    main()
