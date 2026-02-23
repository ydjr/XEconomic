import numpy as np
import pandas as pd
import torch
from pathlib import Path
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# =====================
# CONFIG
# =====================
MODEL_DIR = "../wangchanberta_cls/best_model"
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
INPUT_CSV = DATA_DIR /  "1_cleaned_news/all_news.csv"
OUTPUT_CSV = DATA_DIR / "2_news_cci_r.csv"

TEXT_COL = "summary"
MAX_LENGTH = 512
BATCH_SIZE = 16

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# =====================
# LOAD MODEL
# =====================
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, use_fast=True)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
model.to(DEVICE)
model.eval()

# =====================
# LOAD DATA
# =====================
df = pd.read_csv(INPUT_CSV)

# keep original text; make a safe version for tokenization
texts = df[TEXT_COL].astype(str).fillna("").str.strip().tolist()

all_preds = []
all_prob1 = []

# =====================
# INFERENCE
# =====================
with torch.no_grad():
    for i in tqdm(
        range(0, len(texts), BATCH_SIZE),
        desc="Running CCI classification",
        unit="batch"
    ):
        batch = texts[i:i+BATCH_SIZE]

        enc = tokenizer(
            batch,
            truncation=True,
            max_length=MAX_LENGTH,
            padding=True,
            return_tensors="pt"
        ).to(DEVICE)

        logits = model(**enc).logits
        probs = torch.softmax(logits, dim=-1).cpu().numpy()

        pred = np.argmax(probs, axis=1)
        prob1 = probs[:, 1]

        all_preds.extend(pred.tolist())
        all_prob1.extend(prob1.tolist())


# =====================
# SAVE RESULTS
# =====================
df["CCI_pred"] = all_preds
df["CCI_prob1"] = all_prob1

df.to_csv(OUTPUT_CSV, index=False)
print("Saved:", OUTPUT_CSV)

# count the relevance news
df = pd.read_csv(OUTPUT_CSV)

counts = df["CCI_pred"].value_counts().sort_index()
ratios = df["CCI_pred"].value_counts(normalize=True).sort_index()

print("Predicted counts:")
print(counts)

print("\nPredicted ratios:")
print(ratios)

