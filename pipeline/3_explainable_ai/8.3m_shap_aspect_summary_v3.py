import re
import time
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from datetime import datetime
from collections import Counter
from dateutil.relativedelta import relativedelta

import sys
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import Dirs, Files, call_hf_api

# ==========================================
# CONFIG
# ==========================================
MONTHLY_SUMMARY_PATH = Files.MONTHLY_SUMMARY_CSV
SHAP_PATH            = Dirs.SHAP_RESULT / "shap_latest.csv"
PRED_PATH            = Files.PRED_LATEST_CSV

TOP_K = 3
OUTPUT_CSV = Files.SUMMARY_3M_CSV
OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

MAX_RETRIES       = 2
RETRY_SLEEP       = 6
MAX_OUTPUT_TOKENS = 400

# Fixed fallback outputs when evidence does not align with indicator definition
NO_ALIGN_POS = "ไม่มีข้อมูลสัญญาณบวกที่สอดคล้องกับตัวชี้วัดนี้"
NO_ALIGN_NEG = "ไม่มีข้อมูลสัญญาณลบที่สอดคล้องกับตัวชี้วัดนี้"

VALID_ASPECTS = {
    "เศรษฐกิจไทย",
    "มาตรการของรัฐ",
    "สังคม/ความมั่นคง",
    "การเมือง",
    "ราคาสินค้าเกษตร",
    "เศรษฐกิจโลก",
    "ภัยพิบัติ/โรคระบาด",
    "ราคาน้ำมันเชื้อเพลิง",
}

FEATURE_ASPECT_MAP = {
    "cpi":          ["เศรษฐกิจไทย", "ราคาสินค้าเกษตร", "ราคาน้ำมันเชื้อเพลิง"],
    "gdp":          ["เศรษฐกิจไทย"],
    "unemployment": ["สังคม/ความมั่นคง"],
    "import":       ["เศรษฐกิจโลก", "ราคาน้ำมันเชื้อเพลิง"],
    "export":       ["เศรษฐกิจโลก", "ราคาสินค้าเกษตร"],
}
FALLBACK_ASPECTS = ["เศรษฐกิจไทย"]

# ==========================================
# INDICATOR DEFINITIONS
# ==========================================
INDICATOR_DEFINITIONS = {
    "cpi":          "ดัชนีราคาผู้บริโภค (CPI) สะท้อนการเปลี่ยนแปลงของค่าครองชีพโดยรวม ครอบคลุมราคาสินค้าเกษตร ราคาพลังงานและน้ำมันเชื้อเพลิง รวมถึงภาวะเศรษฐกิจที่กระทบกำลังซื้อของผู้บริโภค",
    "gdp":          "ผลิตภัณฑ์มวลรวมในประเทศ (GDP) สะท้อนการเติบโตหรือหดตัวของเศรษฐกิจโดยรวม รายได้ประชาชาติ และความแข็งแกร่งของการจ้างงานในประเทศ",
    "unemployment": "อัตราการว่างงานและสภาวะตลาดแรงงาน สะท้อนความมั่นคงของรายได้ครัวเรือน ความสามารถในการใช้จ่าย และความเชื่อมั่นในอนาคตของแรงงาน",
    "import":       "มูลค่าการนำเข้าสินค้าและต้นทุนจากต่างประเทศ ครอบคลุมราคาพลังงาน วัตถุดิบ และสถานการณ์เศรษฐกิจโลกที่กระทบต้นทุนการผลิตในประเทศ",
    "export":       "มูลค่าการส่งออกและความต้องการจากตลาดโลก ครอบคลุมราคาสินค้าเกษตรส่งออก รายได้เข้าประเทศ และอุปสงค์ต่างประเทศที่กระทบรายได้เกษตรกร",
}
DEFAULT_DEFINITION = "ตัวชี้วัดเศรษฐกิจที่กระทบค่าครองชีพและความเชื่อมั่นของผู้บริโภค"

# ==========================================
# UTILITIES
# ==========================================

def clean_text(s) -> str:
    """Clean whitespace and remove markdown fences / invisible chars."""
    if not isinstance(s, str):
        return ""
    return re.sub(r"\s+", " ", s.replace("```", " ").replace("\u200b", " ")).strip()

def strip_feature_tag(feature: str) -> str:
    """
    Remove trailing lag suffix from SHAP feature name.
    Example:
      cpi_pastcov_lag-3 -> cpi
      import_pastcov_lag_1 -> import
    """
    return re.sub(r"_pastcov_lag[-_]\d+$", "", str(feature), flags=re.IGNORECASE)

def get_aspects(feature: str) -> list:
    """
    Map SHAP feature → monthly summary aspect list.
    If exact aspect exists already, use it directly.
    Otherwise match indicator keywords via FEATURE_ASPECT_MAP.
    """
    base = strip_feature_tag(feature)
    if base in VALID_ASPECTS:
        return [base]

    for k, v in FEATURE_ASPECT_MAP.items():
        if k in base.lower():
            return v

    return FALLBACK_ASPECTS

def get_definition(feature: str) -> str:
    """
    Map SHAP feature → indicator definition to inject into LLM prompt.
    """
    base = strip_feature_tag(feature).lower()
    for k, v in INDICATOR_DEFINITIONS.items():
        if k in base:
            return v
    return DEFAULT_DEFINITION

def get_shap_direction(shap_value: float) -> str:
    """Human-readable SHAP sign interpretation."""
    if shap_value > 0:
        return "ส่งผลบวกต่อ CCI"
    elif shap_value < 0:
        return "ส่งผลลบต่อ CCI"
    else:
        return "ไม่มีผลต่อ CCI"


def call_model(prompt: str) -> str:
    for i in range(MAX_RETRIES + 1):
        try:
            return call_hf_api(prompt, max_tokens=MAX_OUTPUT_TOKENS, temperature=0.1)
        except Exception as e:
            if i < MAX_RETRIES:
                time.sleep(RETRY_SLEEP)
            else:
                return f"[HF_ERROR] {e}"

def normalize_llm_summary(text: str, mode: str = "pos") -> str:
    """
    Normalize LLM output:
      - clean text
      - preserve OLLAMA errors
      - if fallback phrase is present anywhere, collapse to exact fallback phrase
    """
    text = clean_text(text)

    if not text or text.startswith("[HF_ERROR]"):
        return text

    if mode == "pos":
        allowed = [NO_ALIGN_POS]
    else:
        allowed = [NO_ALIGN_NEG]

    for a in allowed:
        if a in text:
            return a

    return text

def pull_window(df_monthly, current_month_dt, aspects: list):
    """
    Pull 3-month evidence window merging across all mapped aspects.

    For each month back in [3,2,1]:
      - collect all rows matching the mapped aspects
      - majority vote Overall_Lean
      - concatenate positive summaries
      - concatenate negative summaries
    """
    window_rows = []
    trend_parts = []

    for months_back in [3, 2, 1]:
        w_dt  = current_month_dt - relativedelta(months=months_back)
        w_str = w_dt.strftime("%Y-%m")

        p_list, n_list, lean_list = [], [], []

        for asp in aspects:
            match = df_monthly[
                (df_monthly["Month"] == w_str) &
                (df_monthly["Aspect"] == asp)
            ]

            if not match.empty:
                r = match.iloc[0]
                lean_list.append(clean_text(r["Overall_Lean"]))
                p = clean_text(r["Positive_Summary"])
                n = clean_text(r["Negative_Summary"])

                if p and p.lower() != "nan":
                    p_list.append(p)
                if n and n.lower() != "nan":
                    n_list.append(n)

        if not lean_list:
            window_rows.append({
                "month": w_str,
                "lean": "ไม่มีข้อมูล",
                "pos": "",
                "neg": "",
            })
            trend_parts.append("ไม่มีข้อมูล")
        else:
            vote = Counter(lean_list).most_common(1)[0][0]
            window_rows.append({
                "month": w_str,
                "lean": vote,
                "pos": " ".join(p_list),
                "neg": " ".join(n_list),
            })
            trend_parts.append(vote)

    return window_rows, trend_parts

# ==========================================
# PROMPT BUILDERS check alignment between evidence and indicator definition
# ==========================================

def build_prompt_pos(aspects, trend_str, window_rows, definition, display_feat):
    aspect_str = " / ".join(aspects)
    month_blocks = []

    for m in window_rows:
        pos = clean_text(m["pos"]) or "-"
        month_blocks.append(
            f"เดือน {m['month']} (แนวโน้ม: {m['lean']}):\n  สัญญาณบวก: {pos}"
        )

    evidence_block = "\n\n".join(month_blocks)

    return f"""คุณเป็นผู้ช่วยวิเคราะห์ข่าวเศรษฐกิจไทย
หน้าที่: สรุปสัญญาณบวกจากหมวด "{aspect_str}" เพื่ออธิบายการเปลี่ยนแปลงของ "{display_feat}"
นิยามของ {display_feat}: {definition}

หลักฐานสัญญาณบวกรายเดือน:
{evidence_block}

กฎสำคัญ (ห้ามฝ่าฝืน):
1. ต้องตรวจสอบก่อนว่าหลักฐานสอดคล้องกับนิยามของ {display_feat} อย่างชัดเจนหรือไม่  
2. หากไม่สอดคล้อง หรือเชื่อมโยงไม่ชัดเจน ให้ตอบเพียง: "{NO_ALIGN_POS}"
3. หากสอดคล้อง ให้เลือกเพียง "1 กลไกหลัก" ที่อธิบายผลกระทบต่อ {display_feat} ได้ชัดเจนที่สุดเท่านั้น  
   - ห้ามกล่าวถึงหลายกลไก  
   - ห้ามรวมหลายประเด็นในย่อหน้าเดียว  
4. ให้เลือกเพียง 1–2 ประเด็นที่สำคัญที่สุด และต้องเชื่อมโยงกับนิยามของ {display_feat} โดยตรงเท่านั้น  
   - หากมีหลายเหตุการณ์ ให้เลือกเฉพาะเหตุการณ์เดียวที่มีผลกระทบชัดเจนที่สุด  
5. ต้องอธิบายเป็น causal chain:
   [เหตุการณ์] → [ผลกระทบทางเศรษฐกิจ] → [ผลต่อ {display_feat}]  
6. ใช้เฉพาะข้อมูลจากหลักฐานที่ให้มาเท่านั้น ห้ามเพิ่มข้อมูลภายนอก  
7. หากเดือนใดไม่มีสัญญาณ ("-") ให้ข้ามเดือนนั้น  
8. เขียนเป็นภาษาไทยทางการ  
   - ย่อหน้าเดียวต่อเนื่อง  
   - ห้ามใช้ bullet points หรือเครื่องหมาย "-"  
9. ห้าม:
   - ขึ้นต้นด้วย "ภาพรวม" "สัญญาณบวก/ลบ" หรือ "ใน 3 เดือนที่ผ่านมา"  
   - ระบุชื่อเดือนหรือช่วงเวลาใดๆ  
10. ต้องสรุปใหม่เท่านั้น  
    - ห้ามคัดลอกข้อความจากรายเดือน  
    - ห้าม list หลายเหตุการณ์ต่อกัน  
11. ความยาว:
    - เป้าหมาย 250–350 ตัวอักษร  
    - ห้ามเกิน 450 ตัวอักษรโดยเด็ดขาด  


บทสรุปสัญญาณบวก:"""

def build_prompt_neg(aspects, trend_str, window_rows, definition, display_feat):
    """
    Build negative-summary prompt.
    display_feat is printed/logged in main so you can inspect its actual value.
    """
    aspect_str = " / ".join(aspects)
    month_blocks = []

    for m in window_rows:
        neg = clean_text(m["neg"]) or "-"
        month_blocks.append(
            f"เดือน {m['month']} (แนวโน้ม: {m['lean']}):\n  สัญญาณลบ: {neg}"
        )

    evidence_block = "\n\n".join(month_blocks)

    return f"""คุณเป็นผู้ช่วยวิเคราะห์ข่าวเศรษฐกิจไทย
หน้าที่: สรุปสัญญาณลบจากหมวด "{aspect_str}" เพื่ออธิบายการเปลี่ยนแปลงของ "{display_feat}"
นิยามของ {display_feat}: {definition}

หลักฐานสัญญาณลบรายเดือน:
{evidence_block}

กฎสำคัญ (ห้ามฝ่าฝืน):

1. ต้องตรวจสอบก่อนว่าหลักฐานสอดคล้องกับนิยามของ {display_feat} อย่างชัดเจนหรือไม่  
2. หากไม่สอดคล้อง หรือเชื่อมโยงไม่ชัดเจน ให้ตอบเพียง: "{NO_ALIGN_NEG}"
3. หากสอดคล้อง ให้เลือกเพียง "1 กลไกหลัก" ที่อธิบายผลกระทบต่อ {display_feat} ได้ชัดเจนที่สุดเท่านั้น  
   - ห้ามกล่าวถึงหลายกลไก  
   - ห้ามรวมหลายประเด็นในย่อหน้าเดียว  
4. ให้เลือกเพียง 1–2 ประเด็นที่สำคัญที่สุด และต้องเชื่อมโยงกับนิยามของ {display_feat} โดยตรงเท่านั้น  
   - หากมีหลายเหตุการณ์ ให้เลือกเฉพาะเหตุการณ์เดียวที่มีผลกระทบชัดเจนที่สุด  
5. ต้องอธิบายเป็น causal chain:
   [เหตุการณ์] → [ผลกระทบทางเศรษฐกิจ] → [ผลต่อ {display_feat}]  
6. ใช้เฉพาะข้อมูลจากหลักฐานที่ให้มาเท่านั้น ห้ามเพิ่มข้อมูลภายนอก  
7. หากเดือนใดไม่มีสัญญาณ ("-") ให้ข้ามเดือนนั้น  
8. เขียนเป็นภาษาไทยทางการ  
   - ย่อหน้าเดียวต่อเนื่อง  
   - ห้ามใช้ bullet points หรือเครื่องหมาย "-"  
9. ห้าม:
   - ขึ้นต้นด้วย "ภาพรวม" "สัญญาณบวก/ลบ" หรือ "ใน 3 เดือนที่ผ่านมา"  
   - ระบุชื่อเดือนหรือช่วงเวลาใดๆ  
10. ต้องสรุปใหม่เท่านั้น  
    - ห้ามคัดลอกข้อความจากรายเดือน  
    - ห้าม list หลายเหตุการณ์ต่อกัน  
11. ความยาว:
    - เป้าหมาย 250–350 ตัวอักษร  
    - ห้ามเกิน 450 ตัวอักษรโดยเด็ดขาด  

บทสรุปสัญญาณลบ:"""

# ==========================================
# OUTPUT
# ==========================================

def init_output() -> None:
    """Remove existing output file so each run starts fresh."""
    if OUTPUT_CSV.exists():
        OUTPUT_CSV.unlink()
        print(f"  [!] Removed existing output: {OUTPUT_CSV.name}")

def append_row(row: dict) -> None:
    """Append one result row to CSV."""
    df_row = pd.DataFrame([row])

    if OUTPUT_CSV.exists():
        df_row.to_csv(
            OUTPUT_CSV,
            mode="a",
            header=False,
            index=False,
            encoding="utf-8-sig",
        )
    else:
        df_row.to_csv(
            OUTPUT_CSV,
            mode="w",
            header=True,
            index=False,
            encoding="utf-8-sig",
        )

# ==========================================
# MAIN
# ==========================================

def main():
    print("Loading files...")
    df_monthly = pd.read_csv(MONTHLY_SUMMARY_PATH, encoding="utf-8-sig")
    df_shap    = pd.read_csv(SHAP_PATH,            encoding="utf-8-sig")
    df_pred    = pd.read_csv(PRED_PATH,            encoding="utf-8-sig")

    # Standardize month to to YYYY-MM
    df_monthly["Month"] = df_monthly["Month"].astype(str).str.strip().str[:7]
    df_pred["date"]     = df_pred["date"].astype(str).str.strip().str[:7]

    # Find matched shap date col
    shap_date_col = next(
        (c for c in df_shap.columns if c.strip().lower() in {
            "date", "month", "forecast_month", "target_month", "ym"
        }),
        None
    )
    if shap_date_col is None:
        raise ValueError(f"Cannot find date column in SHAP CSV. Columns: {list(df_shap.columns)}")

    df_shap["date"] = df_shap[shap_date_col].astype(str).str.strip().str[:7]

    shap_feat_col = next((c for c in df_shap.columns if "feature" in c.lower()), None)  # find shap feature col
    if shap_feat_col is None:
        raise ValueError("Cannot find feature column in SHAP CSV.")

    for col in ["Positive_Summary", "Negative_Summary", "Overall_Lean", "Aspect"]:
        df_monthly[col] = df_monthly[col].astype(str).apply(clean_text)

    # Build target month range
    target_months_str = sorted(df_shap["date"].unique())
    target_months = [datetime.strptime(f"{m}-01", "%Y-%m-%d") for m in target_months_str]

    init_output()
    print(f"Target months: {len(target_months)} months | Model: 4-bit HF API")

    for i, current_month_dt in enumerate(tqdm(target_months, desc="Months")):
        month_str = current_month_dt.strftime("%Y-%m")

        # Get prediction row for current month
        pred_row = df_pred[df_pred["date"] == month_str]
        if pred_row.empty:
            print(f"  [!] No prediction data for {month_str} — skipping")
            continue

        # Get SHAP rows for current month
        shap_month = df_shap[df_shap["date"] == month_str].copy()
        if shap_month.empty:
            print(f"  [!] No SHAP data for {month_str} — skipping")
            continue

        shap_month["base"] = shap_month[shap_feat_col].apply(strip_feature_tag)
        top_features = (
            shap_month
            .sort_values("ABS_SHAP", ascending=False)
            .drop_duplicates(subset="base", keep="first")
            .head(TOP_K)
        )

        for _, row in tqdm(top_features.iterrows(), total=len(top_features),
                           desc=f"  {month_str}", leave=False):

            feat     = clean_text(str(row[shap_feat_col]))
            shap_val = float(row.get("SHAP_Value", row.get("shap_value", 0)))
            abs_shap = float(row.get("ABS_SHAP", abs(shap_val)))

            d_feat   = strip_feature_tag(feat) # to rm lag suffix
            asps     = get_aspects(feat)
            dfn      = get_definition(feat)
            shap_dir = get_shap_direction(shap_val)
            print(f"    [display_feat] raw_feature={feat} | display_feat={d_feat}")

            # Pull 3-month window
            win, trd  = pull_window(df_monthly, current_month_dt, asps)
            trend_str = " → ".join(trd)

            all_empty = all(w["lean"] == "ไม่มีข้อมูล" for w in win)

            if all_empty:
                pos_summary = f"ไม่พบข้อมูลในช่วง 3 เดือนที่ผ่านมาสำหรับ {d_feat}"
                neg_summary = pos_summary
            else:
                months_with_pos = [w for w in win if w["pos"]]
                months_with_neg = [w for w in win if w["neg"]]

                # -------------------------
                # Positive summary
                # -------------------------
                if len(months_with_pos) == 0:
                    pos_summary = "ไม่พบสัญญาณบวกที่ชัดเจนในช่วงนี้"
                elif len(months_with_pos) == 1:
                    p_prompt = build_prompt_pos(asps, trend_str, win, dfn, d_feat)
                    pos_summary = normalize_llm_summary(call_model(p_prompt), mode="pos")
                else:
                    p_prompt = build_prompt_pos(asps, trend_str, win, dfn, d_feat)
                    print(
                        f"    [LLM pos] feat={d_feat} | aspects={asps} | trend={trend_str} | "
                        f"evidence_months={[w['month'] for w in months_with_pos]} | "
                        f"pos_chars={[len(w['pos']) for w in months_with_pos]}"
                    )
                    pos_summary = normalize_llm_summary(call_model(p_prompt), mode="pos")

                # -------------------------
                # Negative summary
                # -------------------------
                if len(months_with_neg) == 0:
                    neg_summary = "ไม่พบสัญญาณลบที่ชัดเจนในช่วงนี้"
                elif len(months_with_neg) == 1:
                    n_prompt = build_prompt_neg(asps, trend_str, win, dfn, d_feat)
                    neg_summary = normalize_llm_summary(call_model(n_prompt), mode="neg")
                else:
                    n_prompt = build_prompt_neg(asps, trend_str, win, dfn, d_feat)
                    print(
                        f"    [LLM neg] feat={d_feat} | aspects={asps} | trend={trend_str} | "
                        f"evidence_months={[w['month'] for w in months_with_neg]} | "
                        f"neg_chars={[len(w['neg']) for w in months_with_neg]}"
                    )
                    neg_summary = normalize_llm_summary(call_model(n_prompt), mode="neg")

            print(
                f"  [{month_str}] feat={d_feat} | aspects={asps} | SHAP={shap_val:+.4f} ({shap_dir}) | "
                f"trend={trend_str} | pos_len={len(pos_summary)} | neg_len={len(neg_summary)}"
            )

            append_row({
                "Target_Month":        month_str,
                "Predicted_CCI":       round(float(pred_row.iloc[0]["predicted"]), 2),
                "CCI_Direction":       pred_row.iloc[0]["direction"],
                "SHAP_Feature":        feat,
                "SHAP_Value":          round(shap_val, 6),
                "ABS_SHAP":            round(abs_shap, 6),
                "SHAP_Direction":      shap_dir,
                "Evidence_Aspects":    ", ".join(asps),
                "3M_Trend":            trend_str,
                "Summary_3M_Positive": pos_summary,
                "Summary_3M_Negative": neg_summary,
            })
            
        # Auto-commit every month to prevent data loss on Kaggle timeout
        import os
        if os.environ.get("KAGGLE_ENV") == "1":
            print(f"\n[Auto-Save] Saving 3M summary progress for month {month_str} to GitHub...")
            os.system("git config --global user.email 'bot@kaggle.com'")
            os.system("git config --global user.name 'Kaggle Bot'")
            os.system(f"git add {OUTPUT_CSV}")
            os.system("git commit -m 'chore: auto-save 3m summary progress'")
            os.system("git push")

    print(f"\nDone. Output saved to:\n  {OUTPUT_CSV}")

if __name__ == "__main__":
    main()