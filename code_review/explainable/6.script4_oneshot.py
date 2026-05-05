
import re
import time
import requests
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

# ==========================================
# CONFIG
# ==========================================

SUMMARY_3M_PATH = Path(r"/home/xecon/sp2025/SP2025-SeniorProject/text_summarization/3m_summary/gemma2_27b/3m_summary_2024-01_to_2025-08.csv")
PRED_PATH       = Path(r"/home/xecon/sp2025/SP2025-SeniorProject/forecasted_value/pred_direction.csv")
OUTPUT_DIR = Path(r"/home/xecon/sp2025/SP2025-SeniorProject/reasoning/reasoning/oneshot_results/gemma4_31b/bulletver")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

START_MONTH = "2024-01"
END_MONTH   = "2025-08"

OUTPUT_CSV  = OUTPUT_DIR / f"reasoning_{START_MONTH}_to_{END_MONTH}.csv"
OUTPUT_JSON = OUTPUT_DIR / f"reasoning_{START_MONTH}_to_{END_MONTH}.json"

# Ollama
OLLAMA_URL        = "http://localhost:11434/api/generate"
MODEL_NAME        = "gemma4:31b"
MAX_RETRIES       = 2
RETRY_SLEEP       = 6
MAX_OUTPUT_TOKENS = 700
OLLAMA_TIMEOUT    = 360

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
DEFAULT_DEFINITION = "ตัวชี้วัดเศรษฐกิจที่ส่งผลต่อกำลังซื้อและความเชื่อมั่นของผู้บริโภค"

# ==========================================
# ECONOMIC RELATIONSHIP HINTS
# ==========================================
FEATURE_CCI_RELATIONSHIP = {
    "cpi":                  "CPI ↑ = เงินเฟ้อสูง = กำลังซื้อลด = CCI มักลดลง | CPI ↓ หรือทรงตัว = เงินเฟ้อนิ่ง = CCI มักเพิ่มขึ้น",
    "gdp":                  "GDP ↑ = เศรษฐกิจขยายตัว = รายได้/การจ้างงาน ↑ = CCI มักเพิ่มขึ้น | GDP ↓ = CCI มักลดลง",
    "unemployment":         "การว่างงาน ↑ = รายได้/ความมั่นคง ↓ = CCI ลดลง | การว่างงาน ↓ = CCI ↑",
    "import":               "ราคานำเข้า ↑ = ต้นทุนการผลิต ↑ = ราคาสินค้า ↑ = กำลังซื้อ ↓ = CCI ลดลง | ราคานำเข้า ↓ = CCI ↑",
    "export":               "ส่งออก ↑ = รายได้ประเทศ ↑ = เศรษฐกิจแข็งแกร่ง = CCI ↑ | ส่งออก ↓ = CCI ↓",
    "ราคาน้ำมันเชื้อเพลิง": "ราคาน้ำมัน ↑ = ต้นทุนครัวเรือน/ธุรกิจ ↑ = CCI ลดลง | ราคาน้ำมัน ↓ = ภาระค่าครองชีพลด = CCI ↑",
    "ราคาสินค้าเกษตร":      "ราคาเกษตร ↑ = รายได้เกษตรกร ↑ = CCI ↑ (ในกลุ่มเกษตร) | ราคาเกษตร ↓ = รายได้เกษตรกรลด = CCI ↓",
    "สังคม/ความมั่นคง":      "ความมั่นคงทางสังคม ↑ = ความเชื่อมั่น ↑ = CCI ↑ | ความไม่สงบ/ปัญหาสังคม = CCI ↓",
    "เศรษฐกิจโลก":           "เศรษฐกิจโลกขยายตัว = การค้า/ส่งออก ↑ = CCI ↑ | เศรษฐกิจโลกชะลอ/สงครามการค้า = CCI ↓",
    "เศรษฐกิจไทย":           "ภาพรวมเศรษฐกิจดี = รายได้/งาน ↑ = CCI ↑ | เศรษฐกิจชะลอ/หนี้สูง = CCI ↓",
    "มาตรการของรัฐ":         "มาตรการกระตุ้น/สวัสดิการ = รายได้/ความมั่นคง ↑ = CCI ↑ | มาตรการรัดเข็มขัด/ภาษีเพิ่ม = CCI ↓",
}
DEFAULT_RELATIONSHIP = "ปัจจัยนี้ส่งผลต่อค่าครองชีพและความมั่นใจในการใช้จ่ายของผู้บริโภค"

# ==========================================
# UTILITIES
# ==========================================

def clean_text(s) -> str:
    if not isinstance(s, str):
        return ""
    s = s.replace("```", " ").replace("\u200b", " ")
    return re.sub(r"\s+", " ", s).strip()

def get_definition(base_feat: str) -> str:
    for keyword, definition in INDICATOR_DEFINITIONS.items():
        if keyword.lower() in base_feat.lower():
            return definition
    return DEFAULT_DEFINITION

def get_relationship(base_feat: str) -> str:
    for keyword, rel in FEATURE_CCI_RELATIONSHIP.items():
        if keyword.lower() in base_feat.lower():
            return rel
    return DEFAULT_RELATIONSHIP

def query_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": MAX_OUTPUT_TOKENS,
            "temperature": 0.2,
            "repeat_penalty": 1.1,
        },
    }
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
            r.raise_for_status()
            return clean_text(r.json().get("response", ""))
        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"  [Retry {attempt+1}] Ollama error: {e} — waiting {RETRY_SLEEP}s")
                time.sleep(RETRY_SLEEP)
            else:
                return f"[OLLAMA_ERROR] {e}"

def init_output() -> None:
    if OUTPUT_CSV.exists():
        OUTPUT_CSV.unlink()
        print(f"  [!] Removed existing output: {OUTPUT_CSV.name}")

def append_row(row: dict) -> None:
    df_row = pd.DataFrame([row])
    if OUTPUT_CSV.exists():
        df_row.to_csv(OUTPUT_CSV, mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        df_row.to_csv(OUTPUT_CSV, mode="w", header=True, index=False, encoding="utf-8-sig")

# ==========================================
# SHOT EXAMPLES
# ==========================================

SHOT_EXAMPLES = """===== ตัวอย่างบทวิเคราะห์ที่ถูกต้อง (อ้างอิงรูปแบบและตรรกะเท่านั้น ห้ามนำเนื้อหาไปใช้) =====
 
[ตัวอย่างที่ 1 — ทิศทางเพิ่มขึ้น]
[FACTOR1]ภาคนโยบายแรงงานที่เอื้อต่อรายได้ครัวเรือน จากการที่คณะรัฐมนตรีอนุมัติกฎหมายจ่ายค่าล่วงเวลาสำหรับพนักงาน รปภ. ในอัตรา 1.25 เท่าในวันธรรมดาและ 2.5 เท่าในวันหยุด ซึ่งช่วยเพิ่มรายได้และความมั่นคงทางการเงินของแรงงานโดยตรง ส่งผลให้ผู้บริโภคมีความเชื่อมั่นในการใช้จ่ายมากขึ้น[/FACTOR1]
[FACTOR2]ราคานำเข้าที่ทรงตัวในช่วงที่ผ่านมา สะท้อนว่าต้นทุนการผลิตของภาคธุรกิจยังไม่เร่งตัว ทำให้ราคาสินค้าและบริการในประเทศไม่ปรับสูงขึ้นจนกดดันกำลังซื้อของผู้บริโภค[/FACTOR2]
[FACTOR3]ดัชนีราคาผู้บริโภคที่ทรงตัวในระดับต่ำ ชี้ให้เห็นว่าแรงกดดันเงินเฟ้อยังอยู่ในระดับที่ควบคุมได้ ทำให้ผู้บริโภคมีความมั่นใจว่ากำลังซื้อจะไม่ถูกกัดกร่อนในระยะใกล้[/FACTOR3]
[CONCLUSION]มาตรการภาครัฐที่เพิ่มรายได้แรงงานโดยตรง ประกอบกับต้นทุนนำเข้าและเงินเฟ้อที่ทรงตัวในระดับที่จัดการได้ ส่งผลให้กำลังซื้อและความเชื่อมั่นผู้บริโภคปรับตัวเพิ่มขึ้น[/CONCLUSION]

[ตัวอย่างที่ 2 — ทิศทางลดลง]
[FACTOR1]การขยายตัวทางเศรษฐกิจที่ต่ำกว่าที่คาดไว้ ทำให้ผู้บริโภคและภาคธุรกิจขาดความมั่นใจในรายได้และการจ้างงานในระยะข้างหน้า ส่งผลให้ความเชื่อมั่นในการใช้จ่ายลดลงต่อเนื่อง[/FACTOR1]
[FACTOR2]ภาระหนี้สินครัวเรือนที่ปรับตัวสูงขึ้นจากต้นทุนการกู้ยืมที่เพิ่มขึ้น ทำให้กำลังซื้อของผู้บริโภคถูกกัดกร่อนและลดทอนความสามารถในการใช้จ่าย ส่งผลให้ความเชื่อมั่นในปัจจุบันอ่อนแอลง[/FACTOR2]
[FACTOR3]ราคาสินค้าเกษตรบางรายการที่ปรับตัวลดลง ส่งผลให้รายได้ของเกษตรกรหดตัวโดยตรง ทำให้กำลังซื้อในกลุ่มครัวเรือนเกษตรอ่อนแอลงและฉุดรั้งความเชื่อมั่นโดยรวม[/FACTOR3]
[CONCLUSION]การเติบโตทางเศรษฐกิจที่ต่ำกว่าคาดทำให้ความมั่นใจด้านรายได้และการจ้างงานลดลง ประกอบกับภาระหนี้ครัวเรือนที่สูงขึ้นและรายได้เกษตรกรที่หดตัว ส่งผลให้กำลังซื้อและความเชื่อมั่นผู้บริโภคปรับตัวลดลง[/CONCLUSION]

[ตัวอย่างที่ 3 — ทิศทางทรงตัว]
[FACTOR1]มาตรการลดภาระค่าครองชีพของภาครัฐที่ดำเนินการต่อเนื่อง อาทิ โครงการคนละครึ่ง พลัส ช่วยเพิ่มกำลังซื้อให้ครัวเรือนโดยตรง ทำให้ผู้บริโภคยังคงมีความสามารถในการใช้จ่ายในระดับหนึ่ง[/FACTOR1]
[FACTOR2]การส่งออกที่ยังคงมีแนวโน้มเชิงบวกและการเข้าสู่ช่วงเทศกาลปลายปีที่ช่วยกระตุ้นการหมุนเวียนของรายได้ในระบบเศรษฐกิจ ส่งผลให้ธุรกิจการค้าและบริการได้รับอานิสงส์และช่วยพยุงความเชื่อมั่นไว้ได้[/FACTOR2]
[FACTOR3]ความไม่แน่นอนทางการเมืองภายในประเทศและปัญหาความขัดแย้งชายแดนที่ทวีความรุนแรง ทำให้ผู้บริโภคระมัดระวังการใช้จ่ายมากขึ้นและถ่วงดุลแรงสนับสนุนจากปัจจัยบวก[/FACTOR3]
[CONCLUSION]มาตรการลดภาระค่าครองชีพของภาครัฐและบรรยากาศเทศกาลที่หนุนการใช้จ่าย ถูกถ่วงดุลโดยความไม่แน่นอนทางการเมืองที่ทำให้ผู้บริโภคระมัดระวังการใช้จ่าย ส่งผลให้ความเชื่อมั่นผู้บริโภคปรับตัวทรงตัว[/CONCLUSION]
 ==========================================================================
"""

# ==========================================
# PROMPT BUILDER
# ==========================================

def build_prompt(month, predicted, direction, evidence_rows):
    evidence_blocks = []
    allowed_tags = []

    for i, row in enumerate(evidence_rows, 1):
        shap_feature_raw = clean_text(row.get("SHAP_Feature", ""))
        base_feat = re.sub(r"_pastcov.*", "", shap_feature_raw, flags=re.IGNORECASE)
        base_feat = re.sub(r"_lag.*", "", base_feat, flags=re.IGNORECASE).strip().lower()

        shap_dir    = clean_text(row.get("SHAP_Direction", ""))
        trend       = clean_text(row.get("3M_Trend", ""))
        pos_summary = clean_text(row.get("Summary_3M_Positive", ""))
        neg_summary = clean_text(row.get("Summary_3M_Negative", ""))
        shap_val    = float(row.get("SHAP_Value", 0))
        aspect      = clean_text(str(row.get("Evidence_Aspects", "")))
        definition  = get_definition(base_feat)
        relationship = get_relationship(base_feat)
        feature_tag = shap_feature_raw

        allowed_tags.append(f"({i}) {feature_tag}")

        if "เพิ่มขึ้น" in direction:
            primary_label   = "สัญญาณหลัก [ใช้เป็นแกนอธิบาย]"
            secondary_label = "สัญญาณรอง  [ใช้แสดงความสมดุลเท่านั้น]"
            primary         = pos_summary
            secondary       = neg_summary[:200] if neg_summary else "ไม่มี"
        elif "ลดลง" in direction:
            primary_label   = "สัญญาณหลัก [ใช้เป็นแกนอธิบาย]"
            secondary_label = "สัญญาณรอง  [ใช้แสดงความสมดุลเท่านั้น]"
            primary         = neg_summary
            secondary       = pos_summary[:200] if pos_summary else "ไม่มี"
        else:
            primary_label   = "สัญญาณบวก"
            secondary_label = "สัญญาณลบ"
            primary         = pos_summary
            secondary       = neg_summary

        block = (
            f"ปัจจัยที่ {i}: {base_feat} ({feature_tag})\n"
            f"  นิยาม                : {definition}\n"
            f"  ความสัมพันธ์กับ CCI : {relationship}\n"
            f"  ทิศทาง              : {shap_dir} (น้ำหนัก {shap_val:+.3f})\n"
            f"  แนวโน้ม 3 เดือน     : {trend}\n"
            f"  หลักฐานจาก          : {aspect}\n"
            f"  {primary_label}     : {primary}\n"
            f"  {secondary_label}   : {secondary}"
        )
        evidence_blocks.append(block)

    evidence_text     = "\n\n".join(evidence_blocks)
    allowed_tags_text = "\n".join(allowed_tags)

    return f"""คุณคือนักเศรษฐศาสตร์อาวุโสของสถาบันวิจัยเศรษฐกิจไทย มีหน้าที่เขียนบทวิเคราะห์ดัชนีความเชื่อมั่นผู้บริโภค (CCI) เพื่อเผยแพร่ในรายงานวิชาการรายเดือน

===== ข้อมูลที่ต้องนำไปใช้ =====
เดือนที่วิเคราะห์ : {month}
ค่า CCI ที่คาดการณ์ : {predicted:.2f}
ทิศทาง : {direction}

===== reference tag ที่อนุญาต (ใช้ได้เฉพาะ 3 tag นี้เท่านั้น ห้ามเขียน tag อื่นโดยเด็ดขาด) =====
{allowed_tags_text}

===== หลักฐานจากข่าว (เรียงจากมีผลกระทบมากที่สุด → น้อยที่สุด) =====
{evidence_text}

{SHOT_EXAMPLES}
===== รูปแบบผลลัพธ์ที่ต้องการ =====
ให้เขียนบทวิเคราะห์แบ่งเป็น 4 ส่วน โดยครอบแต่ละส่วนด้วยป้ายกำกับเปิด-ปิดตามรูปแบบนี้ทุกครั้ง:

[FACTOR1]อธิบายปัจจัยที่ 1[/FACTOR1]
[FACTOR2]อธิบายปัจจัยที่ 2[/FACTOR2]
[FACTOR3]อธิบายปัจจัยที่ 3[/FACTOR3]
[CONCLUSION]ประโยคปิด[/CONCLUSION]

===== คำแนะนำแต่ละส่วน =====

[FACTOR1] — ปัจจัยหลัก อธิบายละเอียดที่สุด
[FACTOR2] — ปัจจัยสนับสนุน อธิบายกระชับกว่า
[FACTOR3] — ปัจจัยสนับสนุน อธิบายกระชับกว่า
โครงสร้างแต่ละปัจจัย: [เหตุการณ์/บริบทจาก "สัญญาณหลัก"] ทำให้ [ผลกระทบทางเศรษฐกิจ] ส่งผลให้ [ความเชื่อมั่น/กำลังซื้อเปลี่ยนแปลง]
ความยาวต่อปัจจัย: 2–3 ประโยค

[CONCLUSION] — ประโยคสรุปภาพรวม (Quick-Glance Card)
เป้าหมาย:
เขียนประโยคสรุป 2–3 ประโยคที่ทำให้ผู้อ่านเข้าใจทันทีว่า "อะไรคือสาเหตุหลักที่ทำให้ ดัชนีความเชื่อมั่นผู้บริโภค {direction}"
 
กฎการเขียน:
- ให้ใช้คำว่า “ดัชนีความเชื่อมั่นผู้บริโภค” แทนชื่อย่อ
- ระบุชื่อสาเหตุอย่างเป็นรูปธรรม ห้ามใช้คำลอยๆ เช่น "หลายปัจจัย" "ปัจจัยต่างๆ" "ปัจจัยข้างต้น"
- ต้องสรุปจาก FACTOR1–3 เป็นหลัก 
- ต้องแสดง "ความสัมพันธ์เชิงเหตุและผล" (cause → effect) อย่างชัดเจน
- ห้ามกล่าวถึงตัวเลข SHAP หรือกระบวนการทางเทคนิค, ห้ามระบุชื่อเดือนหรือช่วงเวลา
- ห้ามขึ้นต้นด้วย "โดยรวมแล้ว" หรือ "ปัจจัยข้างต้น"
- ความยาว: 2-3 ประโยคสมบูรณ์ ห้ามตัดกลางคำหรือกลางประโยค
 

===== กฎเหล็กที่ห้ามละเมิด =====
1. ต้องใช้ delimiter ครบทั้ง 4 ส่วน [FACTOR1][FACTOR2][FACTOR3][CONCLUSION] ห้ามละเว้นหรือเปลี่ยนชื่อ delimiter
2. แต่ละส่วนต้องเป็นข้อความต่อเนื่อง ห้ามใช้ bullet points หรือหัวข้อย่อยภายในส่วน
3. ห้ามอ้างชื่อโมเดล, ค่า SHAP, หรือกระบวนการทางเทคนิคใดๆ ห้ามเขียนสัญลักษณ์ลูกศร →
4. ทุกปัจจัยต้องอธิบายกลไกเป็นลูกโซ่: [เหตุการณ์] ทำให้ [ผลกระทบเศรษฐกิจ] ส่งผลให้ [ความเชื่อมั่น/กำลังซื้อ ↑↓] ห้ามแค่ระบุว่ามีเหตุการณ์อะไรเกิดขึ้น
5. ห้ามนำข้อเท็จจริงภายนอกที่ไม่อยู่ในหลักฐานมาใส่
6. แต่ละปัจจัยต้องอธิบายจาก "สัญญาณหลัก" เป็นแกนหลัก "สัญญาณรอง" ใช้แสดงความสมดุลเท่านั้น สอดคล้องกับทิศทาง "{direction}"
7. ใช้ "ความสัมพันธ์กับ CCI" เป็นหลักในการอธิบายทิศทาง ห้ามตีความสวนทางกับความสัมพันธ์ที่ระบุไว้
8. ห้ามระบุชื่อเดือนหรือช่วงเวลาใดๆ ในบทวิเคราะห์
9. [กฎที่เข้มงวดที่สุด] reference tag ที่ใช้ต้องตรงกับรายการใน "reference tag ที่อนุญาต" เท่านั้น ห้ามแต่ง tag ใหม่ ห้ามดัดแปลง ห้ามซ้ำ และต้องใช้ครบทั้ง 3 tag กระจายใน FACTOR1 FACTOR2 FACTOR3

เขียนเฉพาะ 4 ส่วนตาม delimiter ข้างต้น ไม่ต้องมีคำนำหรือคำอธิบายเพิ่มเติม:"""


# ==========================================
# SECTION PARSER
# for open and closing factor tags
# ==========================================

def parse_sections(raw: str) -> dict:
    keys = ["FACTOR1", "FACTOR2", "FACTOR3", "CONCLUSION"]
    sections = {}

    for i, key in enumerate(keys):
        closed = re.search(rf"\[{key}\](.*?)\[/{key}\]", raw, re.DOTALL)
        if closed:
            sections[key.lower()] = clean_text(closed.group(1))
            continue

        if i + 1 < len(keys):
            next_key = keys[i + 1]
            open_match = re.search(rf"\[{key}\](.*?)(?=\[{next_key}\]|$)", raw, re.DOTALL)
        else:
            open_match = re.search(rf"\[{key}\](.*?)$", raw, re.DOTALL)

        sections[key.lower()] = clean_text(open_match.group(1)) if open_match else ""

    sections["parse_ok"] = all(sections[k] for k in ["factor1", "factor2", "factor3", "conclusion"])
    return sections


# ==========================================
# MAIN
# ==========================================

def main():
    print("Loading files...")
    df_3m   = pd.read_csv(SUMMARY_3M_PATH, encoding="utf-8-sig")
    df_pred = pd.read_csv(PRED_PATH,       encoding="utf-8-sig")

    df_3m.columns   = [c.strip() for c in df_3m.columns]
    df_pred.columns = [c.strip() for c in df_pred.columns]

    df_3m["Target_Month"] = df_3m["Target_Month"].astype(str).str.strip().str[:7]
    df_pred["date"]       = df_pred["date"].astype(str).str.strip().str[:7]

    print(f"3M summary columns  : {list(df_3m.columns)}")
    print(f"Sample SHAP features: {df_3m['SHAP_Feature'].unique()[:6].tolist()}")

    start_dt      = datetime.strptime(f"{START_MONTH}-01", "%Y-%m-%d")
    end_dt        = datetime.strptime(f"{END_MONTH}-01",   "%Y-%m-%d")
    target_months = pd.date_range(start=start_dt, end=end_dt, freq="MS")

    init_output()
    print(f"\nTarget months: {START_MONTH} → {END_MONTH} | Model: {MODEL_NAME}\n")

    for current_month_dt in tqdm(target_months, desc="Months"):
        month = current_month_dt.strftime("%Y-%m")

        pred_row = df_pred[df_pred["date"] == month]
        if pred_row.empty:
            print(f"  [!] No prediction data for {month} — skipping")
            continue
        predicted = float(pred_row.iloc[0]["predicted"])
        direction = str(pred_row.iloc[0]["direction"])

        month_evidence = df_3m[df_3m["Target_Month"] == month].copy()
        if month_evidence.empty:
            print(f"  [!] No 3M evidence for {month} — skipping")
            continue

        month_evidence = month_evidence.sort_values("ABS_SHAP", ascending=False).head(3)
        evidence_rows  = month_evidence.to_dict(orient="records")

        print(f"  [{month}] CCI={predicted:.2f} | {direction} | "
              f"Features: {[r.get('SHAP_Feature', '') for r in evidence_rows]}")

        prompt = build_prompt(month, predicted, direction, evidence_rows)

        # # Print full prompt for debugging
        # # Print full prompt for debugging
        # print(f"\n{'='*60}")
        # print(f"FULL PROMPT FOR {month}:")
        # print(prompt)
        # print('='*60 + "\n")

        allowed_tags_print = "\n".join([f"({i+1}) {clean_text(r.get('SHAP_Feature',''))}" for i, r in enumerate(evidence_rows)])
        evidence_print     = "\n".join([
            f"  ปัจจัยที่ {i+1}: {clean_text(r.get('SHAP_Feature',''))} | {clean_text(r.get('SHAP_Direction',''))} | แนวโน้ม: {clean_text(r.get('3M_Trend',''))}"
            for i, r in enumerate(evidence_rows)
        ])
        print(f"\nเดือนที่วิเคราะห์   : {month}")
        print(f"ค่า CCI ที่คาดการณ์ : {predicted:.2f}")
        print(f"ทิศทาง             : {direction}")
        print(f"reference tags:\n{allowed_tags_print}")
        print(f"evidence:\n{evidence_print}")

        reasoning = query_ollama(prompt)
        sections  = parse_sections(reasoning)

        if not sections["parse_ok"]:
            print(f"  [!] parse_ok=False for {month} — some delimiters missing, raw saved")

        # Build intro deterministically in Python — no LLM needed
        intro = (
            f"ดัชนีความเชื่อมั่นผู้บริโภคประจำเดือน {month} "
            f"อยู่ที่ระดับ {predicted:.2f} "
            f"คาดว่าจะปรับตัว{direction} "
            f"โดยปัจจัยสนับสนุนที่ส่งผลให้ดัชนีปรับตัวในทิศทางดังกล่าวมาจากหลายปัจจัย อาทิ"
        )

        top3_shap = [clean_text(er.get("SHAP_Feature", "")) for er in evidence_rows]

        append_row({
            "date":          month,
            "predicted":     round(predicted, 2),
            "direction":     direction,
            "top3_shap":     top3_shap,
            "intro":         intro,
            "factor1_text":  sections["factor1"],
            "factor2_text":  sections["factor2"],
            "factor3_text":  sections["factor3"],
            "conclusion":    sections["conclusion"],
            "parse_ok":      sections["parse_ok"],
            "raw_reasoning": reasoning,
        })

    print(f"\nDone. CSV saved to:\n  {OUTPUT_CSV}")

    # ==========================================
    # EXPORT JSON
    # ==========================================
    import json

    df_out = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
    records = []

    for _, r in df_out.iterrows():
        # top3_shap stored as string repr of list — parse it back
        try:
            import ast
            shap_list = ast.literal_eval(str(r["top3_shap"]))
        except Exception:
            shap_list = [str(r["top3_shap"])]

        factors = [
            {"tag": shap_list[0] if len(shap_list) > 0 else "", "text": str(r.get("factor1_text", ""))},
            {"tag": shap_list[1] if len(shap_list) > 1 else "", "text": str(r.get("factor2_text", ""))},
            {"tag": shap_list[2] if len(shap_list) > 2 else "", "text": str(r.get("factor3_text", ""))},
        ]

        records.append({
            "date":          str(r["date"]),
            "predicted":     float(r["predicted"]),
            "direction":     str(r["direction"]),
            "top3_shap":     shap_list,
            "intro":         str(r.get("intro", "")),
            "factors":       factors,
            "conclusion":    str(r.get("conclusion", "")),
            "parse_ok":      bool(r.get("parse_ok", False)),
            "raw_reasoning": str(r.get("raw_reasoning", "")),
        })

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"JSON saved to:\n  {OUTPUT_JSON}")

if __name__ == "__main__":
    main()