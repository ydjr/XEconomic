import os
import sys
import json
from pathlib import Path

import pandas as pd
import numpy as np
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# --- resolve project root & import config ---
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import Dirs, Files

ROOT          = str(Dirs.ROOT)
ART_DIR       = str(Dirs.ARTIFACTS)
REASONING_DIR = str(Dirs.REASONING / "oneshot_results")

# Centralized via config — paths follow the actual on-disk layout
def get_workspace_path(original_path: str) -> str:
    """Read from kaggle_workspace if the file exists, to keep original files untouched."""
    rel_path = os.path.relpath(original_path, ROOT)
    kw_path = os.path.join(ROOT, "kaggle_workspace", rel_path)
    if os.path.exists(kw_path):
        return kw_path
    return original_path

CCI_CSV         = get_workspace_path(str(Files.CCI_CSV))             # public/data/indicators/cci.csv
PRED_LATEST_CSV = get_workspace_path(str(Files.PRED_LATEST_CSV))     # artifacts/pred_latest.csv (script 6 output)
NEWS_CSV        = get_workspace_path(str(Files.ABSA_NEWS_CSV))       # data/2017-2026.csv
SHAP_CSV        = get_workspace_path(str(Files.SHAP_TOP3_CSV))       # artifacts/shap_top3_unique.csv
WORDCLOUD_JSON  = get_workspace_path(str(Files.WORDCLOUD_JSON))      # public/data/wordcloud_words.json


def find_latest_reasoning_json(lang: str = "TH") -> str:
    """Return the statically defined reasoning JSON path from config."""
    path = str(Files.REASONING_JSON_TH) if lang == "TH" else str(Files.REASONING_JSON_EN)
    if os.path.exists(path):
        return path
    
    # Fallback to the old English file if TH doesn't exist but EN does (for legacy data)
    en_path = str(Files.REASONING_JSON_EN)
    if os.path.exists(en_path):
        return en_path
        
    return None

# Resolve at startup
EXPLAIN_JSON = find_latest_reasoning_json("TH")
EN_EXPLAIN_JSON = find_latest_reasoning_json("EN")


app = FastAPI(title="CCI Forecast API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_json_file(path: str):
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/data")
def health_data():
    """Freshness report — latest date present in each key data file.

    Lets the dashboard surface "data as of YYYY-MM" warnings when the
    pipeline hasn't caught up, instead of silently serving stale content.
    """
    def _latest_date(path: str, date_col: str):
        if not os.path.exists(path):
            return None
        try:
            df = pd.read_csv(path)
            if date_col not in df.columns:
                return None
            s = pd.to_datetime(df[date_col], errors="coerce").dropna()
            if s.empty:
                return None
            return s.max().strftime("%Y-%m-%d")
        except Exception:
            return None

    return {
        "cci_latest":          _latest_date(CCI_CSV, "date"),
        "news_latest":         _latest_date(NEWS_CSV, "published_at"),
        "prediction_latest":   _latest_date(PRED_LATEST_CSV, "date"),
        "shap_latest":         _latest_date(SHAP_CSV, "date"),
        "reasoning_file":      os.path.basename(EXPLAIN_JSON) if EXPLAIN_JSON and os.path.exists(EXPLAIN_JSON) else None,
        "files": {
            "cci":         os.path.exists(CCI_CSV),
            "news":        os.path.exists(NEWS_CSV),
            "prediction":  os.path.exists(PRED_LATEST_CSV),
            "shap":        os.path.exists(SHAP_CSV),
            "reasoning":   bool(EXPLAIN_JSON) and os.path.exists(EXPLAIN_JSON),
        },
    }

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
    if not EXPLAIN_JSON or not os.path.exists(EXPLAIN_JSON):
        return {"data": []}
    data = load_json_file(EXPLAIN_JSON)
    if not isinstance(data, list):
        return {"data": []}
    for row in data:
        if "date" in row and row["date"]:
            row["date"] = str(row["date"])[:7]
    data = sorted(data, key=lambda x: x.get("date", ""))
    return {"data": data}


@app.get("/dashboard/explain/all")
def dashboard_explain_all():
    if not os.path.exists(EXPLAIN_JSON):
        return {"data": []}

    data = load_json_file(EXPLAIN_JSON)
    if not isinstance(data, list):
        return {"data": []}

    for row in data:
        if "date" in row and row["date"]:
            row["date"] = str(row["date"])[:7]

    data = sorted(data, key=lambda x: x.get("date", ""))
    return {"data": data}


@app.get("/dashboard/explain/all/en")
def dashboard_explain_all_en():
    if not os.path.exists(EN_EXPLAIN_JSON):
        return {"data": []}

    data = load_json_file(EN_EXPLAIN_JSON)
    if not isinstance(data, list):
        return {"data": []}

    for row in data:
        if "date" in row and row["date"]:
            row["date"] = str(row["date"])[:7]

    data = sorted(data, key=lambda x: x.get("date", ""))
    return {"data": data}


@app.get("/dashboard/explain/by-date")
def dashboard_explain_by_date(date: str = Query(...)):
    """date format: YYYY-MM"""
    if not os.path.exists(EXPLAIN_JSON):
        return {"data": None}
    df = pd.read_csv(EXPLAIN_JSON)
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

        pred_col = "predicted" if "predicted" in df_pred.columns else "cci_pred" if "cci_pred" in df_pred.columns else None
        if "date" in df_pred.columns and pred_col is not None:
            df_pred["date"] = pd.to_datetime(df_pred["date"], errors="coerce")
            df_pred["pred"] = pd.to_numeric(df_pred[pred_col], errors="coerce")
            df_pred["date"] = df_pred["date"].dt.to_period("M").dt.to_timestamp()

            # normalize optional comparison columns from pred_direction.csv
            compare_value_col = None
            for c in ["compare_value", "comparison_value", "prev_value", "previous_value", "base_value"]:
                if c in df_pred.columns:
                    compare_value_col = c
                    break

            compare_basis_col = None
            for c in ["compare_basis", "comparison_basis", "prev_type", "previous_type", "base_type"]:
                if c in df_pred.columns:
                    compare_basis_col = c
                    break

            if compare_value_col is not None:
                df_pred["compare_value"] = pd.to_numeric(df_pred[compare_value_col], errors="coerce")
            else:
                df_pred["compare_value"] = np.nan

            if compare_basis_col is not None:
                df_pred["compare_basis"] = df_pred[compare_basis_col].astype(str).str.strip().str.lower()
            else:
                df_pred["compare_basis"] = None

            # if compare info not provided in csv, infer it:
            # compare against previous month actual if available, otherwise previous month predicted
            pred_lookup = (
                df_pred[["date", "pred"]]
                .dropna(subset=["date"])
                .sort_values("date")
                .copy()
            )

            actual_lookup = (
                df_actual[["date", "actual"]]
                .dropna(subset=["date"])
                .sort_values("date")
                .copy()
            )

            actual_map = dict(zip(actual_lookup["date"], actual_lookup["actual"]))
            pred_map = dict(zip(pred_lookup["date"], pred_lookup["pred"]))

            def infer_compare(row):
                if pd.notna(row.get("compare_value")) and pd.notna(row.get("compare_basis")):
                    basis = str(row["compare_basis"]).strip().lower()
                    if basis in ["pred", "predicted", "forecast"]:
                        basis = "predicted"
                    elif basis in ["actual", "real"]:
                        basis = "actual"
                    else:
                        basis = None
                    return pd.Series([row["compare_value"], basis])

                d = row["date"]
                if pd.isna(d):
                    return pd.Series([np.nan, None])

                prev_month = (pd.Timestamp(d) - pd.DateOffset(months=1)).to_period("M").to_timestamp()

                if prev_month in actual_map and pd.notna(actual_map[prev_month]):
                    return pd.Series([actual_map[prev_month], "actual"])

                if prev_month in pred_map and pd.notna(pred_map[prev_month]):
                    return pd.Series([pred_map[prev_month], "predicted"])

                return pd.Series([np.nan, None])

            df_pred[["compare_value", "compare_basis"]] = df_pred.apply(infer_compare, axis=1)

            keep_cols = ["date", "pred"]
            if "direction" in df_pred.columns:
                keep_cols.append("direction")
            else:
                df_pred["direction"] = None
                keep_cols.append("direction")

            keep_cols += ["compare_value", "compare_basis"]
            df_pred = df_pred[keep_cols]
        else:
            df_pred = pd.DataFrame(columns=["date", "pred", "direction", "compare_value", "compare_basis"])
    else:
        df_pred = pd.DataFrame(columns=["date", "pred", "direction", "compare_value", "compare_basis"])

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

    cols = ["id", "published_at", "headline", "url", "Aspect", "category", "subtype", "sentiment_score", "impact_type", "effect_type"]
    df = pd.read_csv(NEWS_CSV, usecols=lambda x: x in cols)

    # ปรับชื่อคอลัมน์ให้ตรงกับไฟล์คุณ wtf krai tum wa
    # จากรูปไฟล์คุณมี: id, category, subtype, published_at, headline, ... sentiment_score, impact_type, effect_type, aspects
    for c in ["published_at", "headline"]:
        if c not in df.columns:
            return {"data": []}

    df["date"] = pd.to_datetime(df["published_at"], dayfirst=True, errors="coerce")
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


@app.get("/dashboard/wordcloud")
def dashboard_wordcloud(limit: int = Query(120, ge=1, le=500)):
    """Per-word data for the interactive word cloud.

    Each item: word, score, weight (0..1 for font sizing), count,
    positive/negative article split, and sample headlines for the
    hover tooltip. Produced by pipeline/generate_wordcloud.py.
    """
    if not os.path.exists(WORDCLOUD_JSON):
        return {"data": []}
    data = load_json_file(WORDCLOUD_JSON)
    if not isinstance(data, list):
        return {"data": []}
    return {"data": data[:limit]}


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
