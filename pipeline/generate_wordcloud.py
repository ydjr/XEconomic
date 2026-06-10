"""
Generate a CCI-impact word cloud from news_sentiment_summary_all.csv

Usage:
    python pipeline/generate_wordcloud.py

Output:
    public/data/cci_impact_wordcloud.png
"""

import os
import re
import csv
import sys
import json
import random
from pathlib import Path
from collections import defaultdict

from pythainlp.tokenize import word_tokenize
from pythainlp.corpus import thai_stopwords
from wordcloud import WordCloud
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
OUTPUT_PATH = str(Files.WORDCLOUD_PNG)
JSON_OUTPUT_PATH = str(Files.WORDCLOUD_JSON)

# how many sample headlines to keep per word (for the hover tooltip)
SAMPLE_CAP = 5

# --- config ---
MIN_WORD_LEN = Pipeline.WORDCLOUD_MIN_WORD_LEN
TOP_N_WORDS = Pipeline.WORDCLOUD_TOP_N

# ---------- stopwords ----------
# รวม pythainlp default + custom ทั้งหมด
EXTRA_STOPS = {
    # --- function words ---
    "ที่", "ใน", "จะ", "ได้", "ของ", "มี", "ให้", "เป็น", "กับ", "จาก",
    "และ", "แต่", "หรือ", "ว่า", "ไม่", "ก็", "อยู่", "ขึ้น", "ลง", "แล้ว",
    "ยัง", "ถูก", "ทำ", "ด้วย", "เข้า", "ออก", "มา", "ไป", "เรื่อง", "อีก",
    "กัน", "นี้", "นั้น", "บาง", "ทุก", "ต่อ", "รวม", "ซึ่ง", "ดัง", "โดย",
    "การ", "ความ", "อย่าง", "คือ", "พบ", "หลัง", "ก่อน", "เมื่อ", "ตั้งแต่",
    "ผู้", "คน", "ราย", "กรณี", "ส่วน", "ด้าน", "ระบุ", "เผย", "กล่าว",
    "สำหรับ", "เกี่ยว", "เพื่อ", "อาจ", "ต้อง", "ควร", "ถึง", "ระหว่าง",
    "พร้อม", "ตาม", "ผ่าน", "ช่วง", "ทั้ง", "หาก", "ขณะ", "เพราะ",
    "สามารถ", "ส่ง", "มาก", "น้อย", "ปี", "เดือน", "วัน", "ครั้ง",
    "ท่า", "แห่ง", "ล่าสุด", "เพิ่ม", "ลด", "สูง", "ต่ำ",
    "ต่อเนื่อง", "เป็นต้น", "ขณะที่", "อย่างไรก็ตาม", "ดังนั้น",
    "แม้", "แม้ว่า", "เนื่องจาก", "ทั้งนี้", "ฯ", "เช่น", "อาทิ",
    "นอกจาก", "อีกทั้ง", "รวมถึง", "เฉพาะ", "เริ่ม", "เริ่มต้น",
    # --- generic verbs/adj ---
    "ดำเนินการ", "จัดทำ", "ประกอบ", "ประมาณ", "ราว", "ประมาณการ",
    "คาดว่า", "คาดการณ์", "เปิดเผย", "ชี้", "ระบุว่า", "เปิดเผยว่า",
    "มองว่า", "เชื่อว่า", "แจ้ง", "แถลง", "ยืนยัน", "เสนอ",
    "ประกาศ", "สนับสนุน", "พัฒนา", "ดูแล", "จัดการ", "บริหาร",
    "เกิด", "เกิดขึ้น", "รับ", "ใช้", "ปรับ", "ปรับตัว",
    "อัตรา", "จำนวน", "ระดับ", "แนวโน้ม", "สถานการณ์", "ภาพรวม",
    "สาเหตุ", "ผลกระทบ", "ปัจจัย", "กรอบ", "มาตรการ",
    "เพิ่มขึ้น", "ลดลง", "ปรับเพิ่ม", "ปรับลด", "เพิ่มเติม",
    "ต่อไป", "ต่อมา", "ก่อนหน้า", "ถัดไป", "ล่า",
    "ครึ่ง", "รอบ", "ต้น", "ปลาย", "กลาง",
    "ฟื้น", "ฟื้นตัว", "หนุน", "คาด", "แข็ง", "อ่อน",
    "ดัน", "กดดัน", "จ่อ", "โอกาส", "หวัง", "มุ่ง",
    "เร่ง", "รุก", "ลุ้น", "ชะลอ", "ชะลอตัว", "ส่อ",
    "ยอด", "แรง", "หนัก", "เต็ม", "ร่วม", "พุ่ง",
    # --- short meaningless ---
    "จีน", "ลิ", "วอ", "แนะ", "ศูนย์", "หวั่น", "แผน",
    "วัน", "ที", "ทุน", "แก้", "วา", "ดึง", "หั่น",
    "ตั้ง", "วาง", "ย้ำ", "ห่วง", "ชี้", "เตือน",
    "ถก", "เล็ง", "หา", "จัด", "ลง", "รอ",
    "เปิด", "ปิด", "ตก", "ขยาย", "ชง", "จ่า", "ขาด",
    "ชัด", "อ้าง", "เรียก", "บุก", "ฝ่า",
    "เวลา", "เงื่อนไข", "ข้อมูล", "รูปแบบ", "กำหนด",
    "ผลิต", "บริการ", "เตรียม", "เดิน", "หน้า", "เดินหน้า",
    "กระทบ", "กระตุ้น", "ขยายตัว", "คำ", "สั่ง", "ค่า",
    "ผ่อน", "ตลาด", "ประเทศ",
    # --- time/date/numbers generic ---
    "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.",
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
    "น.", "พ.ศ.", "ค.ศ.", "วันนี้", "พรุ่งนี้", "เมื่อวาน", "ปีนี้", "ปีหน้า",
    # --- person names / titles ---
    "พิชัย", "เศรษฐา", "แพทองธาร", "ประยุทธ์", "ประวิตร",
    "อนุทิน", "สุริยะ", "จุลพันธ์", "เสี่ยตัน", "ทักษิณ",
    "เผ่าภูมิ", "จุฬา", "อมรรัตน์", "นฤมล", "สุพัฒน์พงษ์",
    "นายก", "นายกฯ", "รัฐมนตรี", "ผู้ว่า", "ผู้ว่าการ", "เลขาธิการ",
    "ปลัด", "อธิบดี", "รองนายก", "ว่าการ",
    "นาย", "นาง", "นางสาว", "ดร.", "ศ.", "ผศ.", "รศ.",
    # --- single chars / abbreviations ---
    "พี", "ที", "ซี", "เอ", "บี", "ดี", "จี", "เค", "เอส",
    "กก.", "กม.", "ลบ.", "บ.", "จ.", "อ.", "ต.", "ม.",
    # --- agency abbreviations ---
    "ธ.พ.", "ธปท.", "ธปท", "สศช.", "สศช", "สนค.", "กนง.", "กนง",
    "ส.อ.ท.", "ก.ล.ต.", "สคร.", "บสย.", "สสว.",
    # --- media ---
    "ไทยรัฐ", "ThaiPBS", "thaipbs", "ไทยพีบีเอส",
    # --- highly generic stock/finance words we want to filter out to show pure impact topics ---
    "บาท", "ไทย", "ล้าน", "จุด", "ราคา", "ดัชนี", "มูลค่า", "ขาย", "ซื้อ", "เงิน", "การซื้อขาย", 
    "บริษัท", "รายได้", "บ่าย", "เช้า", "โครงการ", "ตลาดหุ้น", "หุ้น", "ธุรกิจ", "นักลงทุน", "กำไร", "ลงทุน", "ไตรมาส",
    "หมื่น", "แสน", "พัน", "ร้อย", "เปอร์เซ็นต์", "ร้อยละ", "คาด", "เพิ่ม", "ลด", "ต่อ",
    "อย่า", "ที่จะ", "จอง", "โชว์", "ยัน", "สาย"
}

# regex patterns ที่ต้องกรองออก
JUNK_RE = re.compile(
    r"^[\d\.\,\:\-\/\\]+$"     # pure numbers/time
    r"|^\d+[\.,]\d+$"          # decimals (2.5, 05.55)
    r"|^[a-zA-Z]$"             # single English letter
    r"|^[ก-๙]$"                # single Thai char
    r"|^\W+$"                  # only punctuation
    r"|^\d+.*"                 # starts with numbers and has stuff
    r"|.*%$"                   # ends with percent
)

# ---------- color palette (mockup-style) ----------
# สีหลากหลายเฉดเขียว + ม่วง + ส้ม เหมือน mockup
COLOR_PALETTE = [
    "#22c55e", "#16a34a", "#15803d", "#059669",  # green shades
    "#10b981", "#34d399", "#6ee7b7",             # emerald
    "#a855f7", "#8b5cf6", "#7c3aed",             # purple
    "#f59e0b", "#d97706", "#b45309",             # amber/orange
    "#6366f1", "#4f46e5",                        # indigo
    "#06b6d4", "#0891b2",                        # cyan
]

def _random_color_func(word, **kwargs):
    return random.choice(COLOR_PALETTE)

# ---------- functions ----------

def load_news(csv_path):
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows

def compute_weight(sentiment_str, impact_type):
    """Weight = how far from neutral × impact direction boost"""
    try:
        score = float(sentiment_str)
    except (ValueError, TypeError):
        score = 0.5
    w = abs(score - 0.5) * 2
    if impact_type in ("Positive", "Negative") and w < 0.3:
        w = 0.3
    return w

def is_valid_token(w, stops):
    """Check if a token is valid for the word cloud"""
    if len(w) < MIN_WORD_LEN:
        return False
    if w in stops:
        return False
    # skip english short words
    if w.isascii() and len(w) < 4:
        return False
    if w.isdigit():
        return False
    if JUNK_RE.match(w):
        return False
    # skip tokens that are mostly non-alpha (punctuation, digits)
    alpha_count = sum(1 for c in w if c.isalpha())
    if alpha_count < len(w) * 0.6:
        return False
    return True


def build_freq(news_rows, stops):
    """Build weighted word frequency dict + per-word metadata.

    Returns (freq, meta):
      freq — {word: weighted score}, used to size the cloud. Primary weight
             is sentiment intensity (per token occurrence). If every article
             is neutral (e.g. ABSA fell back to defaults), all weights
             collapse to zero — in that case fall back to article counts so
             the cloud still renders instead of crashing on a
             divide-by-zero in WordCloud.generate_from_frequencies().
      meta — per-word counts / positive / negative / sample headlines,
             used by _export_word_json() for the interactive hover tooltip.
    """
    scores = defaultdict(float)
    counts = defaultdict(int)            # number of articles a word appears in
    pos = defaultdict(int)
    neg = defaultdict(int)
    samples = defaultdict(list)

    for row in news_rows:
        headline = (row.get("headline") or "").strip()
        summary = row.get("summary", "")
        impact_type = row.get("impact_type", "Neutral")
        sentiment = row.get("sentiment_score", "0.5")

        weight = compute_weight(sentiment, impact_type)
        text = f"{headline} {summary}"

        tokens = word_tokenize(text, engine="newmm")
        seen = set()  # so per-article metadata counts each word once
        for t in tokens:
            w = t.strip()
            if not is_valid_token(w, stops):
                continue
            scores[w] += weight                 # per-occurrence — unchanged
            if w not in seen:                   # per-article metadata
                seen.add(w)
                counts[w] += 1
                if impact_type == "Positive":
                    pos[w] += 1
                elif impact_type == "Negative":
                    neg[w] += 1
                if (headline and len(samples[w]) < SAMPLE_CAP
                        and headline not in samples[w]):
                    samples[w].append(headline)

    meta = {"counts": counts, "pos": pos, "neg": neg, "samples": samples}

    if not scores or max(scores.values()) <= 0:
        print("  [warn] sentiment weights are all zero "
              "(ABSA likely produced only neutral scores) "
              "- falling back to word frequency")
        return counts, meta

    return scores, meta


def _export_word_json(top, meta):
    """Write per-word data the dashboard uses for the interactive
    (hover-tooltip) word cloud — score, occurrence count, positive/negative
    split, and a few sample headlines per word."""
    counts  = meta["counts"]
    pos     = meta["pos"]
    neg     = meta["neg"]
    samples = meta["samples"]

    max_score = max(top.values()) or 1.0
    words = []
    for w, score in sorted(top.items(), key=lambda x: -x[1]):
        words.append({
            "word":     w,
            "score":    round(float(score), 2),
            "weight":   round(float(score) / max_score, 4),  # 0..1 for font sizing
            "count":    int(counts.get(w, 0)),
            "positive": int(pos.get(w, 0)),
            "negative": int(neg.get(w, 0)),
            "samples":  samples.get(w, [])[:SAMPLE_CAP],
        })

    out = Path(JSON_OUTPUT_PATH)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(words, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] word data JSON: {out}  ({len(words)} words)")


def _find_thai_font():
    candidates = [
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/THSarabunNew.ttf",
        "C:/Windows/Fonts/cordia.ttc",
        "C:/Windows/Fonts/angsana.ttc",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/tlwg/TlwgTypo.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansThai-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p

    # Fallback: scan common Linux font dirs. On Kaggle the pipeline installs
    # fonts-thai-tlwg, which drops Garuda/Norasi/Loma/... under tlwg/.
    import glob
    for pattern in [
        "/usr/share/fonts/truetype/tlwg/*.ttf",
        "/usr/share/fonts/**/Noto*Thai*.ttf",
        "/usr/share/fonts/**/*[Tt]hai*.ttf",
    ]:
        hits = sorted(glob.glob(pattern, recursive=True))
        if hits:
            return hits[0]

    print("[WARN] no Thai font found - Thai text may render as boxes")
    return None


def generate(csv_path=CSV_PATH, output_path=OUTPUT_PATH):
    print(f"📰 อ่านข่าวจาก {csv_path}")
    news = load_news(csv_path)
    print(f"   พบ {len(news)} ข่าว")

    stops = thai_stopwords() | EXTRA_STOPS

    print("🔤 ตัดคำ + คำนวณ weight...")
    scores, meta = build_freq(news, stops)

    # top N
    top = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:TOP_N_WORDS])

    if not top:
        print("❌ ไม่พบคำ")
        return

    # per-word data for the interactive (hover) word cloud on the dashboard
    _export_word_json(top, meta)

    print(f"☁️  สร้าง word cloud ({len(top)} คำ)...")

    wc = WordCloud(
        font_path=_find_thai_font(),
        width=1200,
        height=600,
        background_color="white",
        max_words=TOP_N_WORDS,
        color_func=_random_color_func,
        prefer_horizontal=0.75,
        margin=8,
        min_font_size=12,
        max_font_size=180,
        relative_scaling=0.6,
    )
    wc.generate_from_frequencies(top)

    # save — no title, clean image like the mockup
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, ax = plt.subplots(1, 1, figsize=(14, 7))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    fig.tight_layout(pad=0)
    fig.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor="white", pad_inches=0.05)
    plt.close(fig)

    print(f"✅ บันทึกที่: {output_path}")
    # print top 20 for debugging
    print("\n📊 Top 20 คำ:")
    for i, (w, s) in enumerate(sorted(top.items(), key=lambda x: -x[1])[:20], 1):
        print(f"   {i:2d}. {w:20s}  score={s:.2f}")


if __name__ == "__main__":
    generate()
