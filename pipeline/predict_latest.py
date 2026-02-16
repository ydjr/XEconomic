import pandas as pd
from darts import TimeSeries
from darts.models import XGBModel
from darts.explainability.shap_explainer import ShapExplainer

# ======================
# LOAD DATA
# ======================
df = pd.read_csv("data/avg_sent_indi.csv")
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

target = TimeSeries.from_dataframe(df, time_col="date", value_cols="cci_overall", freq="MS")
cov_cols = [c for c in df.columns if c not in ["date", "cci_overall"]]
past_cov = TimeSeries.from_dataframe(df, time_col="date", value_cols=cov_cols, freq="MS")

# ======================
# LOAD MODEL + PREDICT
# ======================
model = XGBModel.load("models/backtest_avg_sent_indi/xgb_weights.pkl")

forecast = model.predict(
    n=1,
    series=target,
    past_covariates=past_cov
)

pred_df = forecast.to_dataframe().reset_index()
pred_df.columns = ["date", "cci_pred"]
print(pred_df)

pred_df.to_csv("artifacts/pred_latest.csv", index=False)
print("Saved artifacts/pred_latest.csv")

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
shap_df = shap_ts.to_dataframe()  # keep this ONE dataframe

# save full shap (with date column)
shap_out = shap_df.copy()
shap_out.insert(0, "date", shap_out.index.to_period("M").astype(str))
shap_out.to_csv("artifacts/shap_h1.csv", index=False)
print("Saved artifacts/shap_h1.csv")

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

rank_df.to_csv("artifacts/shap_predicted_month_rank.csv", index=False)
print("Saved artifacts/shap_predicted_month_rank.csv")
print(rank_df.head(10))
