import os
import json
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Project root = one level above /api
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

ART_DIR = os.path.join(ROOT, "artifacts")
DATA_DIR = os.path.join(ROOT, "data")

CCI_CSV = os.path.join(DATA_DIR, "indicators/cci.csv")

LATEST_FORECAST = os.path.join(ART_DIR, "latest_forecast.json")
LATEST_EXPLAIN = os.path.join(ART_DIR, "latest_explain.json")

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
        "latest_month": "YYYY-MM-DD",
        "latest_value": 51.7,
        "prev_month": "YYYY-MM-DD",
        "prev_value": 52.5,
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
    """
    Returns:
      { data: [ {date: 'YYYY-MM-DD', actual: number|null, pred: number|null, is_anchor: bool}, ... ] }

    Logic:
    - read full actual history from CCI_CSV
    - read latest_forecast.json with forecast_path[]
    - set pred at last_actual_month = last actual value (anchor) with is_anchor=True (visual line connection)
    - append forecast_path points as pred (actual=None) with is_anchor=False
    """
    if not os.path.exists(CCI_CSV):
        return {"data": []}

    df = pd.read_csv(CCI_CSV)

    if "date" not in df.columns or "cci_overall" not in df.columns:
        return {"data": []}

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["cci_overall"] = pd.to_numeric(df["cci_overall"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    # normalize monthly to first day of month
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")

    rows = []
    for _, r in df.iterrows():
        actual_val = r["cci_overall"]
        try:
            actual_val = float(actual_val)
        except Exception:
            actual_val = None
        rows.append({"date": r["date_str"], "actual": actual_val, "pred": None, "is_anchor": False})

    # --- forecast JSON format ---
    fc = read_json(LATEST_FORECAST)

    if fc and isinstance(fc.get("forecast_path"), list):
        last_actual_month = fc.get("last_actual_month")

        # 1) Anchor point (connect line) — pred = actual at last_actual_month
        if last_actual_month:
            feature_dt = pd.to_datetime(last_actual_month).to_period("M").to_timestamp()
            feature_s = feature_dt.strftime("%Y-%m-%d")

            found = False
            for x in rows:
                if x["date"] == feature_s:
                    # only set anchor if actual exists
                    if x["actual"] is not None:
                        x["pred"] = x["actual"]
                        x["is_anchor"] = True
                    found = True
                    break

            # if that month not found in history, add a row (best effort)
            if not found:
                last_val = rows[-1]["actual"] if rows else None
                rows.append({"date": feature_s, "actual": last_val, "pred": last_val, "is_anchor": True})

        # 2) Append forecast path points (real forecasts)
        for p in fc["forecast_path"]:
            try:
                dt = pd.to_datetime(p.get("forecast_month")).to_period("M").to_timestamp()
                dt_s = dt.strftime("%Y-%m-%d")
                y_pred = float(p.get("y_pred"))
            except Exception:
                continue

            rows.append({"date": dt_s, "actual": None, "pred": y_pred, "is_anchor": False})

        # sort by date
        rows = sorted(rows, key=lambda x: x["date"])

    if limit and len(rows) > limit:
        rows = rows[-limit:]

    return {"data": rows}
