import json
import sys
from pathlib import Path

import pandas as pd
from darts import TimeSeries
from darts.models import XGBModel

# ─── resolve project root & import config ───
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import Dirs, Files, Pipeline

# ─── load data ───
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

# ─── load best params from backtest ───
with open(Files.XGB_BEST_PARAMS, "r", encoding="utf-8") as f:
    best_params = json.load(f)

# ─── train final model ───
Dirs.BACKTEST_MDL.mkdir(parents=True, exist_ok=True)
model = XGBModel(**best_params)
model.fit(target, past_covariates=past_cov)

model.save(str(Files.XGB_WEIGHTS))
print("Saved trained model ->", Files.XGB_WEIGHTS)
