import pandas as pd
import requests
import time
import math
import sys

URL = "https://lohxkexggdpqjbxiqqyc.supabase.co"
KEY = "sb_publishable__oDI6LsirULvFLz1b4YwDA_uDI9o-d2"
TABLE = "absa_results"
CSV_PATH = "all data/2017-2026.csv"

HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates" # Upsert
}

def clean_value(v):
    if pd.isna(v):
        return None
    return str(v)

def clean_float(v):
    if pd.isna(v):
        return None
    try:
        return float(v)
    except:
        return None

def upload():
    print(f"Loading {CSV_PATH}...")
    try:
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    required_cols = ["source_file", "agency", "article_id", "section", "subtype", "published_at", "headline", "content", "summary", "url", "sentiment_score", "Aspect", "effect_type", "impact_type"]
    
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"Error: Missing columns in CSV: {missing}")
        return
    
    df = df[required_cols].copy()
    # Filter out empty article_ids
    df = df.dropna(subset=['article_id'])
    
    total_rows = len(df)
    print(f"Total rows to upload: {total_rows}")
    
    batch_size = 500
    num_batches = math.ceil(total_rows / batch_size)
    
    for i in range(num_batches):
        batch_df = df.iloc[i*batch_size : (i+1)*batch_size]
        
        payload = []
        for _, row in batch_df.iterrows():
            payload.append({
                "source_file": clean_value(row["source_file"]),
                "agency": clean_value(row["agency"]),
                "article_id": clean_value(row["article_id"]),
                "section": clean_value(row["section"]),
                "subtype": clean_value(row["subtype"]),
                "published_at": clean_value(row["published_at"]),
                "headline": clean_value(row["headline"]),
                "content": clean_value(row["content"]),
                "summary": clean_value(row["summary"]),
                "url": clean_value(row["url"]),
                "sentiment_score": clean_float(row["sentiment_score"]),
                "Aspect": clean_value(row["Aspect"]),
                "effect_type": clean_value(row["effect_type"]),
                "impact_type": clean_value(row["impact_type"]),
            })
            
        url = f"{URL}/rest/v1/{TABLE}"
        
        for attempt in range(3):
            try:
                resp = requests.post(url, json=payload, headers=HEADERS, timeout=60)
                if resp.status_code in (201, 200, 204):
                    print(f"Uploaded batch {i+1}/{num_batches} ({(i+1)*batch_size}/{total_rows})")
                    break
                else:
                    print(f"Error uploading batch {i+1} attempt {attempt+1}: {resp.status_code} - {resp.text}")
                    if attempt == 2:
                        print("Failed after 3 attempts.")
                    time.sleep(5)
            except Exception as e:
                print(f"Exception uploading batch {i+1} attempt {attempt+1}: {e}")
                time.sleep(5)

if __name__ == "__main__":
    upload()
