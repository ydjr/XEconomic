"""
Extract top entities (PEOPLE & GROUPS) from news CSV.

Focuses on:
  - Person names (detected by prefix นาย/นาง/นางสาว + name token)
  - Known politicians/officials
  - Government bodies & committees (กนง., ครม., ธปท. etc.)
  - People groups (เกษตรกร, ผู้ค้า, ลูกหนี้ etc.)

Usage:
    python pipeline/extract_entities.py

Output:
    public/data/top_entities.json
"""

import os
import csv
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

from pythainlp.tokenize import word_tokenize

# --- resolve project root & import config ---
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import Files, Pipeline

# Windows console (cp874) can't encode the emoji used in progress prints
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --- paths ---
CSV_PATH = str(Files.ABSA_NEWS_CSV)
OUTPUT_PATH = str(Files.TOP_ENTITIES_JSON)

TOP_N = Pipeline.ENTITY_TOP_N
MIN_FREQ = Pipeline.ENTITY_MIN_FREQ

# --- KNOWN PERSON NAMES in Thai economic/political news ---
KNOWN_PERSONS = {
    # นักการเมือง/ผู้บริหาร
    "พิชัย", "เศรษฐา", "แพทองธาร", "ประยุทธ์", "ประวิตร",
    "อนุทิน", "สุริยะ", "จุลพันธ์", "ทักษิณ", "เผ่าภูมิ",
    "สุพัฒนพงษ์", "อาคม", "อรรถวิชช์", "ศิริกัญญา",
    "ชัชชาติ", "พิธา", "กรณ์",
    # ผู้ว่าการ ธปท. / กนง.
    "เศรษฐพุฒิ", "วิรไท", "ประสาร", "ธาริษา",
    "เกียรติพงศ์", "รุ่ง", "สักกะภพ",
    # ธุรกิจ
    "ธนินท์", "เจริญ", "สารัชถ์", "ศุภชัย",
}

# --- KNOWN GROUPS/ORGANIZATIONS (actors, not concepts) ---
KNOWN_GROUPS = {
    # สถาบันที่เป็น "ตัวละคร"
    "ธปท.": "ธปท.",
    "ธปท": "ธปท.",
    "ธนาคารแห่งประเทศไทย": "ธปท.",
    "BOT": "ธปท.",
    "กนง.": "กนง.",
    "กนง": "กนง.",
    "MPC": "กนง.",
    "ครม.": "ครม.",
    "ครม": "ครม.",
    "คณะรัฐมนตรี": "ครม.",
    "สศช.": "สภาพัฒน์",
    "สศช": "สภาพัฒน์",
    "สภาพัฒน์": "สภาพัฒน์",
    "สนค.": "สนค.",
    "สนค": "สนค.",
    "กระทรวงการคลัง": "กระทรวงการคลัง",
    "คลัง": "กระทรวงการคลัง",
    "กระทรวงพาณิชย์": "กระทรวงพาณิชย์",
    "กระทรวงพลังงาน": "กระทรวงพลังงาน",
    "ก.ล.ต.": "ก.ล.ต.",
    "ส.อ.ท.": "ส.อ.ท.",
    "SET": "SET",
    "ตลาดหลักทรัพย์": "SET",
    "BOI": "BOI",
    "Fed": "Fed",
    "เฟด": "Fed",
    "IMF": "IMF",
    "ECB": "ECB",
    "OPEC": "OPEC",
    "โอเปก": "OPEC",
    "ธนาคารโลก": "ธนาคารโลก",
    "ธนาคารกลาง": "ธนาคารกลาง",
    "สคร.": "สคร.",
    "บสย.": "บสย.",
    "สสว.": "สสว.",
    "กรมสรรพากร": "กรมสรรพากร",
    "กรมศุลกากร": "กรมศุลกากร",
    "กรมการค้าภายใน": "กรมการค้าภายใน",
    "สภาอุตสาหกรรม": "ส.อ.ท.",
}

# --- PEOPLE GROUPS (กลุ่มคนที่เป็น "ตัวละคร") ---
PEOPLE_GROUPS = {
    "เกษตรกร", "ผู้ค้า", "ผู้ส่งออก", "ผู้นำเข้า",
    "ลูกหนี้", "เจ้าหนี้", "ผู้ประกอบการ", "นักลงทุน",
    "ผู้บริโภค", "ประชาชน", "ชาวนา", "ชาวสวน",
    "สหกรณ์", "แรงงาน", "ผู้มีรายได้น้อย",
    "นายจ้าง", "ลูกจ้าง", "พ่อค้า", "แม่ค้า",
    "ผู้ซื้อ", "ผู้ขาย", "ผู้เช่า",
    "SME", "SMEs", "เอสเอ็มอี",
    "นักท่องเที่ยว", "ผู้โดยสาร",
}

# prefixes ที่ใช้นำหน้าชื่อคน
PERSON_PREFIXES = {"นาย", "นาง", "นางสาว", "ดร.", "ศ.", "ผศ.", "รศ."}
# title prefixes
TITLE_PREFIXES = {
    "นายก", "นายกฯ", "นายกรัฐมนตรี",
    "รัฐมนตรี", "รัฐมนตรีว่าการ", "รองนายก",
    "ผู้ว่า", "ผู้ว่าการ", "ผู้ว่าฯ",
    "ปลัด", "อธิบดี", "เลขาธิการ",
    "ประธาน", "รองประธาน",
}


def load_news(csv_path):
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def extract_people_and_groups(text):
    """Extract person names and groups from text"""
    tokens = word_tokenize(text, engine="newmm")
    found = []

    for i, tok in enumerate(tokens):
        t = tok.strip()
        if not t:
            continue

        # 1. Check known groups/organizations
        if t in KNOWN_GROUPS:
            found.append(("group", KNOWN_GROUPS[t]))
            continue

        # 2. Check people groups
        if t in PEOPLE_GROUPS:
            found.append(("people_group", t))
            continue

        # 3. Check known persons
        if t in KNOWN_PERSONS:
            # try to get full name: prefix + firstName (+ optional lastName)
            # look backward for prefix
            prefix = ""
            if i > 0 and tokens[i-1].strip() in PERSON_PREFIXES:
                prefix = tokens[i-1].strip()
            found.append(("person", f"{prefix}{t}" if prefix else t))
            continue

        # 4. Detect unknown persons by prefix pattern: นาย/นาง/นางสาว + name
        if t in PERSON_PREFIXES and i + 1 < len(tokens):
            next_tok = tokens[i+1].strip()
            # name should be Thai text, at least 2 chars, not a stopword
            if (len(next_tok) >= 2
                    and next_tok not in PERSON_PREFIXES
                    and next_tok not in TITLE_PREFIXES
                    and not next_tok.isdigit()
                    and any(c.isalpha() for c in next_tok)):
                full = f"{t}{next_tok}"
                found.append(("person", full))
                continue

        # 5. Detect titles: รัฐมนตรี, ผู้ว่า etc. 
        if t in TITLE_PREFIXES:
            found.append(("title", t))
            continue

    return found


def build_entity_freq(news_rows):
    """Count entities across all news"""
    # merge duplicates
    NORMALIZE_NAMES = {
        "SME": "SMEs", "เอสเอ็มอี": "SMEs",
        "นายกรัฐมนตรี": "นายกฯ", "นายก": "นายกฯ",
        "ผู้ว่า": "ผู้ว่าฯ ธปท.", "ผู้ว่าการ": "ผู้ว่าฯ ธปท.", "ผู้ว่าฯ": "ผู้ว่าฯ ธปท.",
        "นายเศรษฐา": "เศรษฐา", "นายพิชัย": "พิชัย", "นายสุริยะ": "สุริยะ",
        "ประธาน": None,  # skip generic title
        "รัฐมนตรี": None,
        "นายพี": None,  # noise from tokenizer
    }

    counts = defaultdict(int)

    for row in news_rows:
        headline = row.get("headline", "")
        summary = row.get("summary", "")
        text = f"{headline} {summary}"

        entities = extract_people_and_groups(text)

        # deduplicate within same news
        seen = set()
        for etype, name in entities:
            norm = NORMALIZE_NAMES.get(name, name)
            if norm is None:
                continue  # skip generic titles
            if norm not in seen and len(norm) >= 2:
                seen.add(norm)
                counts[norm] += 1

    return counts


def main():
    print(f"📰 อ่านข่าวจาก {CSV_PATH}")
    news = load_news(CSV_PATH)
    print(f"   พบ {len(news)} ข่าว")

    print("🔍 กำลังดึง บุคคล/กลุ่มคน/องค์กร...")
    counts = build_entity_freq(news)

    # filter by min frequency
    filtered = {k: v for k, v in counts.items() if v >= MIN_FREQ}

    # sort and take top N
    top = sorted(filtered.items(), key=lambda x: -x[1])[:TOP_N]

    result = [{"name": name, "count": count} for name, count in top]

    # save JSON
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ บันทึก {len(result)} entities ที่: {OUTPUT_PATH}")
    print(f"\n📊 Top 20:")
    for i, item in enumerate(result[:20], 1):
        print(f"   {i:2d}. {item['name']:25s}  count={item['count']}")


if __name__ == "__main__":
    main()
