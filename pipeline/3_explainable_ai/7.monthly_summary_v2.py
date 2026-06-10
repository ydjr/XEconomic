import re
import os
import time
import requests
import pandas as pd
from pathlib import Path
from tqdm import tqdm

try:
    import tiktoken
    ENC = tiktoken.get_encoding("cl100k_base")
except Exception:
    ENC = None

import sys
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import Dirs, Files, call_hf_api

# ==========================================
# CONFIG
# ==========================================
INPUT_CSV = Files.ABSA_NEWS_CSV
OUTPUT_CSV = Files.MONTHLY_SUMMARY_CSV
OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

MAX_RETRIES       = 2
RETRY_SLEEP       = 6
MAX_OUTPUT_TOKENS = 500

INPUT_TOKEN_BUDGET = 6_000   # if total tokens exceed this -> use map-reduce
CHUNK_TOKEN_BUDGET = 2_000   # max tokens per chunk in map-reduce

ASPECTS = [
    "การเมือง",
    "ภัยพิบัติ/โรคระบาด",
    "มาตรการของรัฐ",
    "ราคาน้ำมันเชื้อเพลิง",
    "ราคาสินค้าเกษตร",
    "สังคม/ความมั่นคง",
    "เศรษฐกิจโลก",
    "เศรษฐกิจไทย",
]

# ==========================================
# UTILITIES
# ==========================================

def clean_text(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.replace("```", " ").replace("\u200b", " ")
    return re.sub(r"\s+", " ", s).strip()

def count_tokens(text: str) -> int:
    text = clean_text(text)
    if not text:
        return 0
    if ENC:
        return len(ENC.encode(text))
    return max(1, len(text) // 4)

def build_news_block(summaries: list) -> str:
    lines = []
    for i, s in enumerate(summaries):
        s = clean_text(s)
        if s:
            lines.append(f"[{i+1}] {s}")
    return "\n".join(lines)

def call_model(prompt: str) -> str:
    for attempt in range(MAX_RETRIES + 1):
        try:
            return call_hf_api(prompt, max_tokens=MAX_OUTPUT_TOKENS, temperature=0.1)
        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"  [Retry {attempt+1}] HF API error: {e} — waiting {RETRY_SLEEP}s")
                time.sleep(RETRY_SLEEP)
            else:
                return f"[HF_ERROR] {e}"

def chunk_by_budget(summaries: list, budget: int) -> list:
    """Split list of summaries into chunks that fit within token budget."""
    chunks, cur, cur_tok = [], [], 0
    for s in summaries:
        s = clean_text(s)
        if not s:
            continue
        t = count_tokens(s) + 4
        if cur and (cur_tok + t) > budget:
            chunks.append(cur)
            cur, cur_tok = [s], t
        else:
            cur.append(s)
            cur_tok += t
    if cur:
        chunks.append(cur)
    return chunks

# ==========================================
# PROMPT BUILDERS
# ==========================================

def prompt_summarize(month: str, aspect: str, sentiment_side: str, news_block: str) -> str:
    """
    Main summarization prompt for one polarity side.
    Fixed issues:
    - No bullet points / numbered lists allowed
    - No relevance commentary allowed
    - Must summarize what is given regardless of quality
    - No outside knowledge
    """
    return f"""คุณเป็นผู้ช่วยวิเคราะห์ข่าวเศรษฐกิจไทย
หน้าที่ของคุณ: สรุปภาพรวมของสัญญาณ{sentiment_side}ในหมวด "{aspect}" ประจำเดือน {month}

กฎสำคัญ (ห้ามฝ่าฝืนโดยเด็ดขาด):
1. ยึดข้อมูลจากข้อความที่ให้มาเท่านั้น ห้ามเพิ่มข้อมูลภายนอก
2. ห้ามคาดเดาหรือวิเคราะห์เกินจากเนื้อหาที่ปรากฏในข่าว
3. ห้ามใช้ข้อ 1. 2. 3. หรือ bullet points หรือ "-" นำหน้าประโยคโดยเด็ดขาด
4. ห้ามแสดงความเห็นว่าข่าวเกี่ยวข้องหรือไม่เกี่ยวข้องกับหมวดนี้
5. ให้สรุปเนื้อหาที่มีอยู่เท่านั้น หากข่าวมีน้อยให้สรุปสั้นๆ จากที่มี
6. ห้ามขึ้นต้นด้วยคำว่า "ขออภัย" หรือปฏิเสธการตอบ ห้ามขึ้นต้นด้วย "บทความนี้" หรือ "ข่าวสารเหล่านี้" หรือคำที่อธิบายตัวเนื้อหา ให้เริ่มต้นด้วยเนื้อหาโดยตรง
7. เขียนเป็นภาษาไทยทางการ เป็นย่อหน้าเดียวต่อเนื่อง ห้ามเกิน 5 ประโยค
แนวทางการสรุป: กล่าวถึงประเด็นหลักที่ปรากฏในข่าวของเดือนนั้น ระบุเหตุการณ์หรือตัวเลขสำคัญที่เกิดขึ้นจริง หากมีหลายเหตุการณ์ให้เรียงจากสำคัญมากไปน้อย

ข่าวในหมวด "{aspect}" (สัญญาณ{sentiment_side}) เดือน {month}:
{news_block}

บทสรุป (ย่อหน้าเดียว ห้ามใช้ข้อหรือ bullet):"""


def prompt_reduce(month: str, aspect: str, sentiment_side: str, chunk_summaries: list) -> str:
    """
    Reduce multiple chunk summaries into one final summary (map-reduce step).
    Same strict rules applied.

    128 pos news
        ↓ chunk by 2000 tokens each
    [chunk1] [chunk2] [chunk3] [chunk4] [chunk5]
        ↓ LLM summarizes each chunk separately
    [summary1] [summary2] [summary3] [summary4] [summary5]
        ↓ LLM combines all chunk summaries into ONE final summary
    [Final Positive_Summary for เศรษฐกิจไทย 2024-01]

    """
    block = "\n".join(
        f"[{i+1}] {clean_text(s)}"
        for i, s in enumerate(chunk_summaries) if clean_text(s)
    )
    return f"""รวมบทสรุปย่อยต่อไปนี้เป็น "บทสรุปสุดท้าย" สำหรับสัญญาณ{sentiment_side}
หมวด "{aspect}" เดือน {month}

กฎสำคัญ:
1. ยึดข้อมูลจากบทสรุปย่อยที่ให้มาเท่านั้น ห้ามเพิ่มข้อมูลภายนอก
2. ห้ามใช้ข้อ 1. 2. 3. หรือ bullet points หรือ "-" นำหน้าประโยค
3. เขียนเป็นภาษาไทยทางการ ความยาว 2-3 ประโยค เป็นย่อหน้าเดียวต่อเนื่อง
4. ห้ามขึ้นต้นด้วย "ขออภัย" หรือปฏิเสธการตอบ

บทสรุปย่อย:
{block}

บทสรุปสุดท้าย (ย่อหน้าเดียว ห้ามใช้ข้อหรือ bullet):"""

# ==========================================
# CORE SUMMARIZATION
# ==========================================

def summarize_side(month: str, aspect: str, sentiment_side: str, summaries: list) -> str:
    """
    Summarize one polarity side (Positive or Negative) for a given month+aspect.
    Uses map-reduce chunking if total tokens exceed INPUT_TOKEN_BUDGET.
    """
    n = len(summaries)
    if n == 0:
        return ""  # No news on this side — leave blank
    if n == 1:
        return clean_text(summaries[0])  # Single news — copy directly

    total_tokens = sum(count_tokens(s) for s in summaries)

    # if not exceed 6_000
    if total_tokens <= INPUT_TOKEN_BUDGET:
        block  = build_news_block(summaries)
        prompt = prompt_summarize(month, aspect, sentiment_side, block)
        return call_model(prompt)

    # if exceed 
    print(f"    [map-reduce] {month} | {aspect} | {sentiment_side} | tokens={total_tokens}")
    chunks = chunk_by_budget(summaries, CHUNK_TOKEN_BUDGET)
    chunk_results = []
    for idx, ch in enumerate(chunks):
        block  = build_news_block(ch)
        prompt = prompt_summarize(month, aspect, sentiment_side, block)
        result = call_model(prompt)
        chunk_results.append(result)

    reduce_prompt = prompt_reduce(month, aspect, sentiment_side, chunk_results)
    return call_model(reduce_prompt)

# ==========================================
# RESUME LOGIC
# ==========================================

def load_done_keys() -> set:
    """Load already completed (Month, Aspect) pairs to support resume."""
    keys = set()
    if OUTPUT_CSV.exists():
        try:
            df = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
            if {"Month", "Aspect"}.issubset(df.columns):
                for _, row in df.iterrows():
                    keys.add((str(row["Month"]), str(row["Aspect"])))
        except Exception:
            pass
    return keys

def append_row(row: dict) -> None:
    df_row = pd.DataFrame([row])
    if OUTPUT_CSV.exists():
        df_row.to_csv(OUTPUT_CSV, mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        df_row.to_csv(OUTPUT_CSV, mode="w", header=True, index=False, encoding="utf-8-sig")

# ==========================================
# MAIN
# ==========================================

def main():
    print("Loading ABSA CSV...")
    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]

    required = {"published_at", "summary", "Aspect", "impact_type"}
    missing  = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}. Found: {list(df.columns)}")

    # Parse dates
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
    df = df[df["published_at"].notna()].copy()
    df["Year"]  = df["published_at"].dt.year
    df["Month"] = df["published_at"].dt.to_period("M").astype(str)
    
    if df.empty:
        print(f"No data found.")
        return

    df["summary"]     = df["summary"].astype(str).apply(clean_text)
    df["Aspect"]      = df["Aspect"].astype(str).apply(clean_text)
    df["impact_type"] = df["impact_type"].astype(str).apply(clean_text)

    done_keys = load_done_keys()
    months    = sorted(df["Month"].unique())
    print(f"Years: {sorted(df['Year'].unique())} | Months: {months}")
    print(f"Resuming: {len(done_keys)} pairs already done.")

    for month in tqdm(months, desc="Months"):
        month_df = df[df["Month"] == month]

        for aspect in tqdm(ASPECTS, desc=f"  {month}", leave=False):
            key = (month, aspect)
            if key in done_keys:
                continue

            aspect_df = month_df[month_df["Aspect"] == aspect].copy()
            aspect_df = aspect_df[aspect_df["summary"].str.len() > 0]

            if aspect_df.empty:
                continue  # No news for this month+aspect — skip entirely

            # --- Split by polarity ---
            # Neutral is excluded
            pos_summaries = aspect_df[aspect_df["impact_type"] == "Positive"]["summary"].tolist()
            neg_summaries = aspect_df[aspect_df["impact_type"] == "Negative"]["summary"].tolist()
            pos_count     = len(pos_summaries)
            neg_count     = len(neg_summaries)
            total_count   = len(aspect_df)

            # --- Overall Lean: simple majority count ---
            if pos_count > neg_count:
                overall_lean = "บวก"
            elif neg_count > pos_count:
                overall_lean = "ลบ"
            else:
                overall_lean = "ทรงตัว"

            print(f"\n  [{month}] {aspect} | pos={pos_count} neg={neg_count} total={total_count} → {overall_lean}")

            # --- Summarize each polarity side ---
            pos_summary = summarize_side(month, aspect, "บวก", pos_summaries)
            neg_summary = summarize_side(month, aspect, "ลบ",  neg_summaries)

            row = {
                "Month":            month,
                "Aspect":           aspect,
                "Total_News":       total_count,
                "Pos_Count":        pos_count,
                "Neg_Count":        neg_count,
                "Overall_Lean":     overall_lean,
                "Positive_Summary": pos_summary,
                "Negative_Summary": neg_summary,
            }

            append_row(row)
            done_keys.add(key)

    print(f"\nDone. Output saved to:\n  {OUTPUT_CSV}")

if __name__ == "__main__":
    main()