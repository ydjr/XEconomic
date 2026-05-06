"""
SHAP Post-Processing: prep.py
Prepare SHAP results for dashboard consumption.
"""
import sys
import pandas as pd
from pathlib import Path

# ─── resolve project root & import config ───
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from config import Dirs, Files

input_file = Files.SHAP_RANK_CSV
output_dir = Dirs.SHAP_RESULT
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / "shap_latest.csv"

# Load the dataframe
df = pd.read_csv(input_file)
df['forecast_month'] = '2025-08'

# 1. Drop features containing 'cci_overall'
df_filtered = df[~df['feature'].str.contains('cci_overall', case=False)].copy()

# 2. Add 'abs_shap' column by taking the absolute value of 'shap_value'
df_filtered['abs_shap'] = df_filtered['shap_value'].abs()

# 3. Sort by importance and keep the same naming/structure
df_final = df_filtered.sort_values('abs_shap', ascending=False).copy()

# Save to CSV
cols_to_keep = ['forecast_month', 'feature', 'shap_importance', 'shap_value', 'abs_shap']
df_final = df_final[cols_to_keep]

df_final.to_csv(output_file, index=False)
print(f"Success! Saved to: {output_file}")