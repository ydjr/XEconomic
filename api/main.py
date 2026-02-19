import os
import json
import pandas as pd
import numpy as np
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Project root = one level above /api
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

ART_DIR = os.path.join(ROOT, "artifacts")
DATA_DIR = os.path.join(ROOT, "data")

CCI_CSV = os.path.join(DATA_DIR, "indicators/cci.csv")
NEWS_CSV = os.path.join(DATA_DIR, "2_news_cci_r.csv")


LATEST_FORECAST = os.path.join(ART_DIR, "latest_forecast.json")
LATEST_EXPLAIN = os.path.join(ART_DIR, "latest_explain.json")

DASHBOARD_CSV = os.path.join(ART_DIR, "cci_dashboard_latest.csv")

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
    """
    Actual-only summary for the top cards (no forecast involved).

    Returns:
      {
        "last_actual_month": "YYYY-MM-DD",
        "last_actual_value": 51.7,
        "forecast_month": "YYYY-MM-DD",
        "y_pred": 52.5,
        "mom_change": -0.8,
        "trend": "UP" | "DOWN" | "STABLE" | "N/A"
      }
    """
    if not os.path.exists(CCI_CSV):
        return {
            "latest_month": None,
            "latest_value": None,
            "prev_month": None,
            "prev_value": None,
            "mom_change": None,
            "trend": "N/A",
        }
    
    df = pd.read_csv(CCI_CSV)

    if "date" not in df.columns or "cci_overall" not in df.columns:
        return {
            "latest_month": None,
            "latest_value": None,
            "prev_month": None,
            "prev_value": None,
            "mom_change": None,
            "trend": "N/A",
        }

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["cci_overall"] = pd.to_numeric(df["cci_overall"], errors="coerce")

    df = df.dropna(subset=["date", "cci_overall"]).sort_values("date")

    # normalize to first day of month (consistent)
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()

    if len(df) == 0:
        return {
            "latest_month": None,
            "latest_value": None,
            "prev_month": None,
            "prev_value": None,
            "mom_change": None,
            "trend": "N/A",
        }

    latest = df.iloc[-1]
    latest_month = latest["date"].strftime("%Y-%m-%d")
    latest_value = float(latest["cci_overall"])

    prev_month = None
    prev_value = None
    mom_change = None
    trend = "N/A"

    if len(df) >= 2:
        prev = df.iloc[-2]
        prev_month = prev["date"].strftime("%Y-%m-%d")
        prev_value = float(prev["cci_overall"])

        mom_change = round(latest_value - prev_value, 2)

        eps = 0.05  # small threshold to avoid noise
        if mom_change > eps:
            trend = "UP"
        elif mom_change < -eps:
            trend = "DOWN"
        else:
            trend = "STABLE"

    return {
        "latest_month": latest_month,
        "latest_value": latest_value,
        "prev_month": prev_month,
        "prev_value": prev_value,
        "mom_change": mom_change,
        "trend": trend,
    }


@app.get("/dashboard/explain/latest")
def dashboard_explain_latest():
    ex = read_json(LATEST_EXPLAIN)
    return ex or {}


@app.get("/dashboard/timeseries")
def dashboard_timeseries(limit: int = Query(500, ge=1, le=5000)):
    if not os.path.exists(DASHBOARD_CSV):
        return {"data": []}

    df = pd.read_csv(DASHBOARD_CSV)

    required_cols = {"date", "actual", "pred"}
    if not required_cols.issubset(df.columns):
        return {"data": []}

    # Parse date safely
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    # Normalize monthly
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()

    # Ensure numeric columns
    df["actual"] = pd.to_numeric(df["actual"], errors="coerce")
    df["pred"] = pd.to_numeric(df["pred"], errors="coerce")

    # Apply limit
    if limit and len(df) > limit:
        df = df.tail(limit)

    
    # Convert date to string for frontend
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # IMPORTANT: Replace NaN with None (fix JSON error)
    df = df.replace({np.nan: None})

    rows = df[["date", "actual", "pred"]].to_dict(orient="records")

    return {"data": rows}
