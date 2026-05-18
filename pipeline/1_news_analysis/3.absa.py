import csv
import json
import os
import re
import time
from tqdm import tqdm
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import requests

# ========================================
# CONFIGURATION
# ========================================
INPUT_CSV = r"/home/xecon/sp2025/SP2025-SeniorProject/datapreprocessing/All3econnews2017_2026_full_sum.csv"
OUTPUT_DIR = r"/home/xecon/sp2025/SP2025-SeniorProject/sentiment/outputs_thai2/All3econnews2017_2026_full_sum_results/llama3.1_70b"
OUTPUT_FILENAME = "2017-2026.csv"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma2:27b"
TEMPERATURE = 0.1
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

def call_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "temperature": TEMPERATURE,
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        return r.json().get("response", "")
    except Exception:
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
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fpath = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)

    print(f"Starting processing with {MODEL_NAME}...")
    print(f"Results will be saved to <3: {fpath}")

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
    # RESUME LOGIC
    # -----------------------------
    processed = 0
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8-sig") as f:
            processed = sum(1 for _ in f) - 1
            if processed < 0:
                processed = 0

    print(f"Resuming from row: {processed}")

    for i, r in enumerate(tqdm(rows, desc="Analyzing")):
        if i < processed:
            continue

        content_to_analyze = r.get("summary") or r.get("headline") or ""
        news_text = f"ข่าว: {content_to_analyze}"

        final_result = None
        current_prompt = SYSTEM_PROMPT + "\n\n" + news_text

        for attempt in range(MAX_RETRIES + 1):
            raw_response = call_ollama(current_prompt)
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
