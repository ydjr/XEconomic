## this script w the diff evidence aspect.
# import pandas as pd
# import os
# import requests
# import time # Added for sleep/retry
# from tqdm import tqdm
# from datetime import datetime
# from dateutil.relativedelta import relativedelta

# # ==========================================
# # CONFIGURATION
# # ==========================================
# CONFIG = {
#     "aspect_path": r"D:\ICT\senior_project\code\text_summarization\aspect_summaries\llama3.1\aspect_summaries_2024_2025.csv",
#     "shap_base_dir": r"D:\ICT\senior_project\code\shap\shap_result", 
#     "output_dir": r"D:\ICT\senior_project\code\text_summarization\3m_shap-aspect_summary\llama3.1",
#     "start_month": "2025-01", 
#     "end_month": "2025-08",
#     "top_k": 3,
#     "model_name": "llama3.1:8b",
#     "ollama_url": "http://localhost:11434/api/generate",
# }

# INDICATOR_MAP = ["cpi", "gdp", "import_price", "export_price", "unemployment", "policy_rate"]
# os.makedirs(CONFIG["output_dir"], exist_ok=True)

# # ==========================================
# # FUNCTIONS
# # ==========================================

# def call_ollama_with_retry(prompt, retries=2):
#     """Sends prompt with a retry mechanism for connection errors."""
#     payload = {
#         "model": CONFIG["model_name"], 
#         "prompt": prompt, 
#         "stream": False, 
#         "options": {"temperature": 0.2}
#     }
#     for i in range(retries + 1):
#         try:
#             # Increased timeout to 180s for heavy economic summaries
#             response = requests.post(CONFIG["ollama_url"], json=payload, timeout=180)
#             return response.json().get('response', '').strip()
#         except Exception as e:
#             if i < retries:
#                 time.sleep(2) # Wait 2 seconds before retrying
#                 continue
#             return f"Error after retries: {str(e)}"

# def get_target_aspect(shap_feature):
#     if str(shap_feature).lower() in [i.lower() for i in INDICATOR_MAP]:
#         return "เศรษฐกิจไทย"
#     return shap_feature

# def generate_prompt(feature, shap_value, target_aspect, combined_texts):
#     # Truncate combined_texts to avoid overloading Ollama (roughly ~8000 chars)
#     safe_text = combined_texts[:8000] 
#     return f"""Task: สรุปบทวิเคราะห์เศรษฐกิจ 3 เดือน
# ปัจจัย: {feature} (SHAP Score: {shap_value})
# หมวดหมู่หลักฐาน: {target_aspect}

# เนื้อหาข่าวสาร:
# {safe_text}

# คำสั่ง:
# - สรุปความเชื่อมโยงระหว่างข่าวกับปัจจัย {feature} เป็นภาษาไทยทางการ
# - ความยาว 3-4 ประโยค
# - หากเนื้อหาข่าวน้อยเกินไป ให้สรุปตามข้อมูลที่มีอยู่จริง
# - ข้อห้ามสำคัญ: ห้ามระบุตัวเลข SHAP Score หรือพูดถึงคำว่า "SHAP" ในบทวิเคราะห์โดยเด็ดขาด

# บทวิเคราะห์:"""

# # ==========================================
# # MAIN EXECUTION
# # ==========================================

# def main():
#     df_aspect = pd.read_csv(CONFIG["aspect_path"])
#     df_aspect['Month'] = pd.to_datetime(df_aspect['Month'])
    
#     start_dt = datetime.strptime(f"{CONFIG['start_month']}-01", "%Y-%m-%d")
#     end_dt = datetime.strptime(f"{CONFIG['end_month']}-01", "%Y-%m-%d")
#     target_months = pd.date_range(start=start_dt, end=end_dt, freq='MS')
    
#     results = []

#     for current_month in tqdm(target_months, desc="Overall Progress"):
#         month_str = current_month.strftime('%Y-%m')
#         shap_file_path = os.path.join(CONFIG["shap_base_dir"], f"shap{month_str}.csv")
        
#         if not os.path.exists(shap_file_path):
#             continue
            
#         df_shap = pd.read_csv(shap_file_path)
#         all_features = df_shap.sort_values(by='rank', ascending=True)
        
#         selected_rows = []
#         used_aspects = set()

#         for _, row in all_features.iterrows():
#             target_aspect = get_target_aspect(row['feature'])
#             if target_aspect not in used_aspects:
#                 selected_rows.append(row)
#                 used_aspects.add(target_aspect)
#             if len(selected_rows) >= CONFIG["top_k"]:
#                 break

#         print(f"\n--- Processing Month: {month_str} ---")

#         for row in selected_rows:
#             feature = row['feature']
#             target_aspect = get_target_aspect(feature)
#             print(f"  > Feature: {feature} | Aspect: {target_aspect}")
            
#             start_window = current_month - relativedelta(months=2)
#             mask = (df_aspect['Month'] >= start_window) & (df_aspect['Month'] <= current_month) & (df_aspect['Aspect'] == target_aspect)
#             window_data = df_aspect.loc[mask].sort_values('Month')

#             if len(window_data) == 0:
#                 summary_3m = "No news data found."
#             else:
#                 combined_texts = "\n\n".join(window_data['Aspect_Summary_TH'].fillna('').tolist())
#                 prompt = generate_prompt(feature, row['shap_value'], target_aspect, combined_texts)
#                 summary_3m = call_ollama_with_retry(prompt)
                
#             print(f"    [OK] Preview: {summary_3m[:50]}...")

#             results.append({
#                 "Target_Month": month_str,
#                 "SHAP_Feature": feature,
#                 "Evidence_Aspect": target_aspect,
#                 "SHAP_Value": row['shap_value'],
#                 "Summary_3M_Evidence": summary_3m
#             })

#     if results:
#         final_df = pd.DataFrame(results)
#         out_path = os.path.join(CONFIG["output_dir"], f"3m_summary_{CONFIG['start_month']}_to_{CONFIG['end_month']}.csv")
#         final_df.to_csv(out_path, index=False, encoding='utf-8-sig')
#         print(f"\nFinal CSV Saved: {out_path}")

# if __name__ == "__main__":
#     main()


# this pick top3 wo considreation of same evidence aspect. == can be same evidence aspect
import pandas as pd
import os
import requests
import time
from tqdm import tqdm
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # project root
from config import cfg, call_hf_api, Files, Dirs, HF_LLM, Pipeline

# ==========================================
# CONFIGURATION
# ==========================================
CONFIG = {
    "aspect_path": str(Dirs.EXPLAINABLE / "text_summarization" / "aspect_summaries.csv"),
    "shap_base_dir": str(Dirs.SHAP_RESULT),
    "output_dir": str(Dirs.ARTIFACTS / "3m_summary_output"),
    "start_month": Pipeline.START_MONTH,
    "end_month": Pipeline.END_MONTH,
    "top_k": Pipeline.SHAP_TOP_K,
    "model_name": HF_LLM.SUMMARY_MODEL,
}

# Mapping keywords for the new lagged feature names
INDICATOR_MAP = ["cpi", "gdp", "import", "export", "unemployment", "policy", "เศรษฐกิจไทย"]
os.makedirs(CONFIG["output_dir"], exist_ok=True)
INDICATOR_DEFINITIONS = {
    "cpi": "ดัชนีราคาผู้บริโภค (เงินเฟ้อ) ซึ่งสะท้อนถึงค่าครองชีพและราคาสินค้าทั่วไป",
    "gdp": "ผลิตภัณฑ์มวลรวมในประเทศ (GDP) ซึ่งสะท้อนถึงการเติบโตหรือการหดตัวทางเศรษฐกิจ",
    "policy": "อัตราดอกเบี้ยนโยบาย ซึ่งส่งผลต่อต้นทุนการกู้ยืมและการใช้จ่ายของภาคประชาชน",
    "unemployment": "อัตราการว่างงานและสภาวะตลาดแรงงาน",
    "import": "สถานการณ์การนำเข้าสินค้าและต้นทุนการผลิตจากต่างประเทศ",
    "export": "สถานการณ์การส่งออกสินค้าและความต้องการจากตลาดโลก",
    "เศรษฐกิจไทย": "ภาพรวมภาวะเศรษฐกิจภายในประเทศไทย"
}
# ==========================================
# FUNCTIONS
# ==========================================

def call_llm_with_retry(prompt, retries=2):
    """Call HuggingFace Inference API with retry."""
    return call_hf_api(
        prompt,
        model=CONFIG["model_name"],
        max_tokens=600,
        temperature=0.2,
        retries=retries,
    )

def get_target_aspect(shap_feature):
    """Maps features like 'cpi_pastcov_lag-3' to news categories."""
    feature_str = str(shap_feature).lower()
    
    if any(ind in feature_str for ind in INDICATOR_MAP):
        return "เศรษฐกิจไทย"
    
    base_name = feature_str.split('_')[0]
    if "การเมือง" in base_name: return "การเมือง"
    if "เกษตร" in base_name: return "สินค้าเกษตร"
    
    return base_name


def generate_prompt(feature, shap_value, target_aspect, combined_texts):
    
    definition = "ข้อมูลทางเศรษฐกิจทั่วไป" # Default
    for key, desc in INDICATOR_DEFINITIONS.items():
        if key in feature.lower():
            definition = desc
            break

    safe_text = combined_texts[:8000] 
    return f"""Task: สรุปบทวิเคราะห์เศรษฐกิจ 3 เดือน
ปัจจัย: {feature} คำนิยาม: {definition}) (Impact Value: {shap_value}) 
หมวดหมู่หลักฐาน: {target_aspect}

เนื้อหาข่าวสาร:
{safe_text}

คำสั่ง:
- สรุปความเชื่อมโยงระหว่างข่าวกับปัจจัย {feature} ({definition}) ในมุมมองเศรษฐกิจไทย เป็นภาษาไทยทางการ
- ความยาว 3-4 ประโยค เท่านั้น
- หากเนื้อหาข่าวน้อยเกินไป ให้สรุปตามข้อมูลที่มีอยู่จริง
- ข้อห้ามสำคัญ: ห้ามเริ่มต้นประโยคด้วย "เศรษฐกิจไทยในปี..." หรือ "ภาพรวมเศรษฐกิจ..." ให้เข้าประเด็นการเปลี่ยนแปลงของ {feature} ทันที**
- ห้ามระบุตัวเลข SHAP Score หรือพูดถึงคำว่า "SHAP" ในบทวิเคราะห์โดยเด็ดขาด**
บทวิเคราะห์:"""

# ==========================================
# MAIN EXECUTION
# ==========================================

def main():
    df_aspect = pd.read_csv(CONFIG["aspect_path"])
    df_aspect['Month'] = pd.to_datetime(df_aspect['Month'])
    
    start_dt = datetime.strptime(f"{CONFIG['start_month']}-01", "%Y-%m-%d")
    end_dt = datetime.strptime(f"{CONFIG['end_month']}-01", "%Y-%m-%d")
    target_months = pd.date_range(start=start_dt, end=end_dt, freq='MS')
    
    results = []

    for current_month in tqdm(target_months, desc="Overall Progress"):
        month_str = current_month.strftime('%Y-%m')
        shap_file_path = os.path.join(CONFIG["shap_base_dir"], f"shap{month_str}.csv")
        
        if not os.path.exists(shap_file_path):
            continue
            
        df_shap = pd.read_csv(shap_file_path)
        
        # UPDATED: Take top_k strictly by abs_shap, regardless of duplicate aspects
        selected_features = df_shap.sort_values(by='abs_shap', ascending=False).head(CONFIG["top_k"])

        print(f"\n--- Processing Month: {month_str} ---")

        for _, row in selected_features.iterrows():
            feature = row['feature']
            target_aspect = get_target_aspect(feature)
            print(f"  > Feature: {feature} | Aspect: {target_aspect}")
            
            start_window = current_month - relativedelta(months=2)
            mask = (df_aspect['Month'] >= start_window) & (df_aspect['Month'] <= current_month) & (df_aspect['Aspect'] == target_aspect)
            window_data = df_aspect.loc[mask].sort_values('Month')

            if len(window_data) == 0:
                summary_3m = f"ไม่พบข้อมูลข่าวสารที่เกี่ยวข้องกับ {target_aspect} ในช่วง 3 เดือนที่ผ่านมา"
            else:
                combined_texts = "\n\n".join(window_data['Aspect_Summary_TH'].fillna('').tolist())
                prompt = generate_prompt(feature, row['shap_value'], target_aspect, combined_texts)
                summary_3m = call_llm_with_retry(prompt)
                
            print(f"    [OK] Preview: {summary_3m[:50]}...")

            results.append({
                "Target_Month": month_str,
                "SHAP_Feature": feature,
                "Evidence_Aspect": target_aspect,
                "SHAP_Value": row['shap_value'],
                "ABS_SHAP": row['abs_shap'],
                "Summary_3M_Evidence": summary_3m
            })

    if results:
        final_df = pd.DataFrame(results)
        out_path = os.path.join(CONFIG["output_dir"], f"3m_summary_{CONFIG['start_month']}_to_{CONFIG['end_month']}.csv")
        final_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        print(f"\nFinal CSV Saved: {out_path}")

if __name__ == "__main__":
    main()