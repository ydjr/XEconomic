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
import random
from collections import defaultdict

from pythainlp.tokenize import word_tokenize
from pythainlp.corpus import thai_stopwords
from wordcloud import WordCloud
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# --- paths ---
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PATH = os.path.join(ROOT, "public", "data", "news_sentiment_summary_all.csv")
OUTPUT_PATH = os.path.join(ROOT, "public", "data", "cci_impact_wordcloud.png")

# --- config ---
MIN_WORD_LEN = 3        # ข้ามคำสั้นกว่า 3 ตัวอักษร
TOP_N_WORDS = 120       # จำนวนคำสูงสุดใน word cloud

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
    # --- time/date ---
    "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.",
    "ม.ค", "ก.พ", "มี.ค", "เม.ย", "พ.ค", "มิ.ย",
    "ก.ค", "ส.ค", "ก.ย", "ต.ค", "พ.ย", "ธ.ค",
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
    "น.", "พ.ศ.", "พ.ศ", "ค.ศ.", "ค.ศ",
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
}

# regex patterns ที่ต้องกรองออก
JUNK_RE = re.compile(
    r"^[\d\.\,\:\-\/\\]+$"     # pure numbers/time
    r"|^\d+[\.,]\d+$"          # decimals (2.5, 05.55)
    r"|^[a-zA-Z]$"             # single English letter
    r"|^[ก-๙]$"                # single Thai char
    r"|^\W+$"                  # only punctuation
    r"|^\d{1,4}$"              # 1-4 digit numbers
    r"|^\d+%$"                 # percentages
    r"|^[ก-ฮ]\.$"              # single Thai char + period
)

# ---------- color palette (mockup-style) ----------
# สีหลากหลายเฉดเขียว + ม่วง + ส้ม เหมือน mockup
COLOR_PALETTE = [
    "#22c55e", "#16a34a", "#15803d", "#059669",  # green shades
    "#10b981", "#34d399", "#6ee7b7",              # emerald
    "#a855f7", "#8b5cf6", "#7c3aed",              # purple
    "#f59e0b", "#d97706", "#b45309",              # amber/orange
    "#6366f1", "#4f46e5",                          # indigo
    "#06b6d4", "#0891b2",                          # cyan
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
    """Build weighted word frequency dict — unigrams only"""
    scores = defaultdict(float)

    for row in news_rows:
        headline = row.get("headline", "")
        summary = row.get("summary", "")
        impact_type = row.get("impact_type", "Neutral")
        sentiment = row.get("sentiment_score", "0.5")

        weight = compute_weight(sentiment, impact_type)
        text = f"{headline} {summary}"

        tokens = word_tokenize(text, engine="newmm")
        for t in tokens:
            w = t.strip()
            if is_valid_token(w, stops):
                scores[w] += weight

    return scores


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
    print("⚠️  ไม่พบ Thai font")
    return None


def generate(csv_path=CSV_PATH, output_path=OUTPUT_PATH):
    print(f"📰 อ่านข่าวจาก {csv_path}")
    news = load_news(csv_path)
    print(f"   พบ {len(news)} ข่าว")

    stops = thai_stopwords() | EXTRA_STOPS

    print("🔤 ตัดคำ + คำนวณ weight...")
    scores = build_freq(news, stops)

    # top N
    top = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:TOP_N_WORDS])

    if not top:
        print("❌ ไม่พบคำ")
        return

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
