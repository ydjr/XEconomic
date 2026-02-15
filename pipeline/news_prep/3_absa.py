import argparse
import csv
import json
import os
import re
import time
from tqdm import tqdm
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

import requests

OUTPUT_JSONL = "outputs_thai2/news_sentiment_summary.jsonl"
OUTPUT_JSON  = "outputs_thai2/news_sentiment_summary.json"

FACTORS = {
    "เศรษฐกิจไทย": "General macroeconomic indicators (GDP, inflation, interest rates, export/import totals).",
    "มาตรการของรัฐ": "Specific government actions, stimulus packages, subsidies, or new laws/regulations.",
    "สังคม/ความมั่นคง": "Crimes, public safety, protests, national security, and social stability issues.",
    "การเมือง": "Government stability, elections, political party movements, and internal power dynamics.",
    "ราคาสินค้าเกษตร": "Price fluctuations and production of rice, rubber, palm oil, livestock, etc.",
    "เศรษฐกิจโลก": "International trade wars, global market trends, or economic news from major partners like US, China, or EU.",
    "ภัยพิบัติ/โรคระบาด": "Natural disasters (floods, droughts), environmental issues (PM2.5), and public health crises.",
    "ราคาน้ำมันเชื้อเพลิง": "Changes in oil, gas, or electricity prices and energy policies."
}

# Create a formatted string for the prompt
FACTORS_FORMATTED = "\n".join([f"- {k}: {v}" for k, v in FACTORS.items()])

EFFECT_TYPES = ["Short-term", "Long-term"]
IMPACT_TYPES = ["Positive", "Negative", "Neutral"]


# -----------------------------
# PROMPTS
# -----------------------------
SYSTEM_PROMPT = f"""
You are an expert Thai Economic Analyst. Your task is to analyze Thai news and extract structured economic insights.

### CLASSIFICATION GUIDELINES (ASPECTS):
Choose exactly one label for 'aspects' based on these definitions:
{FACTORS_FORMATTED}

Task:
Read the provided Thai news text and output ONLY a valid JSON object that matches this schema:
{{
  "sentiment_score": number,
  "rationality": string,
  "impact_type": "Positive" | "Negative" | "Neutral",
  "effect_type": "Short-term" | "Long-term",
  "aspects": string
}}

Rules:
1) Output JSON only. No markdown. No extra text.
2) sentiment_score meaning: -1 very negative, 0 neutral, 1 very positive.
3) impact_type must align with sentiment_score:
   - score >= 0.3 => Positive
   - score <= -0.3 => Negative
   - otherwise => Neutral
4) effect_type:
   - Short-term: events that cause immediate, temporary deviations from the trend without changing the underlying economic structure.
   - Long-term: events that signal a fundamental change in the "baseline" or "social behavior" that will influence the data for an extended period.
5) 'rationality': Provide a concise (2-3 sentences) causal link. Explain *why* this news affects the chosen 'aspect' and *who* are the main stakeholders. Use Thai language for this field.
6) aspects: pick exactly one best match from:
   {", ".join(FACTORS)}
7) If unclear, choose Neutral and/or Other.
""".strip()


REPAIR_PROMPT = f"""
Your previous output was not valid JSON or did not match the schema.

Return ONLY a valid JSON object with keys:
sentiment_score, rationality, impact_type, effect_type, aspects

Constraints:
- sentiment_score is a number -1 to 1
- impact_type in {IMPACT_TYPES}
- effect_type in {EFFECT_TYPES}
- aspects in {FACTORS}

No extra text, no markdown.
""".strip()


# -----------------------------
# OLLAMA CONFIG
# -----------------------------
@dataclass
class OllamaConfig:
    url: str
    model: str
    temperature: float = 0.2
    timeout_sec: int = 120


def call_ollama(cfg: OllamaConfig, prompt: str) -> str:
    payload = {
        "model": cfg.model,
        "prompt": prompt,
        "stream": False,
        "temperature": cfg.temperature,
    }
    r = requests.post(cfg.url, json=payload, timeout=cfg.timeout_sec)
    r.raise_for_status()
    return r.json().get("response", "")


# -----------------------------
# JSON EXTRACTION + VALIDATION
# -----------------------------
def extract_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError("No JSON object found.")
    return json.loads(m.group(0))


def enforce_impact_from_score(score: float) -> str:
    if score >= 0.60:
        return "Positive"
    if score <= 0.40:
        return "Negative"
    return "Neutral"


def validate_and_fix(obj: Dict[str, Any]) -> Dict[str, Any]:
    required = ["sentiment_score", "rationality", "impact_type", "effect_type", "aspects"]
    for k in required:
        if k not in obj:
            raise ValueError(f"Missing key: {k}")

    obj["rationality"] = str(obj["rationality"]).strip()

    # sentiment_score
    try:
        score = float(obj["sentiment_score"])
    except Exception:
        score = 0.50
    score = max(0.0, min(1.0, score))
    score = round(score, 2)
    obj["sentiment_score"] = score

    # force impact_type to be consistent
    obj["impact_type"] = enforce_impact_from_score(score)

    # effect_type whitelist
    if obj["effect_type"] not in EFFECT_TYPES:
        obj["effect_type"] = "Short-term"

    # aspects whitelist
    if obj["aspects"] not in FACTORS:
        obj["aspects"] = "Other"

    return obj


def build_news_text(summary: str) -> str:
    summary = (summary or "").strip()

    max_chars = 2500
    if len(summary) > max_chars:
        summary = summary[:max_chars] + "\n[TRUNCATED]"
    return f"สรุปข่าว:\n{summary}"


# -----------------------------
# AGENT CORE
# -----------------------------
def categorize_one_news(cfg: OllamaConfig, news_text: str, max_retries: int = 2, sleep_sec: float = 0.2) -> Dict[str, Any]:
    base_prompt = SYSTEM_PROMPT + "\n\nNEWS:\n" + news_text
    raw = ""
    last_err: Optional[str] = None

    for attempt in range(max_retries + 1):
        if attempt == 0:
            raw = call_ollama(cfg, base_prompt)
        else:
            repair = base_prompt + "\n\n" + REPAIR_PROMPT
            if raw.strip():
                repair += "\n\nPrevious output:\n" + raw.strip()
            raw = call_ollama(cfg, repair)

        try:
            obj = extract_json(raw)
            obj = validate_and_fix(obj)
            time.sleep(sleep_sec)
            return obj
        except Exception as e:
            last_err = str(e)

    return {
        "sentiment_score": 0,
        "rationality": f"ระบบไม่สามารถแปลงผลลัพธ์เป็น JSON ที่ถูกต้องได้ ({last_err}).",
        "impact_type": "Neutral",
        "effect_type": "Short-term",
        "aspects": "Other",
    }


# -----------------------------
# IO HELPERS
# -----------------------------
def read_done_ids(output_jsonl: str) -> set:
    done = set()
    if not os.path.exists(output_jsonl):
        return done
    with open(output_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if "id" in obj:
                    done.add(str(obj["id"]))
            except Exception:
                continue
    return done


def append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def append_pretty_json(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(obj)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)



def read_csv_rows(csv_path: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
    rows = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        # quick check required cols
        required = ["id", "category", "subtype", "published_at", "headline", "content", "summary", "url", "CCI_pred"]
        missing = [c for c in required if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Missing columns in CSV: {missing}. Available: {reader.fieldnames}")

        for r in reader:
            rows.append(r)
            if limit is not None and len(rows) >= limit:
                break
    return rows


# -----------------------------
# MAIN
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_csv", required=True, help="Path to CSV")

    ap.add_argument("--ollama_url", default="http://localhost:11434/api/generate")
    ap.add_argument("--model", default="llama3.1:8b")
    ap.add_argument("--temperature", type=float, default=0.2)

    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--max_retries", type=int, default=2)
    ap.add_argument("--sleep_sec", type=float, default=0.2)

    args = ap.parse_args()

    cfg = OllamaConfig(
        url=args.ollama_url,
        model=args.model,
        temperature=args.temperature,
    )

    done_ids = read_done_ids(OUTPUT_JSONL)
    rows = read_csv_rows(args.input_csv, limit=args.limit)

    rows_to_process = [
        r for r in rows
        if str(r.get("CCI_pred", "")).strip() == "1"
    ]

    processed = 0
    skipped = 0
    total = len(rows)

    for i, r in enumerate(tqdm(rows_to_process, desc="LLM reasoning (CCI only)", unit="news"), start=1):
        news_id = str(r.get("id", "")).strip() or f"row_{i}"
        if news_id in done_ids:
            skipped += 1
            continue

        out_base = {
            "agency": r.get("agency"),
            "article_id": news_id,
            "section": str(r.get("section", "")).strip(),
            "subtype": str(r.get("subtype", "")).strip(),
            "published_at": str(r.get("published_at", "")).strip(),
            "headline": str(r.get("headline", "")).strip(),
            "content": str(r.get("content", "")).strip(),
            "summary": str(r.get("summary", "")).strip(),
            "url": str(r.get("url", "")).strip(),
            "CCI_pred": str(r.get("CCI_pred", "")).strip(),
        }

        news_text = build_news_text(out_base["summary"])
        result = categorize_one_news(cfg, news_text, max_retries=args.max_retries, sleep_sec=args.sleep_sec)

        append_jsonl(OUTPUT_JSONL, {**out_base, **result})
        append_pretty_json(OUTPUT_JSON, {**out_base, **result})

        processed += 1

        if processed % 10 == 0:
            print(f"Processed {processed}/{total} (skipped {skipped})")


    print(f"Done. processed={processed}, skipped={skipped}, outputs=[{OUTPUT_JSONL}, {OUTPUT_JSON}]")

if __name__ == "__main__":
    main()