import csv
import json
import os
import re
import time
from tqdm import tqdm
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import requests
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # project root
from config import cfg, call_hf_api, Files, Dirs, HF_LLM

# ========================================
# CONFIGURATION
# ========================================
INPUT_CSV = str(Files.RELEVANCE_CSV)  # output of step 2 (relevance filter)
OUTPUT_DIR = str(Dirs.ARTIFACTS / "absa_results")

# LLM via HuggingFace Inference API
MODEL_NAME = HF_LLM.ABSA_MODEL
TEMPERATURE = HF_LLM.TEMPERATURE
MAX_RETRIES = HF_LLM.MAX_RETRIES

# Processing Limits
PROCESS_LIMIT = None  # Set to a number (e.g., 50) for testing
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

# -----------------------------
# PROMPT SETTINGS (NO RATIONALITY / NO EMOJIS)
# -----------------------------
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
    """Classify impact in Python based on score."""
    if score >= 0.60: return "Positive"
    if score <= 0.40: return "Negative"
    return "Neutral"

def get_monthly_filename(date_str: str) -> str:
    """Extract YYYY-MM from published_at to name the CSV."""
    # Expected format: 2024-02-13... or similar
    match = re.search(r'(\d{{4}})-(\d{{2}})', date_str)
    if match:
        return f"sentiment_results_{match.group(1)}_{match.group(2)}.csv"
    return "sentiment_results.csv"

def call_llm(prompt: str) -> str:
    """Call HuggingFace Inference API for ABSA."""
    return call_hf_api(
        prompt,
        model=MODEL_NAME,
        max_tokens=200,
        temperature=TEMPERATURE,
        retries=MAX_RETRIES,
    )

def extract_json(text: str) -> Dict[str, Any]:
    text = re.sub(r'```json\s*|```', '', text).strip()
    m = re.search(r'\{.*\}', text, flags=re.DOTALL)
    if not m: raise ValueError("No JSON found")
    return json.loads(m.group(0))

def validate_and_fix(obj: Dict[str, Any]) -> Dict[str, Any]:
    # Check Aspect
    if obj.get("Aspect") not in FACTORS_LIST:
        obj["Aspect"] = "เศรษฐกิจไทย" # Safe default
    # Check Score
    try:
        score = float(obj.get("sentiment_score", 0.5))
        obj["sentiment_score"] = round(max(0.0, min(1.0, score)), 2)
    except:
        obj["sentiment_score"] = 0.5
    # Check Effect
    if obj.get("effect_type") not in EFFECT_TYPES:
        obj["effect_type"] = "Short-term"
    return obj

# -----------------------------
# MAIN PIPELINE
# -----------------------------
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Starting processing with {MODEL_NAME}...")

    # Load CSV
    rows = []
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if str(r.get("CCI_pred")) == "1":
                rows.append(r)
            if PROCESS_LIMIT and len(rows) >= PROCESS_LIMIT:
                break

    for r in tqdm(rows, desc="Analyzing"):
        news_text = f"ข่าว: {r.get('summary', r.get('headline', ''))}"
        
        # LLM Logic with Repair Loop
        final_result = None
        current_prompt = SYSTEM_PROMPT + "\n\n" + news_text
        
        for attempt in range(MAX_RETRIES + 1):
            raw_response = call_llm(current_prompt)
            try:
                data = extract_json(raw_response)
                final_result = validate_and_fix(data)
                break
            except:
                current_prompt = f"{news_text}\n\n{REPAIR_PROMPT}\nError in last attempt."

        # Fallback if all retries fail
        if not final_result:
            final_result = {"sentiment_score": 0.5, "Aspect": "เศรษฐกิจไทย", "effect_type": "Short-term"}

        # Calculate Impact in Python
        final_result["impact_type"] = get_impact_type(final_result["sentiment_score"])

        # Determine Output File
        fname = get_monthly_filename(r.get("published_at", "2026-01"))
        fpath = os.path.join(OUTPUT_DIR, fname)
        
        # Merge data
        output_row = {**r, **final_result}

        # Append to CSV
        file_exists = os.path.isfile(fpath)
        with open(fpath, "a", encoding="utf-8-sig", newline="") as out_f:
            writer = csv.DictWriter(out_f, fieldnames=output_row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(output_row)

    print("Process complete. Check the outputs folder.")

if __name__ == "__main__":
    main()