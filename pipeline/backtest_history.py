# ============================================================
# pipeline/backtest_history.py
# ------------------------------------------------------------
# PURPOSE
# - Run walk-forward backtest (expanding window)
# - Save prediction history for dashboard visualization
#
# OUTPUT
# - artifacts/history_backtest.csv
#
# FORMAT
# predicting_for, y_true, y_pred
# ============================================================

import os
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor

# ============================================================
# CONFIG
# ============================================================

INPUT_CSV = "./data/macro_monthly_overlapv2.csv"
ART_DIR = "artifacts"

DATE_COL = "date"
TARGET_COL = "cci_overall"

HORIZON = 1
MIN_TRAIN_MONTHS = 12

LAGS = [1, 2, 3]
USE_LOG_GDP = True

# ============================================================
# HELPERS
# ============================================================

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def rmse(y_true, y_pred):
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))

def make_model():
    return XGBRegressor(
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

# ============================================================
# BUILD SUPERVISED DATA
# ============================================================

def build_supervised(df: pd.DataFrame):
    df = df.copy()
    df[DATE_COL] = pd.to_datetime(df[DATE_COL])
    df = df.sort_values(DATE_COL).reset_index(drop=True)

    # numeric coercion
    for c in df.columns:
        if c != DATE_COL:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if USE_LOG_GDP and "gdp" in df.columns:
        df["gdp"] = np.log(df["gdp"])

    base_cols = [c for c in df.columns if c != DATE_COL]

    for col in base_cols:
        for lag in LAGS:
            df[f"{col}_lag{lag}"] = df[col].shift(lag)

    df["target"] = df[TARGET_COL].shift(-HORIZON)

    lag_cols = [c for c in df.columns if "_lag" in c]
    keep_cols = [DATE_COL, "target"] + lag_cols

    df = df[keep_cols].dropna().reset_index(drop=True)
    feature_cols = [c for c in df.columns if c not in [DATE_COL, "target"]]

    return df, feature_cols

# ============================================================
# WALK-FORWARD BACKTEST (EXPANDING)
# ============================================================

def run_backtest(df_sup: pd.DataFrame, feature_cols: list):
    rows = []

    for t in range(MIN_TRAIN_MONTHS, len(df_sup)):
        train = df_sup.iloc[:t]
        test = df_sup.iloc[t:t+1]

        X_train = train[feature_cols]
        y_train = train["target"]

        X_test = test[feature_cols]

        model = make_model()
        model.fit(X_train, y_train)

        y_pred = float(model.predict(X_test)[0])
        y_true = float(test["target"].iloc[0])

        date_t = pd.to_datetime(test[DATE_COL].iloc[0])

        rows.append({
            "predicting_for": (date_t + pd.DateOffset(months=HORIZON)).strftime("%Y-%m-%d"),
            "y_true": y_true,
            "y_pred": y_pred,
        })

    return pd.DataFrame(rows)

# ============================================================
# MAIN
# ============================================================

def main():
    ensure_dir(ART_DIR)

    print("Loading:", INPUT_CSV)
    raw = pd.read_csv(INPUT_CSV)

    df_sup, feature_cols = build_supervised(raw)

    if len(df_sup) <= MIN_TRAIN_MONTHS:
        raise ValueError("Not enough data for backtest.")

    print("Running expanding-window backtest...")
    hist = run_backtest(df_sup, feature_cols)

    out_path = os.path.join(ART_DIR, "history_backtest.csv")
    hist.to_csv(out_path, index=False)

    mae = mean_absolute_error(hist["y_true"], hist["y_pred"])
    rmse_val = rmse(hist["y_true"], hist["y_pred"])

    print("Saved:", out_path)
    print(f"Rows: {len(hist)}")
    print(f"MAE : {mae:.4f}")
    print(f"RMSE: {rmse_val:.4f}")

if __name__ == "__main__":
    main()
