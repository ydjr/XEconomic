import sys
from pathlib import Path

import pandas as pd
from darts import TimeSeries
from darts.models import XGBModel
from darts.explainability.shap_explainer import ShapExplainer

# ─── resolve project root & import config ───
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import Dirs, Files, Pipeline

# ======================
# LOAD DATA
# ======================
df = pd.read_csv(Files.AVG_SENT_INDI)
df[Pipeline.DATE_COL] = pd.to_datetime(df[Pipeline.DATE_COL])
df = df.sort_values(Pipeline.DATE_COL)

target = TimeSeries.from_dataframe(
    df, time_col=Pipeline.DATE_COL, value_cols=Pipeline.TARGET_COL, freq="MS"
)
cov_cols = [c for c in df.columns if c not in [Pipeline.DATE_COL, Pipeline.TARGET_COL]]
past_cov = TimeSeries.from_dataframe(
    df, time_col=Pipeline.DATE_COL, value_cols=cov_cols, freq="MS"
)

# ======================
# LOAD MODEL + PREDICT
# ======================
model = XGBModel.load(str(Files.XGB_WEIGHTS))

forecast = model.predict(
    n=1,
    series=target,
    past_covariates=past_cov
)

pred_df = forecast.to_dataframe().reset_index()
pred_df.columns = ["date", "cci_pred"]
print(pred_df)

Dirs.ARTIFACTS.mkdir(parents=True, exist_ok=True)
pred_df.to_csv(Files.PRED_LATEST_CSV, index=False)
print("Saved", Files.PRED_LATEST_CSV)

# ======================
# SHAP
# ======================
foreground_series = target[-12:]
foreground_past_cov = past_cov.slice(
    foreground_series.start_time(),
    foreground_series.end_time()
)

explainer = ShapExplainer(model)
explain_results = explainer.explain(
    foreground_series=foreground_series,
    foreground_past_covariates=foreground_past_cov,
    horizons=1
)

shap_ts = explain_results.get_explanation(horizon=1)
shap_df = shap_ts.to_dataframe()

# save full shap (with date column)
shap_out = shap_df.copy()
shap_out.insert(0, "date", shap_out.index.to_period("M").astype(str))
shap_out.to_csv(Files.SHAP_H1_CSV, index=False)
print("Saved", Files.SHAP_H1_CSV)

# ======================
# RANK LATEST
# ======================
last_shap = shap_df.iloc[-1]  # last row of shap values

rank_df = (
    last_shap.abs()
    .sort_values(ascending=False)
    .reset_index()
)
rank_df.columns = ["feature", "shap_importance"]
rank_df["shap_value"] = last_shap[rank_df["feature"]].values

rank_df.to_csv(Files.SHAP_RANK_CSV, index=False)
print("Saved", Files.SHAP_RANK_CSV)
print(rank_df.head(10))
