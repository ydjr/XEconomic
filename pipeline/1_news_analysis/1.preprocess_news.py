import json
import re
from pathlib import Path
from datetime import datetime
import pandas as pd
from pythainlp.util import normalize
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import Dirs, Files, Pipeline



# =====================
# Config
# =====================
BASE_DIR = Dirs.PIPELINE_DATA
INPUT_FILE = Files.RAW_NEWS_CSV
OUTPUT_FILE = Files.CLEANED_NEWS_CSV
MIN_CHAR_LEN = Pipeline.MIN_CONTENT_LEN


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

    # Month-completeness gate: only let articles through whose month has fully
    # ended. The current in-progress month is held back until we roll over —
    # this keeps ABSA and downstream summaries from spending LLM cycles on a
    # partial month that will look different once it's complete.
    today = pd.Timestamp.today().normalize()
    current_month_start = today.replace(day=1).date().isoformat()
    before = len(df)
    df = df[df["published_at"].notna() & (df["published_at"] < current_month_start)]
    dropped = before - len(df)
    if dropped > 0:
        print(f"  [gate] Held back {dropped} articles from {current_month_start[:7]} or later — "
              f"waiting for the current month to finish")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"Saved {len(df)} cleaned articles to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
