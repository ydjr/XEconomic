# ============================================================
# pipeline/predict_latest.py
# ------------------------------------------------------------
# PURPOSE (Production Forecast):
# - Train on all available supervised rows (where target exists)
# - Use the latest available feature row to predict the NEXT month
# - Save artifacts for dashboard
#
# OUTPUT
# Saved: artifacts\latest_forecast.json
# Saved: artifacts\latest_explain.json
# Saved: artifacts\latest_features.json
# ============================================================

import os
import json
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

# =====================
# CONFIG
# =====================
INPUT_CSV = "./data/macro_monthly_overlapv2.csv"
ART_DIR = "artifacts"

DATE_COL = "date"
TARGET_COL = "cci_overall"
HORIZON = 1

LAGS_TARGET = [1, 2, 3]
LAGS_OTHER  = [1, 2, 3]

USE_LOG_GDP = True
TOPK_LOCAL = 15

MODEL_PARAMS = dict(
    n_estimators=800,
    learning_rate=0.03,
    max_depth=4,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    random_state=42,
    n_jobs=-1,
    tree_method="hist",
)

# =====================
# HELPERS
# =====================
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def save_json(obj, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print("Saved:", path)

def coerce_numeric(df: pd.DataFrame, date_col: str):
    df = df.copy()
    for c in df.columns:
        if c != date_col:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def make_model():
    return XGBRegressor(**MODEL_PARAMS)

def import_shap():
    try:
        import shap
        return shap
    except ImportError:
        raise ImportError("shap is not installed. Run: pip install shap")


# =====================
# FEATURE BUILD
# =====================
def build_features_and_targets(
    df_raw: pd.DataFrame,
    date_col: str,
    target_col: str,
    horizon: int,
    lags_target,
    lags_other,
    use_log_gdp: bool,
):
    """
    Returns:
      - df_feat: rows with date + lag features (keeps last month even if target is missing)
      - df_train: subset of df_feat where target exists (for training)
      - feature_cols: list of feature column names
    """
    df = df_raw.copy()

    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col).reset_index(drop=True)

    df = coerce_numeric(df, date_col=date_col)

    if use_log_gdp and "gdp" in df.columns:
        # log only if positive
        if (df["gdp"] <= 0).any():
            raise ValueError("gdp has non-positive values; cannot apply log(gdp).")
        df["gdp"] = np.log(df["gdp"])

    base_cols = [c for c in df.columns if c != date_col]

    # Lag features
    for col in base_cols:
        lags = lags_target if col == target_col else lags_other
        for L in lags:
            df[f"{col}_lag{L}"] = df[col].shift(L)

    lag_cols = [c for c in df.columns if "_lag" in c]

    # Target (future CCI) get past val direction
    # df["target"] = df[target_col].shift(-horizon)
    df["target"] = df[target_col].shift(-1) - df[target_col]

    # Keep feature table where lag features exist
    df_feat = df[[date_col] + lag_cols + ["target"]].dropna(subset=lag_cols).reset_index(drop=True)
    feature_cols = lag_cols

    df_train = df_feat.dropna(subset=["target"]).reset_index(drop=True)

    return df_feat, df_train, feature_cols

# =====================
# MAIN
# =====================
def main():
    ensure_dir(ART_DIR)
    shap = import_shap()

    raw = pd.read_csv(INPUT_CSV)

    df_feat, df_train, feature_cols = build_features_and_targets(
        df_raw=raw,
        date_col=DATE_COL,
        target_col=TARGET_COL,
        horizon=HORIZON,
        lags_target=LAGS_TARGET,
        lags_other=LAGS_OTHER,
        use_log_gdp=USE_LOG_GDP,
    )

    if df_train.empty:
        raise ValueError("No training rows available after building features/targets.")

    # Train
    X_train = df_train[feature_cols]
    y_train = df_train["target"]

    model = make_model()
    model.fit(X_train, y_train)

    # Latest feature row (this is the most recent month we can build lags for)
    X_latest = df_feat.iloc[-1:][feature_cols]
    latest_date = pd.to_datetime(df_feat.iloc[-1][DATE_COL])
    # Forecast month = latest_date + horizon months
    forecast_date = latest_date + pd.DateOffset(months=HORIZON)

    # y_pred = round(float(model.predict(X_latest)[0]), 1)
    delta_pred = round(float(model.predict(X_latest)[0]), 1)  # ΔCCI

    # Actual known CCI for latest_date
    raw_sorted = raw.copy()
    raw_sorted[DATE_COL] = pd.to_datetime(raw_sorted[DATE_COL])
    raw_sorted = raw_sorted.sort_values(DATE_COL)
    last_actual_date = raw_sorted[DATE_COL].max()
    last_actual_value = float(raw_sorted.loc[raw_sorted[DATE_COL] == last_actual_date, TARGET_COL].iloc[0])
    
    cci_pred_level = round(last_actual_value + delta_pred, 1)

    forecast_obj = {
        "model": "xgboost",
        "horizon": HORIZON,
        "last_actual_month": last_actual_date.strftime("%Y-%m-%d"),
        "last_actual_value": last_actual_value,
        "feature_month_used": latest_date.strftime("%Y-%m-%d"),
        "forecast_month": forecast_date.strftime("%Y-%m-%d"),
        # "cci_pred": y_pred,
        "delta_pred": delta_pred,
        "cci_pred": cci_pred_level,

    }

    save_json(forecast_obj, os.path.join(ART_DIR, "latest_forecast.json"))

    # -------------------------
    # Local SHAP
    # -------------------------
    explainer = shap.TreeExplainer(model)
    shap_val = explainer.shap_values(X_latest)
    base = explainer.expected_value

    local = pd.DataFrame({
        "feature": feature_cols,
        "value": X_latest.iloc[0].values,
        "shap_value": shap_val[0]
    })
    local["abs_shap"] = np.abs(local["shap_value"])
    local = local.sort_values("abs_shap", ascending=False).reset_index(drop=True)

    top = local.head(TOPK_LOCAL).copy()

    explanations = []
    for _, r in top.iterrows():
        explanations.append({
            "feature": str(r["feature"]),
            "value": float(r["value"]),
            "shap_value": float(r["shap_value"]),
            # "abs_shap": float(r["abs_shap"]),
        })
    
    latest_explain = {
        "model": "xgboost",
        "horizon": HORIZON,
        "feature_month_used": latest_date.strftime("%Y-%m-%d"),
        "forecast_month": forecast_date.strftime("%Y-%m-%d"),
        # "cci_pred": y_pred,
        # "base_value": float(base) if np.isscalar(base) else float(np.array(base).reshape(-1)[0]),
        "delta_pred": delta_pred,
        "cci_pred": cci_pred_level,
        "base_value_delta": float(base) if np.isscalar(base) else float(np.array(base).reshape(-1)[0]),
        "base_value_level": round(last_actual_value + (float(base) if np.isscalar(base) else float(np.array(base).reshape(-1)[0])), 3),        
        "topk": TOPK_LOCAL,
        "explanations": explanations,
    }
    save_json(latest_explain, os.path.join(ART_DIR, "latest_explain.json"))
    
    # Optional debug: store top-level feature values used
    latest_features = {
        "feature_month_used": latest_date.strftime("%Y-%m-%d"),
        "features": {c: float(X_latest.iloc[0][c]) for c in feature_cols},
    }
    save_json(latest_features, os.path.join(ART_DIR, "latest_features.json"))

    print("\n=== Production Forecast ===")
    print("Last actual month :", forecast_obj["last_actual_month"])
    print("Feature month used:", forecast_obj["feature_month_used"])
    print("Forecast month    :", forecast_obj["forecast_month"])
    # print("Predicted CCI     :", forecast_obj["cci_pred"])
    print("CCI direction     :", forecast_obj["delta_pred"])
    print("Predicted CCI     :", forecast_obj["cci_pred"])


if __name__ == "__main__":
    main()
