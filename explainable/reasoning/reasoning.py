# # PATH_EVIDENCE is dy prepare for top3 shap-aspect summary
# LLM receives the predicted value, the trend direction, and the month
# flow: absa > monthly aspect summary > 3M aspect summary according to shap val > do reasoninng n summary frm 3M aspect summary.

import pandas as pd
import ollama
import os

# --- Configuration ---
PATH_PRED = r'D:\ICT\senior_project\code\forecasted_value\pred_direction.csv'
PATH_EVIDENCE = r'D:\ICT\senior_project\code\text_summarization\3m_aspect_summarize\llama3.1-2025\3m_summaries.csv'
OUTPUT_DIR = r'D:\ICT\senior_project\code\reasoning\reasoning\llama-gemma_cci_overall'

START_MONTH = "2025-05"
END_MONTH = "2025-08"
MODEL_NAME = "gemma2:9b"

def run_reasoning_pipeline(start_m, end_m):
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"[SYSTEM] Created directory: {OUTPUT_DIR}")

    # 1. Load Data with encoding safety
    print(f"\n[DEBUG 1] Loading CSV files...")
    try:
        pred_df = pd.read_csv(PATH_PRED, encoding='utf-8-sig')
        evidence_df = pd.read_csv(PATH_EVIDENCE, encoding='utf-8-sig')
    except Exception as e:
        print(f"[ERROR] Failed to read CSVs: {e}")
        return

    # --- Data Cleaning & Normalization ---
    # Convert dates to YYYY-MM strings and strip any hidden spaces
    pred_df['date'] = pd.to_datetime(pred_df['date']).dt.strftime('%Y-%m').str.strip()
    
    # Identify the correct column for month in evidence_df
    ev_col = 'Target_Month' if 'Target_Month' in evidence_df.columns else evidence_df.columns[0]
    evidence_df[ev_col] = pd.to_datetime(evidence_df[ev_col]).dt.strftime('%Y-%m').str.strip()

    # --- DEBUG: Data Availability Report ---
    print("-" * 30)
    print(f"[DEBUG 2] Data Availability Report:")
    print(f" - Prediction File Months: {pred_df['date'].unique().tolist()}")
    print(f" - Evidence File Months:   {evidence_df[ev_col].unique().tolist()}")
    
    # Filter months in range
    target_months = sorted(pred_df[(pred_df['date'] >= start_m) & (pred_df['date'] <= end_m)]['date'].unique().tolist())
    print(f" - Target Months to process: {target_months}")
    print("-" * 30)
    
    all_results = []

    for month in target_months:
        print(f"\n[PROCESS] Month: {month}")
        
        # Get Prediction Info
        month_rows = pred_df[pred_df['date'] == month]
        if month_rows.empty:
            print(f"  [!] No prediction data for {month}. Skipping.")
            continue
        
        month_row = month_rows.iloc[0]
        predicted = month_row['predicted']
        direction = month_row['direction']
        
        # Get Evidence and sort by absolute SHAP
        month_evidence = evidence_df[evidence_df[ev_col] == month].copy()
        if month_evidence.empty:
            print(f"  [!] No evidence found in CSV for {month}. Skipping...")
            continue
            
        month_evidence['abs_shap'] = month_evidence['SHAP_Value'].abs()
        month_evidence = month_evidence.sort_values(by='abs_shap', ascending=False)
        
        evidence_lines = [f"- {row['Evidence_Aspect']}: {row['Summary_3M_Evidence']}" for _, row in month_evidence.iterrows()]
        evidence_text = "\n".join(evidence_lines)

        # # 2. Construct Prompt
        # prompt = f"""คุณเป็นนักเศรษฐศาสตร์ที่เขียนรายงานวิเคราะห์ดัชนีความเชื่อมั่นผู้บริโภค (CCI) เป็นภาษาไทย

        # ข้อมูลดัชนี:
        # - เดือน: {month}
        # - ค่า CCI ที่คาดการณ์: {predicted:.2f}
        # - ทิศทาง: {direction}

        # หลักฐานจากข่าว (เรียงตามลำดับความสำคัญจากค่า SHAP):
        # {evidence_text}

        # คำสั่งการเขียน:
        # 1. เขียนเป็น 1 ย่อหน้ายาว (Single Paragraph) โดยใช้ภาษาทางการ
        # 2. **ประโยคเริ่มต้น:** ต้องขึ้นต้นว่า "ดัชนีความเชื่อมั่นผู้บริโภคในเดือน {month} อยู่ที่ {predicted:.2f} โดย{direction}..."
        # 3. **การวิเคราะห์ปัจจัย:** - เริ่มด้วยปัจจัยที่ 1 (ที่มีค่า SHAP สูงสุด) พร้อมรายละเอียดจากหลักฐาน ตามด้วยปัจจัยที่ 2 และปัจจัยที่ 3 โดยใช้คำเชื่อมที่สละสลวย (เช่น นอกจากนี้, ในขณะที่, อีกประการหนึ่งคือ)
        # 4. **การสรุปปิดท้าย (ต้องขึ้นบรรทัดใหม่):** ให้ปิดท้ายย่อหน้าด้วยการสรุปภาพรวม (Summarization) ของปัจจัยทั้งหมดที่กล่าวมา  
        # ให้ขึ้นต้นส่วนสรุปด้วยวลีทางการ เช่น **"โดยรวมแล้วเมื่อพิจารณาสถิติประกอบกับปัจจัยข้างต้น..."** หรือ **"สรุปในภาพรวมจากการวิเคราะห์ความสัมพันธ์ระหว่างแนวโน้มเดิมและปัจจัยอื่น..."** 
        # เพื่อชี้ให้เห็นว่าปัจจัยเหล่านี้ส่งผลรวมต่อความเชื่อมั่นของผู้บริโภคอย่างไรให้ดูน่าเชื่อถือ         
        # 5. **ข้อห้าม:** ห้ามใช้ Bullet points, ห้ามกล่าวถึงชื่อโมเดล/เทคนิค, และห้ามนำข้อมูลภายนอกที่ไม่มีในหลักฐานมาเขียน

        # เขียนเป็นภาษาไทย (1 ย่อหน้าเดียว):
        # """

        
        # # add cci overall info into prompt
        # cci_overall_2025_08 = {
        #     "cci_lag_1": -3.16,
        #     "cci_lag_2": -0.41,
        #     "cci_lag_3": -0.38
        # }
        # print(f"Primary Lag Impact: {cci_overall_2025_08['cci_lag_1']}")

        # # 2. Construct Prompt (change only summarization part)
        # prompt = f"""คุณเป็นนักเศรษฐศาสตร์ที่เขียนรายงานวิเคราะห์ดัชนีความเชื่อมั่นผู้บริโภค (CCI) เป็นภาษาไทย

        # ข้อมูลดัชนี:
        # - เดือน: {month}
        # - ค่า CCI ที่คาดการณ์: {predicted:.2f}
        # - ทิศทาง: {direction}
        # - ข้อมูลดัชนีทางสถิติ (Lagged CCI Influence): {cci_overall_2025_08}

        # หลักฐานจากข่าว (เรียงตามลำดับความสำคัญจากค่า SHAP):
        # {evidence_text}

        # คำสั่งการเขียน:
        # 1. เขียนเป็น 1 ย่อหน้ายาว (Single Paragraph) โดยใช้ภาษาทางการ
        # 2. **ประโยคเริ่มต้น:** ต้องขึ้นต้นว่า "ดัชนีความเชื่อมั่นผู้บริโภคในเดือน {month} อยู่ที่ {predicted:.2f} โดย{direction}..."
        # 3. **การวิเคราะห์ปัจจัย:** - เริ่มด้วยปัจจัยที่ 1 (ที่มีค่า SHAP สูงสุด) พร้อมรายละเอียดจากหลักฐาน
        # - ตามด้วยปัจจัยที่ 2 และปัจจัยที่ 3 โดยใช้คำเชื่อมที่สละสลวย
        # 4. **การสรุปปิดท้าย (ต้องขึ้นบรรทัดใหม่):** ให้ปิดท้ายย่อหน้าด้วยการสรุปภาพรวม (Summarization), ให้ขึ้นต้นส่วนสรุปด้วยวลีทางการ เช่น **"โดยรวมแล้วเมื่อพิจารณาสถิติประกอบกับปัจจัยข้างต้น..."** หรือ **"สรุปในภาพรวมจากการวิเคราะห์ความสัมพันธ์ระหว่างแนวโน้มเดิมและปัจจัยอื่น..."**
        # โดยต้องวิเคราะห์ว่า "แนวโน้มทางสถิติจากเดือนก่อนหน้า {cci_overall_2025_08} และ "ปัจจัยทั้งหมดที่กล่าวมา" ส่งผลร่วมกันอย่างไร 
        # 5. **ข้อห้าม:** ห้ามใช้ Bullet points, ห้ามกล่าวถึงชื่อโมเดล/เทคนิค, และห้ามนำข้อมูลภายนอกที่ไม่มีในหลักฐานมาเขียน

        # เขียนเป็นภาษาไทย (1 ย่อหน้าเดียว):
        # """

        # 3. Call Ollama
        print(f"  [LLM] Requesting {MODEL_NAME}...")
        try:
            response = ollama.chat(
                model=MODEL_NAME,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.2}
            )
            reasoning_text = response['message']['content'].strip()
            
            all_results.append({
                "date": month,
                "predicted": predicted,
                "direction": direction,
                "reasoning": reasoning_text
            })
            print(f"  [OK] Successfully generated reasoning for {month}.")
            
        except Exception as e:
            print(f"  [ERROR] Ollama error for {month}: {e}")

    # 4. Save to CSV
    if all_results:
        output_file = os.path.join(OUTPUT_DIR, f"reasoning_{start_m}_to_{end_m}.csv")
        output_df = pd.DataFrame(all_results)
        output_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n[SUCCESS] Saved {len(all_results)} results to: {output_file}")
    else:
        print("\n[!] Job finished: No results were generated. Check the 'Data Availability Report' above.")

# Execute
if __name__ == "__main__":
    run_reasoning_pipeline(START_MONTH, END_MONTH)