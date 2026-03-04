import csv
import json
import os
import re
import argparse
import time
from tqdm import tqdm
from typing import Dict, Any
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# ========================================
# CONFIGURATION
# ========================================
MODEL_NAME = "meta-llama/Llama-3.1-8B"
TEMPERATURE = 0.1
MAX_NEW_TOKENS = 256
MAX_RETRIES = 3

# Processing Limits
PROCESS_LIMIT = None  # Set to a number (e.g., 5) for testing
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
# PROMPT SETTINGS
# -----------------------------
SYSTEM_PROMPT = f"""You are a Thai Economic Analyst. Analyze the news and return ONLY a JSON object.

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
4) Aspect: Must be exactly one from the list provided."""

REPAIR_PROMPT = """Your previous output was invalid. 
Return ONLY valid JSON with fields: sentiment_score, Aspect, effect_type.
Ensure Aspect is from the allowed list."""

# -----------------------------
# MODEL LOADING
# -----------------------------
def load_model(model_name: str):
    """Load HuggingFace model and tokenizer."""
    print(f"Loading tokenizer for {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"Loading model {model_name}...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    model.eval()
    print(f"Model loaded on: {model.device}")
    return model, tokenizer

# -----------------------------
# LLM INFERENCE
# -----------------------------
def call_llm(prompt: str, model, tokenizer) -> str:
    """Generate text using HuggingFace model."""
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.pad_token_id,
        )

    # Decode only the newly generated tokens (exclude the input prompt)
    generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
    response = tokenizer.decode(generated_ids, skip_special_tokens=True)
    return response.strip()

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
    match = re.search(r'(\d{4})-(\d{2})', date_str)
    if match:
        return f"sentiment_results_{match.group(1)}_{match.group(2)}.csv"
    return "sentiment_results.csv"

def extract_json(text: str) -> Dict[str, Any]:
    text = re.sub(r'```json\s*|```', '', text).strip()
    m = re.search(r'\{.*\}', text, flags=re.DOTALL)
    if not m: raise ValueError("No JSON found")
    return json.loads(m.group(0))

def validate_and_fix(obj: Dict[str, Any]) -> Dict[str, Any]:
    # Check Aspect
    if obj.get("Aspect") not in FACTORS_LIST:
        obj["Aspect"] = "เศรษฐกิจไทย"  # Safe default
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
    parser = argparse.ArgumentParser(description="ABSA pipeline using Llama-3.1-8B")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV file (e.g., all_news_clean.csv)")
    parser.add_argument("--output", type=str, required=True, help="Path to output directory for results")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rows to process (for testing)")
    args = parser.parse_args()

    input_csv = args.input
    output_dir = args.output
    process_limit = args.limit or PROCESS_LIMIT

    os.makedirs(output_dir, exist_ok=True)

    # Load model
    model, tokenizer = load_model(MODEL_NAME)
    print(f"Starting processing with {MODEL_NAME}...")

    # Load CSV
    rows = []
    with open(input_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
            if process_limit and len(rows) >= process_limit:
                break

    print(f"Loaded {len(rows)} rows to process.")

    for r in tqdm(rows, desc="Analyzing"):
        news_text = f"ข่าว: {r.get('summary', r.get('headline', ''))}"

        # LLM Logic with Repair Loop
        final_result = None
        current_prompt = SYSTEM_PROMPT + "\n\n" + news_text

        for attempt in range(MAX_RETRIES + 1):
            raw_response = call_llm(current_prompt, model, tokenizer)
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
        fpath = os.path.join(output_dir, fname)

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