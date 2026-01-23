import os
import json
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Project root = one level above /api
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

ART_DIR = os.path.join(ROOT, "artifacts")
DATA_DIR = os.path.join(ROOT, "data")

CCI_CSV = os.path.join(DATA_DIR, "indicators/cci.csv")  # columns: date, cci_overall

LATEST_FORECAST = os.path.join(ART_DIR, "latest_forecast.json")
LATEST_EXPLAIN = os.path.join(ART_DIR, "latest_explain.json")
LATEST_FEATURES = os.path.join(ART_DIR, "latest_features.json")

app = FastAPI(title="CCI Forecast API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def read_json(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/dashboard/summary")
def dashboard_summary():
    fc = read_json(LATEST_FORECAST)
    return fc or {}

@app.get("/dashboard/explain/latest")
def dashboard_explain_latest():
    ex = read_json(LATEST_EXPLAIN)
    return ex or {}

@app.get("/dashboard/features/latest")
def dashboard_features_latest():
    ft = read_json(LATEST_FEATURES)
    return ft or {}

@app.get("/dashboard/timeseries")
def dashboard_timeseries(limit: int = Query(500, ge=1, le=5000)):
    """
    Returns:
      { data: [ {date: 'YYYY-MM-DD', actual: number|null, pred: number|null}, ... ] }

    Logic:
    - read full actual history from data/cci.csv
    - read latest_forecast.json and append:
        pred at last_actual_month = last_actual_value
        pred at forecast_month = cci_pred (actual=null)
    - shade forecast region in frontend after last actual point
    """
    if not os.path.exists(CCI_CSV):
        return {"data": []}

    df = pd.read_csv(CCI_CSV)

    if "date" not in df.columns or "cci_overall" not in df.columns:
        # Fail-safe: return empty
        return {"data": []}

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    # normalize monthly to first day of month
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")

    rows = []
    for _, r in df.iterrows():
        val = r["cci_overall"]
        try:
            val = float(val)
        except Exception:
            val = None
        rows.append({"date": r["date_str"], "actual": val, "pred": None})

    fc = read_json(LATEST_FORECAST)
    if fc:
        last_m = pd.to_datetime(fc.get("last_actual_month"))
        fc_m = pd.to_datetime(fc.get("forecast_month"))

        last_val = float(fc.get("last_actual_value"))
        pred_val = float(fc.get("cci_pred"))

        last_s = last_m.to_period("M").to_timestamp().strftime("%Y-%m-%d")
        fc_s = fc_m.to_period("M").to_timestamp().strftime("%Y-%m-%d")

        # Put pred at the last actual month (so pred line connects)
        found_last = False
        for x in rows:
            if x["date"] == last_s:
                x["pred"] = last_val
                found_last = True
                break
        if not found_last:
            rows.append({"date": last_s, "actual": last_val, "pred": last_val})

        # Append the forecast point
        rows.append({"date": fc_s, "actual": None, "pred": pred_val})

        rows = sorted(rows, key=lambda x: x["date"])

    if limit and len(rows) > limit:
        rows = rows[-limit:]

    return {"data": rows}
