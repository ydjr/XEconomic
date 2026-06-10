import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # project root
from config import Files, Dirs

import pandas as pd
from darts import TimeSeries
from darts.models import XGBModel

# load data
df = pd.read_csv(str(Files.AVG_SENT_INDI))
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

target = TimeSeries.from_dataframe(df, time_col="date", value_cols="cci_overall", freq="MS")
cov_cols = [c for c in df.columns if c not in ["date", "cci_overall"]]
past_cov = TimeSeries.from_dataframe(df, time_col="date", value_cols=cov_cols, freq="MS")

# load best params from backtest
with open(str(Files.XGB_BEST_PARAMS), "r", encoding="utf-8") as f:
    best_params = json.load(f)

# train final model
Dirs.BACKTEST_MDL.mkdir(parents=True, exist_ok=True)
model = XGBModel(**best_params)
model.fit(target, past_covariates=past_cov)

model.save(str(Files.XGB_WEIGHTS))
print("Saved trained model.")
