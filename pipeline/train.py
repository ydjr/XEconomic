import json
import pandas as pd
from darts import TimeSeries
from darts.models import XGBModel

# load data
df = pd.read_csv("data/avg_sent_indi.csv")
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

target = TimeSeries.from_dataframe(df, time_col="date", value_cols="cci_overall", freq="MS")
cov_cols = [c for c in df.columns if c not in ["date", "cci_overall"]]
past_cov = TimeSeries.from_dataframe(df, time_col="date", value_cols=cov_cols, freq="MS")

# load best params from backtest
with open("artifacts/backtest_avg_sent_indi/xgb_best_params.json", "r", encoding="utf-8") as f:
    best_params = json.load(f)

# train final model
model = XGBModel(**best_params)
model.fit(target, past_covariates=past_cov)

model.save("models/backtest_avg_sent_indi/xgb_weights.pkl")
print("Saved trained model.")
