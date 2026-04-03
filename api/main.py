import os
import json
import pandas as pd
import numpy as np
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

ART_DIR = os.path.join(ROOT, "artifacts")
DATA_DIR = os.path.join(ROOT, "data")

CCI_CSV = os.path.join(DATA_DIR, "indicators/cci.csv")

# DASHBOARD_CSV = os.path.join(ART_DIR, "cci_dashboard_latest.csv")
PRED_LATEST_CSV = os.path.join(ART_DIR, "pred_direction.csv")
EXPLAIN_CSV = os.path.join(ART_DIR, "reasoning_oneshot.csv") # explain path from cream
NEWS_CSV = os.path.join(DATA_DIR, "gemma27b_2024-2025.csv")

SHAP_CSV = os.path.join(ART_DIR, "shap_top3_unique.csv")

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
        "cci_pred": 52.5,
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
    if not os.path.exists(EXPLAIN_CSV):
        return {}
    df = pd.read_csv(EXPLAIN_CSV)
    df = df.replace({np.nan: None})
    return {"data": df.to_dict(orient="records")}

@app.get("/dashboard/explain/all")
def dashboard_explain_all():
    if not os.path.exists(EXPLAIN_CSV):
        return {"data": []}
    df = pd.read_csv(EXPLAIN_CSV)
    df = df.replace({np.nan: None})
    # normalize date to YYYY-MM
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m")
    df = df.sort_values("date")
    return {"data": df.to_dict(orient="records")}

@app.get("/dashboard/explain/by-date")
def dashboard_explain_by_date(date: str = Query(...)):
    """date format: YYYY-MM"""
    if not os.path.exists(EXPLAIN_CSV):
        return {"data": None}
    df = pd.read_csv(EXPLAIN_CSV)
    df = df.replace({np.nan: None})
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m")
    row = df[df["date"] == date]
    if row.empty:
        return {"data": None}
    return {"data": row.iloc[0].to_dict()}

@app.get("/dashboard/timeseries")
def dashboard_timeseries(limit: int = Query(500, ge=1, le=5000)):

    if not os.path.exists(CCI_CSV):
        return {"data": []}

    # ---- Load actual CCI ----
    df_actual = pd.read_csv(CCI_CSV)

    if "date" not in df_actual.columns or "cci_overall" not in df_actual.columns:
        return {"data": []}

    df_actual["date"] = pd.to_datetime(df_actual["date"], errors="coerce")
    df_actual["actual"] = pd.to_numeric(df_actual["cci_overall"], errors="coerce")

    df_actual = df_actual.dropna(subset=["date", "actual"])
    df_actual["date"] = df_actual["date"].dt.to_period("M").dt.to_timestamp()

    df_actual = df_actual[["date", "actual"]]

    # ---- Load prediction ----
    if os.path.exists(PRED_LATEST_CSV):
        df_pred = pd.read_csv(PRED_LATEST_CSV)

        pred_col = "predicted" if "predicted" in df_pred.columns else "cci_pred"
        if "date" in df_pred.columns and pred_col in df_pred.columns:
            df_pred["date"] = pd.to_datetime(df_pred["date"], errors="coerce")
            df_pred["pred"] = pd.to_numeric(df_pred[pred_col], errors="coerce")
            df_pred["date"] = df_pred["date"].dt.to_period("M").dt.to_timestamp()
            df_pred = df_pred[["date", "pred", "direction"]]
        else:
            df_pred = pd.DataFrame(columns=["date", "pred", "direction"])
    else:
        df_pred = pd.DataFrame(columns=["date", "pred", "direction"])

    # ---- Merge ----
    df = pd.merge(df_actual, df_pred, on="date", how="outer")

    df = df.sort_values("date")

    # apply limit
    if limit and len(df) > limit:
        df = df.tail(limit)

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df = df.replace({np.nan: None})

    rows = df.to_dict(orient="records")

    return {"data": rows}


@app.get("/dashboard/news")
def dashboard_news(limit: int = Query(2000, ge=1, le=20000)):
    if not os.path.exists(NEWS_CSV):
        return {"data": []}

    df = pd.read_csv(NEWS_CSV)

    # ปรับชื่อคอลัมน์ให้ตรงกับไฟล์คุณ wtf krai tum wa
    # จากรูปไฟล์คุณมี: id, category, subtype, published_at, headline, ... sentiment_score, impact_type, effect_type, aspects
    for c in ["published_at", "headline"]:
        if c not in df.columns:
            return {"data": []}

    df["date"] = pd.to_datetime(df["published_at"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.sort_values("date")

    if limit and len(df) > limit:
        df = df.tail(limit)

    def infer_source(url: str):
        u = str(url or "")
        if "thairath.co.th" in u: return "Thairath"
        if "thaipbs.or.th" in u: return "Thai PBS"
        try:
            from urllib.parse import urlparse
            host = urlparse(u).netloc.replace("www.", "")
            return host
        except:
            return ""

    # map ให้เป็น schema ที่ frontend ใช้
    rows = []
    for _, r in df.iterrows():
        date_str = r["date"].strftime("%Y-%m-%d")
        rows.append({
            "id": r.get("id"),
            "date": date_str,
            "title": r.get("headline", "") or "",
            "url": r.get("url", "") or "",
            "aspect": r.get("Aspect") or "Other",
            "tag": r.get("category", "") or "",
            "source": infer_source(r.get("url", "")) or (r.get("subtype", "") or ""),
            "rawSentiment": float(r.get("sentiment_score")) if pd.notna(r.get("sentiment_score")) else 0.0,
            "impactType": r.get("impact_type", "Neutral") or "Neutral",
            "effectType": r.get("effect_type", "") or "",
        })

    return {"data": rows}


@app.get("/dashboard/shap")
def dashboard_shap(limit: int = Query(10, ge=1, le=50)):

    if not os.path.exists(SHAP_CSV):
        return {"data": []}

    df = pd.read_csv(SHAP_CSV)

    # make sure required columns exist
    required_cols = {"feature", "shap_value"}
    if not required_cols.issubset(df.columns):
        return {"data": []}

    df["shap_value"] = pd.to_numeric(df["shap_value"], errors="coerce")
    df = df.dropna(subset=["shap_value"])

    # sort by absolute importance
    df = df.reindex(df["shap_value"].abs().sort_values(ascending=False).index)

    df = df.head(limit)

    rows = [
        {
            "name": row["feature"],
            "value": float(row["shap_value"])
        }
        for _, row in df.iterrows()
    ]

    return {"data": rows}
