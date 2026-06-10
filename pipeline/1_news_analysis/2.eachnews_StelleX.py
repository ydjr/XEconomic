# StelleX/mt5-base
import os
import re
import pandas as pd
import torch
from tqdm.auto import tqdm
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from pythainlp.util import normalize
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import Dirs, Files


# ============ CONFIG ============
INPUT_CSV  = Files.CLEANED_NEWS_CSV
OUTPUT_CSV = Files.SUMMARIZED_NEWS_CSV

TRY_ROWS = None # for testing

MODEL_NAME = "StelleX/mt5-base-thaisum-text-summarization" 
TEXT_COL = "content"
SUMMARY_COL = "summary"

# Generation Parameters
BATCH_SIZE = 4         
SAVE_EVERY = 20         # Save progress to CSV every 20 rows
MAX_INPUT_LENGTH = 1024    
GEN_MIN_TOKENS = 100     
GEN_MAX_TOKENS = 200      
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# =================================

def clean_thai_text(text):
    if pd.isna(text) or str(text).strip() == "":
        return ""
    text = normalize(str(text))
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def load_model_and_tokenizer(model_name: str):
    print(f"Loading model: {model_name} on {DEVICE}...")
    tok = AutoTokenizer.from_pretrained(model_name)
    mdl = AutoModelForSeq2SeqLM.from_pretrained(
        model_name, 
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32
    ).to(DEVICE)
    return mdl, tok

def process_batch(model, tokenizer, texts):
    cleaned_texts = [clean_thai_text(t) for t in texts]
    inputs = tokenizer(
        cleaned_texts, 
        return_tensors="pt", 
        padding=True, 
        truncation=True, 
        max_length=MAX_INPUT_LENGTH
    ).to(DEVICE)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            min_length=GEN_MIN_TOKENS,   
            max_length=GEN_MAX_TOKENS,   
            num_beams=5,                 
            length_penalty=1.2,          
            no_repeat_ngram_size=3,      
            early_stopping=True
        )
    return [tokenizer.decode(g, skip_special_tokens=True) for g in output_ids]

def main():
    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} not found.")
        return

    df = pd.read_csv(INPUT_CSV)
    
    # check if 'summary' column exists, if not, create it
    if SUMMARY_COL not in df.columns:
        df[SUMMARY_COL] = ""
    
    # identify missing summary rows
    mask = df[SUMMARY_COL].isna() | (df[SUMMARY_COL].astype(str).str.strip() == "")
    df_todo = df[mask].copy()

    # apply TRY_ROWS limit for testing
    if TRY_ROWS is not None:
        print(f"--- TEST MODE: Only processing first {TRY_ROWS} rows ---")
        df_todo = df_todo.head(TRY_ROWS)
    
    if len(df_todo) == 0:
        print("No rows to process — all summaries already exist.")
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
        print(f"Saved {len(df)} rows (pre-existing summaries) to {OUTPUT_CSV}")
        return

    model, tokenizer = load_model_and_tokenizer(MODEL_NAME)
    
    # generate summaries in batches
    for i in tqdm(range(0, len(df_todo), BATCH_SIZE), desc="Summarizing"):
        batch_indices = df_todo.index[i : i + BATCH_SIZE]
        batch_texts = df_todo.loc[batch_indices, TEXT_COL].tolist()

        try:
            batch_summaries = process_batch(model, tokenizer, batch_texts)
            df.loc[batch_indices, SUMMARY_COL] = batch_summaries
        except Exception as e:
            print(f"Error at batch starting index {i}: {e}")
            df.loc[batch_indices, SUMMARY_COL] = "ERROR"

        # Checkpoint
        if (i + BATCH_SIZE) % SAVE_EVERY == 0:
            df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')

    # Final save
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"\nDone! Processed {len(df_todo)} rows. Results saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
