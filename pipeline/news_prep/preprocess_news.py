import json
import re
from pathlib import Path
from datetime import datetime
import pandas as pd
from pythainlp.util import normalize


# =====================
# Config
# =====================
BASE_DIR = Path(r"D:\ICT\senior_project\code\datapreprocessing")
INPUT_FILE = BASE_DIR / "All3econnewsRAW.csv"
OUTPUT_FILE = BASE_DIR / "All3econnews2017_2026cleaned.csv"
MIN_CHAR_LEN = 300


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
    
    # text = re.sub(r"(\(*?\))", "", text)
    text = re.sub(r"(อ่านต่อทั้งหมด.*?ที่นี่)", "", text)
    text = re.sub(r"(คลิกอ่านต่อ)", "", text)
    text = re.sub(r"อ่าน.*?หนังสือพิมพ์ไทยรัฐ.*?ที่นี่", "", text)
    text = re.sub(r"ติดตามข้อมูลด้าน[\s\S]*$", "", text)
    
    # text = re.sub(r"[^\w\sก-๙.]", "", text)
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
            "source_file": path.name,
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
    print("INPUT_FILE exists:", INPUT_FILE.exists())
    print("Input file:", INPUT_FILE)

    all_records = []

    print(f"Processing {INPUT_FILE.name}")
    all_records.extend(process_file(INPUT_FILE))

    df = pd.DataFrame(all_records)

    df = df.drop_duplicates(subset=["url"], keep="first")
    
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"Saved {len(df)} cleaned articles to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()