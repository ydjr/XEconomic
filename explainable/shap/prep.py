import pandas as pd

input_file = r'D:\ICT\senior_project\code\shap\shap_predicted_month_rank_new.csv'
output_file = r'D:\ICT\senior_project\code\shap\shap_result\shap2025-08_new.csv'

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
cols_to_keep = ['forecast_month','feature', 'shap_importance', 'shap_value', 'abs_shap']
df_final = df_final[cols_to_keep]

df_final.to_csv(output_file, index=False)
print(f"Success! Saved to: {output_file}")