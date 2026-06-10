import csv
import json
import os
import re
import time
from tqdm import tqdm
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import Dirs, Files, Pipeline, call_hf_api


# ========================================
# CONFIGURATION
# ========================================

INPUT_CSV = Files.SUMMARIZED_NEWS_CSV
OUTPUT_FILE = Files.ABSA_NEWS_CSV
MAX_RETRIES = 3

# Processing Limits
PROCESS_LIMIT = None  # for testing
# ========================================

FACTORS = {
    "เศรษฐกิจไทย": "General macroeconomic indicators (GDP, inflation, interest rates).",
    "มาตรการของรัฐ": "Specific government actions, stimulus packages, or new regulations.",
    "สังคม/ความมั่นคง": "Crimes, public safety, and national security.",
    "การเมือง": "Elections, cabinet changes, and political movements.",
    "ราคาสินค้าเกษตร": "Price fluctuations of rice, rubber, palm, etc.",
    "เศรษฐกิจโลก": "International trade, global markets, and global recession risks.",
    "ภัยพิบัติ/โรคระบาด": "Natural disasters, PM2.5, and public health crises.",
    "ราคาน้ำมันเชื้อเพลิง": "Changes in oil, gas, and electricity prices.",
}

FACTORS_LIST = list(FACTORS.keys())
EFFECT_TYPES = ["Short-term", "Long-term"]

SYSTEM_PROMPT = f"""
You are a Thai Economic Analyst. Analyze the news and return ONLY a JSON object.

### ASPECT CATEGORIES:
{", ".join(FACTORS_LIST)}

### OUTPUT SCHEMA:
{{
  "sentiment_score": <number 0.00-1.00>,
  "Aspect": "<one of the categories above>",
  "effect_type": "Short-term" | "Long-term"
}}

### RULES:
1) Output JSON ONLY. No extra text.
2) sentiment_score: 0.00-0.39 (Negative), 0.40-0.60 (Neutral), 0.61-1.00 (Positive).
3) effect_type: Short-term (temporary/immediate), Long-term (structural/policy).
4) Aspect: Must be exactly one from the list provided.
""".strip()

REPAIR_PROMPT = """
Your previous output was invalid.
Return ONLY valid JSON with fields: sentiment_score, Aspect, effect_type.
Ensure Aspect is from the allowed list.
"""

# -----------------------------
# LOGIC FUNCTIONS
# -----------------------------
def get_impact_type(score: float) -> str:
    if score >= 0.60: return "Positive"
    if score <= 0.40: return "Negative"
    return "Neutral"

def call_model(prompt: str) -> str:
    try:
        return call_hf_api(prompt, max_tokens=150, temperature=0.1)
    except Exception as e:
        print(f"LLM API Error: {e}")
        return ""

def extract_json(text: str) -> Dict[str, Any]:
    text = re.sub(r'```json\s*|```', '', text).strip()
    m = re.search(r'\{.*\}', text, flags=re.DOTALL)
    if not m: raise ValueError("No JSON found")
    return json.loads(m.group(0))

def validate_and_fix(obj: Dict[str, Any]) -> Dict[str, Any]:
    if obj.get("Aspect") not in FACTORS_LIST:
        obj["Aspect"] = "เศรษฐกิจไทย"
    try:
        score = float(obj.get("sentiment_score", 0.5))
        obj["sentiment_score"] = round(max(0.0, min(1.0, score)), 2)
    except:
        obj["sentiment_score"] = 0.5
    if obj.get("effect_type") not in EFFECT_TYPES:
        obj["effect_type"] = "Short-term"
    return obj

# -----------------------------
# MAIN PIPELINE
# -----------------------------
def main():
    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    fpath = str(OUTPUT_FILE)

    print(f"Starting processing with HuggingFace Serverless API...")
    print(f"Results will be saved to: {fpath}")

    # Load CSV
    rows = []
    if not os.path.exists(INPUT_CSV):
        print(f"Error: File not found at {INPUT_CSV}")
        return

    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
            if PROCESS_LIMIT and len(rows) >= PROCESS_LIMIT:
                break

    if not rows:
        print("The CSV file appears to be empty.")
        return

    # -----------------------------
    # RESUME LOGIC — id-based
    # -----------------------------
    def row_key(row):
        """Stable per-article key: prefer article_id, fall back to url."""
        aid = str(row.get("article_id", "") or "").strip()
        if aid and aid.lower() != "nan":
            return aid
        return str(row.get("url", "") or "").strip()

    done_ids = set()
    if os.path.exists(fpath):
        try:
            with open(fpath, "r", encoding="utf-8-sig") as f:
                existing = csv.DictReader(f)
                for row in existing:
                    k = row_key(row)
                    if k:
                        done_ids.add(k)
            print(f"Resuming: {len(done_ids)} articles already processed")
        except Exception as e:
            print(f"  [WARN] Could not load resume keys ({e}); starting fresh")

    for i, r in enumerate(tqdm(rows, desc="Analyzing")):
        if row_key(r) in done_ids:
            continue

        content_to_analyze = r.get("summary") or r.get("headline") or ""
        news_text = f"ข่าว: {content_to_analyze}"

        final_result = None
        current_prompt = SYSTEM_PROMPT + "\n\n" + news_text

        for attempt in range(MAX_RETRIES + 1):
            raw_response = call_model(current_prompt)
            try:
                data = extract_json(raw_response)
                final_result = validate_and_fix(data)
                break
            except:
                current_prompt = f"{news_text}\n\n{REPAIR_PROMPT}"

        if not final_result:
            final_result = {"sentiment_score": 0.5, "Aspect": "เศรษฐกิจไทย", "effect_type": "Short-term"}

        final_result["impact_type"] = get_impact_type(final_result["sentiment_score"])

        # Merge news data with LLM results
        output_row = {**r, **final_result}

        # Append to the single master file
        file_exists = os.path.isfile(fpath)
        with open(fpath, "a", encoding="utf-8-sig", newline="") as out_f:
            writer = csv.DictWriter(out_f, fieldnames=output_row.keys())
            if not file_exists or os.path.getsize(fpath) == 0:
                writer.writeheader()
            writer.writerow(output_row)

    print(f"\nSuccess! All results saved in: {fpath}")

if __name__ == "__main__":
    main()
