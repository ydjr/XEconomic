import sys
import numpy as np
import pandas as pd
import torch
from pathlib import Path
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ─── resolve project root & import config ───
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from config import Dirs, Files, WangchanBERTa as WBCfg

# =====================
# CONFIG
# =====================
# Resolve model directory: check primary -> legacy -> HuggingFace base
def resolve_model_dir():
    if WBCfg.MODEL_DIR.exists():
        print(f"Using model: {WBCfg.MODEL_DIR}")
        return str(WBCfg.MODEL_DIR)
    if WBCfg.MODEL_DIR_LEGACY.exists():
        print(f"Using legacy model: {WBCfg.MODEL_DIR_LEGACY}")
        return str(WBCfg.MODEL_DIR_LEGACY)
    print(f"[!] Fine-tuned model not found. Using HuggingFace base: {WBCfg.HF_BASE_MODEL}")
    print(f"    (For best results, place fine-tuned model at: {WBCfg.MODEL_DIR})")
    return WBCfg.HF_BASE_MODEL

MODEL_DIR  = resolve_model_dir()
INPUT_CSV  = Files.CLEANED_NEWS_CSV
OUTPUT_CSV = Files.RELEVANCE_CSV

TEXT_COL   = "summary"
MAX_LENGTH = WBCfg.MAX_LENGTH
BATCH_SIZE = WBCfg.BATCH_SIZE

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

