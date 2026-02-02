import json
import re
from pathlib import Path
from datetime import datetime
import pandas as pd
from pythainlp.util import normalize


# =====================
# Config
# =====================
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "news_summary"
OUTPUT_DIR = DATA_DIR / "1_cleaned_news"
MIN_CHAR_LEN = 300

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =====================
# Utilities
# =====================
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return data

def load_csv(path):
    df = pd.read_csv(
        path,
        encoding="utf-8-sig",
        engine="python"
    )
    print("CSV columns:", df.columns.tolist())
    print(df[["published_at", "headline", "url"]].head(2).to_string(index=False))

    return df.to_dict(orient="records")

# Function to normalize and clean Thai text
def normalize_text(text):
    if not text:
        return ""

    text = normalize(str(text))
    
    text = re.sub(r"(\(*?\))", "", text)
    text = re.sub(r"(อ่านต่อทั้งหมด.*?ที่นี่)", "", text)
    text = re.sub(r"(คลิกอ่านต่อ)", "", text)
    text = re.sub(r"อ่าน.*?หนังสือพิมพ์ไทยรัฐ.*?ที่นี่", "", text)
    text = re.sub(r"ติดตามข้อมูลด้าน[\s\S]*$", "", text)
    
    text = re.sub(r"[^\w\sก-๙.]", "", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    
    return text

def parse_date(date_str):
    dt = pd.to_datetime(date_str, errors="coerce", utc=True)
    if pd.isna(dt):
        return None
    return dt.date().isoformat()

def extract_article_id(url):
    if not url:
        return None
    m = re.search(r"(\d+)$", str(url).rstrip("/"))
    return m.group(1) if m else None


# =====================
# Main cleaning pipeline
# =====================
def process_file(path):
    if path.suffix == ".json":
        records = load_json(path)
    elif path.suffix == ".csv":
        records = load_csv(path)
    else:
        return []

    cleaned = []

    for r in records:
        clean_headline = normalize_text(r.get("headline"))
        clean_content  = normalize_text(r.get("content"))

        if len(clean_content) < MIN_CHAR_LEN:
            continue

        cleaned.append({
            "agency": r.get("agency"),
            "article_id": r.get("id") or extract_article_id(r.get("url")),
            "section": r.get("section"),
            "subtype": r.get("subtype"),
            "published_at": parse_date(r.get("published_at") or r.get("published_iso") or r.get("date")),
            "headline": clean_headline,
            "content": clean_content,
            "summary": r.get("summary"),
            "url": r.get("url"),
        })

    return cleaned


def main():
    # for debug
    print("Script base dir:", BASE_DIR)
    print("CWD:", Path.cwd())
    print("INPUT_DIR exists:", INPUT_DIR.exists())
    print("Files:", list(INPUT_DIR.glob("*")))
    

    all_records = []

    for path in INPUT_DIR.glob("*"):
        if path.suffix not in [".json", ".csv"]:
            continue
        print(f"Processing {path.name}")
        all_records.extend(process_file(path))

    df = pd.DataFrame(all_records)

    df = df.drop_duplicates(subset=["url"], keep="first")
    
    df.to_csv(OUTPUT_DIR / "all_news.csv", index=False, encoding="utf-8-sig")
    df.to_json(OUTPUT_DIR / "all_news.jsonl", orient="records", lines=True, force_ascii=False)

    with open(OUTPUT_DIR / "all_news_pretty.json", "w", encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

    print(f"Saved {len(df)} cleaned articles")

if __name__ == "__main__":
    main()