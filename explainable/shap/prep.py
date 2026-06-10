"""
SHAP Post-Processing: prep.py
Reads the raw SHAP rank CSV from predict_latest,
filters out cci_overall features, adds abs_shap,
and writes a clean shap_latest.csv for the explainable pipeline.
"""
import pandas as pd
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import Dirs, Files

# Input: raw SHAP output from predict_latest (Step 8)
INPUT_FILE = Files.SHAP_RANK_CSV

# Output: cleaned SHAP for explainable pipeline
OUTPUT_DIR = Dirs.SHAP_RESULT
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "shap_latest.csv"

def main():
    if not INPUT_FILE.exists():
        print(f"Error: Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    print(f"Loaded {len(df)} rows from {INPUT_FILE.name}")

    # Standardize date column to YYYY-MM
    if "date" in df.columns:
        df["date"] = df["date"].astype(str).str.strip().str[:7]

    # 1. Drop features containing 'cci_overall' (target leakage)
    if "feature" in df.columns:
        before = len(df)
        df = df[~df["feature"].str.contains("cci_overall", case=False)].copy()
        print(f"Filtered cci_overall features: {before} -> {len(df)} rows")

    # 2. Add/recalculate 'ABS_SHAP' column
    if "SHAP_Value" in df.columns:
        df["ABS_SHAP"] = df["SHAP_Value"].abs()
    elif "shap_value" in df.columns:
        df["ABS_SHAP"] = df["shap_value"].abs()

    # 3. Sort by importance
    if "ABS_SHAP" in df.columns:
        df = df.sort_values("ABS_SHAP", ascending=False)

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"Success! Saved {len(df)} rows to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()