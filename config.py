"""
XEconomic — Central Configuration
==================================
All paths, settings, and constants used across the project.
Every script should import from here instead of hardcoding paths.

Usage:
    from config import cfg
    print(cfg.DATA_DIR)
"""

import os
import re
import time
from pathlib import Path

# ─────────────────────────────────────────────
# PROJECT ROOT  (this file lives at project root)
# ─────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent

# ─────────────────────────────────────────────
# KAGGLE WORKSPACE ISOLATION
# ─────────────────────────────────────────────
# When KAGGLE_ENV=1 is set (e.g. in Kaggle Secrets), all mutable data paths
# redirect to kaggle_workspace/ so the original web files stay untouched.
_KAGGLE_MODE = os.getenv("KAGGLE_ENV", "").strip() in ("1", "true", "True")
WORKSPACE = ROOT / "kaggle_workspace" if _KAGGLE_MODE else ROOT


# ─────────────────────────────────────────────
# DIRECTORY STRUCTURE
# ─────────────────────────────────────────────
class Dirs:
    ROOT        = ROOT
    WORKSPACE   = WORKSPACE  # ROOT or ROOT/kaggle_workspace depending on KAGGLE_ENV

    # --- Mutable directories (redirect to WORKSPACE in Kaggle mode) ---
    DATA        = WORKSPACE / "data"
    INDICATORS  = WORKSPACE / "public" / "data" / "indicators"
    ABSA_FEAT   = WORKSPACE / "data" / "4_absa_features"
    ARTIFACTS   = WORKSPACE / "artifacts"
    BACKTEST_ART = WORKSPACE / "artifacts" / "backtest"
    MODELS      = WORKSPACE / "models"
    BACKTEST_MDL = WORKSPACE / "models" / "backtest"
    PUBLIC      = WORKSPACE / "public"
    PUBLIC_DATA = WORKSPACE / "public" / "data"
    LOGS        = WORKSPACE / "logs"

    # --- Immutable directories (always read from project root) ---
    PIPELINE    = ROOT / "pipeline"
    NEWS_ANALYSIS   = PIPELINE / "1_news_analysis"
    NEWS_PREP   = PIPELINE / "news_prep"
    FORECASTING     = PIPELINE / "2_forecasting"
    EXPLAINABLE_AI  = PIPELINE / "3_explainable_ai"
    NEWS_SUM    = PIPELINE / "data" / "news_sum"
    CLEANED_NEWS = PIPELINE / "data" / "1_cleaned_news"
    PIPELINE_DATA = PIPELINE / "data"

    EXPLAINABLE = ROOT / "explainable"
    EXPLAINABLE_OUT = WORKSPACE / "artifacts" / "explainable"
    SHAP_DIR    = EXPLAINABLE_OUT / "shap"
    SHAP_RESULT = EXPLAINABLE_OUT / "shap" / "shap_result"
    REASONING   = EXPLAINABLE_OUT / "reasoning"
    TEXT_SUM    = EXPLAINABLE_OUT / "text_summarization"

    DASHBOARD      = ROOT / "dashboard"
    DASHBOARD_SRC  = ROOT / "dashboard" / "src"
    DASHBOARD_DATA = WORKSPACE / "artifacts"   # reasoning JSON / forecast outputs read by API
    API            = ROOT / "api"


# ─────────────────────────────────────────────
# KEY DATA FILES
# ─────────────────────────────────────────────
class Files:
    # Indicators
    CCI_CSV           = Dirs.INDICATORS / "cci.csv"
    CCI_UTCC_CSV      = Dirs.INDICATORS / "cci_utcc.csv"  # auto-fetched from UTCC (separate from cci.csv)
    CPI_CSV           = Dirs.INDICATORS / "cpi.csv"
    GDP_CSV           = Dirs.INDICATORS / "gdp_monthly.csv"
    POLICY_RATE_CSV   = Dirs.INDICATORS / "policy_rate.csv"
    UNEMPLOYMENT_CSV  = Dirs.INDICATORS / "unemployment_rate.csv"
    IMPI_CSV          = Dirs.INDICATORS / "impi.csv"
    EXPI_CSV          = Dirs.INDICATORS / "expi.csv"

    # Combined dataset for training
    AVG_SENT_INDI     = Dirs.DATA / "avg_sent_indi.csv"
    FULL_NEWS_CSV     = Dirs.DATA / "2017-2026.csv"   # alias kept for env-check display
    ABSA_NEWS_CSV     = Dirs.DATA / "2017-2026.csv"   # master ABSA file (scripts 3/4/7)
    ASPECT_FEATURES   = Dirs.ABSA_FEAT / "aspect_monthly_features.csv"

    # Pipeline intermediates (Standardized for seamless data flow)
    RAW_NEWS_CSV        = Dirs.NEWS_SUM / "All3econnewsRAW.csv"
    CLEANED_NEWS_CSV    = Dirs.CLEANED_NEWS / "All3econnews2017_2026cleaned.csv"
    SUMMARIZED_NEWS_CSV = Dirs.CLEANED_NEWS / "All3econnews2017_2026_full_sum.csv"
    
    # 3_explainable outputs
    MONTHLY_SUMMARY_CSV = Dirs.TEXT_SUM / "monthly_summary.csv"
    SUMMARY_3M_CSV      = Dirs.TEXT_SUM / "3m_summary.csv"

    RELEVANCE_CSV     = Dirs.PIPELINE_DATA / "2_news_cci_r.csv"
    ABSA_OUTPUT_DIR   = Dirs.PIPELINE_DATA  # legacy path if needed

    # Model artifacts
    BEST_OVERALL_JSON = Dirs.BACKTEST_MDL / "best_overall.json"
    XGB_BEST_PARAMS   = Dirs.BACKTEST_ART / "xgb_best_params.json"
    XGB_WEIGHTS       = Dirs.BACKTEST_MDL / "xgb_weights.pkl"

    # Prediction artifacts
    PRED_LATEST_CSV   = Dirs.ARTIFACTS / "pred_latest.csv"
    PRED_DIRECTION    = Dirs.ARTIFACTS / "pred_direction.csv"
    SHAP_H1_CSV       = Dirs.ARTIFACTS / "shap_h1.csv"
    SHAP_RANK_CSV     = Dirs.ARTIFACTS / "shap_predicted_month_rank.csv"
    SHAP_TOP3_CSV     = Dirs.ARTIFACTS / "shap_top3_unique.csv"

    # Explainability artifacts
    REASONING_JSON_TH = Dirs.ARTIFACTS / "reasoning_oneshot_TH.json"
    REASONING_JSON_EN = Dirs.ARTIFACTS / "reasoning_merged_EN.json"
    REASONING_CSV     = Dirs.ARTIFACTS / "reasoning_oneshot.csv"

    # Dashboard static data
    NEWS_PUBLIC_CSV   = Dirs.PUBLIC_DATA / "2017-2026.csv"
    NEWS_SUMMARY_CSV  = Dirs.PUBLIC_DATA / "news_sentiment_summary_all.csv"
    TOP_ENTITIES_JSON = Dirs.PUBLIC_DATA / "top_entities.json"
    WORDCLOUD_PNG     = Dirs.DASHBOARD_SRC / "assets" / "cci_impact_wordcloud.png"
    WORDCLOUD_JSON    = Dirs.PUBLIC_DATA / "wordcloud_words.json"  # per-word data for interactive cloud


# ─────────────────────────────────────────────
# HUGGINGFACE (LLM) SETTINGS
# ─────────────────────────────────────────────
class HF_LLM:
    # Use models optimized for Thai and Kaggle
    ABSA_MODEL    = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    SUMMARY_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    REASON_MODEL  = "google/gemma-2-27b-it"   # Local 4-bit Quantization model
    TEMPERATURE   = 0.1
    MAX_NEW_TOKENS = 800
    MAX_RETRIES   = 3


# ─────────────────────────────────────────────
# SUPABASE (News Database)
# ─────────────────────────────────────────────
class Supabase:
    URL      = os.getenv("SUPABASE_URL", "").rstrip("/") or "https://ahsnxgiqznzcjppzgctg.supabase.co"
    ANON_KEY = os.getenv("SUPABASE_KEY", "") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFoc254Z2lxem56Y2pwcHpnY3RnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc3MDQ0NzksImV4cCI6MjA4MzI4MDQ3OX0.i2rXE_neXNw_8BfR-XYaf8k-4HaE8a62MqB97x8KWZ0"
    TABLE    = "articles"
    PAGE_SIZE = 100   # small pages — avoids Supabase free-tier statement timeout


# ─────────────────────────────────────────────
# WANGCHANBERTA (Relevance Filter)
# ─────────────────────────────────────────────
class WangchanBERTa:
    # Primary: local model dir inside project
    MODEL_DIR = ROOT / "models" / "wangchanberta"
    # Fallback: original location (outside project)
    MODEL_DIR_LEGACY = ROOT.parent / "wangchanberta_cls" / "best_model"
    # HuggingFace base model (used if no fine-tuned model found)
    HF_BASE_MODEL = "airesearch/wangchanberta-base-att-spm-uncased"
    BATCH_SIZE = 16
    MAX_LENGTH = 512


# ─────────────────────────────────────────────
# PIPELINE SETTINGS
# ─────────────────────────────────────────────
class Pipeline:
    # Date range for explainability (reasoning / summarization)
    START_MONTH = "2024-01"
    END_MONTH   = "2026-04"

    # Date range for news fetching from Supabase
    # "auto" = fetch previous month automatically
    NEWS_START = "2025-09-01"
    NEWS_END   = "2026-04-30"  # Next test month after existing data

    # Backtest config
    FORECAST_HORIZON = 1
    STRIDE           = 1
    BACKTEST_START   = 0.65

    # Forecast config (script 6: predict_latest)
    PREDICT_HORIZON = 3      # months to forecast ahead from latest CCI

    # Target / features
    DATE_COL   = "date"
    TARGET_COL = "cci_overall"

    # ABSA aspects
    ASPECTS = [
        "เศรษฐกิจไทย", "มาตรการของรัฐ", "สังคม/ความมั่นคง",
        "การเมือง", "ราคาสินค้าเกษตร", "เศรษฐกิจโลก",
        "ภัยพิบัติ/โรคระบาด", "ราคาน้ำมันเชื้อเพลิง",
    ]

    # Preprocessing (script 1: preprocess_news)
    MIN_CONTENT_LEN = 300    # skip articles whose cleaned content < this many chars

    # Explainability (script 8: 3m_shap_aspect_summary)
    SHAP_TOP_K = 3           # how many top SHAP features to summarize per month

    # Assets (extract_entities)
    ENTITY_TOP_N    = 30
    ENTITY_MIN_FREQ = 3

    # Assets (generate_wordcloud)
    WORDCLOUD_MIN_WORD_LEN  = 3
    WORDCLOUD_TOP_N         = 150
    WORDCLOUD_WINDOW_MONTHS = 0    # rolling window in months; 0 = use all years


# ─────────────────────────────────────────────
# SERVER SETTINGS
# ─────────────────────────────────────────────
class Server:
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    VITE_PORT = 5173


# ─────────────────────────────────────────────
# LOCAL 4-BIT LLM INITIALIZATION (LAZY LOAD)
# ─────────────────────────────────────────────
_local_pipeline = None

def _init_local_llm(model_id: str):
    global _local_pipeline
    if _local_pipeline is not None:
        return _local_pipeline

    print(f"\n[LLM] Initializing local 4-bit model: {model_id} (This takes ~3-5 mins)...")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline

    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN not set. Required to download gated models like Gemma 2.")

    # 4-bit quantization config to fit 27B across 2x T4 GPUs (32GB total)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_id, token=token)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto",  # Automatically split across GPUs
        token=token,
    )

    _local_pipeline = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=HF_LLM.MAX_NEW_TOKENS,
        temperature=HF_LLM.TEMPERATURE,
        do_sample=True, # Need do_sample=True for temperature < 1.0
        return_full_text=False,
    )
    print("[LLM] Initialization complete. Model loaded into VRAM.")
    return _local_pipeline

# ─────────────────────────────────────────────
# LLM HELPER FUNCTION
# ─────────────────────────────────────────────
def call_hf_api(
    prompt: str,
    model: str | None = None,
    max_tokens: int = HF_LLM.MAX_NEW_TOKENS,
    temperature: float = HF_LLM.TEMPERATURE,
    retries: int = HF_LLM.MAX_RETRIES,
) -> str:
    """
    Executes prompt using local 4-bit Quantized Model on Kaggle.
    (Kept the function name 'call_hf_api' so we don't break downstream scripts)
    """
    if model is None:
        model = HF_LLM.REASON_MODEL

    llm_pipeline = _init_local_llm(model)

    messages = [{"role": "user", "content": prompt}]
    
    for attempt in range(retries + 1):
        try:
            # Generate using local pipeline
            output = llm_pipeline(messages)
            
            # Extract text from the output
            gen_text = output[0]["generated_text"]
            if isinstance(gen_text, list):
                # Pipeline returns full conversation history as list of dicts
                text = gen_text[-1]["content"]
            else:
                text = str(gen_text)
                
            text = text.replace("\u200b", " ")
            text = re.sub(r"\s+", " ", text).strip()
            return text
        except Exception as e:
            if attempt < retries:
                wait = 3 * (attempt + 1)
                print(f"  [LLM Error attempt {attempt+1}/{retries}] {e} — waiting {wait}s")
                time.sleep(wait)
            else:
                return f"[LLM_ERROR] {e}"


# ─────────────────────────────────────────────
# KAGGLE WORKSPACE INITIALIZATION
# ─────────────────────────────────────────────
def init_kaggle_workspace():
    """
    Copy base data files from project root into kaggle_workspace/
    so the pipeline can write new results there without touching originals.
    Call this once before running the pipeline in Kaggle.
    """
    import shutil

    ws = ROOT / "kaggle_workspace"
    if not _KAGGLE_MODE:
        print("Not in Kaggle mode (set KAGGLE_ENV=1 to enable). Skipping.")
        return

    # Directories to seed (copy from project root → kaggle_workspace/)
    seed_dirs = ["data", "artifacts", "models", "public"]
    for d in seed_dirs:
        src = ROOT / d
        dst = ws / d
        if src.exists() and not dst.exists():
            print(f"  Seeding {d}/ → kaggle_workspace/{d}/")
            shutil.copytree(src, dst)
        else:
            dst.mkdir(parents=True, exist_ok=True)

    # Seed indicator CSVs from dashboard/dist (the authoritative source)
    # public/data/indicators/ in the repo may only have cci.csv
    dist_indicators = ROOT / "dashboard" / "dist" / "data" / "indicators"
    ws_indicators = ws / "public" / "data" / "indicators"
    ws_indicators.mkdir(parents=True, exist_ok=True)
    if dist_indicators.exists():
        for csv_file in dist_indicators.glob("*.csv"):
            dst_file = ws_indicators / csv_file.name
            if not dst_file.exists():
                shutil.copy2(csv_file, dst_file)
                print(f"  Seeded indicator: {csv_file.name}")

    print(f"Kaggle workspace ready: {ws}")


# ─────────────────────────────────────────────
# Convenience alias
# ─────────────────────────────────────────────
cfg = type("Config", (), {
    "dirs": Dirs,
    "files": Files,
    "hf_llm": HF_LLM,
    "supabase": Supabase,
    "wangchanberta": WangchanBERTa,
    "pipeline": Pipeline,
    "server": Server,
    "ROOT": ROOT,
    "WORKSPACE": WORKSPACE,
    "KAGGLE_MODE": _KAGGLE_MODE,
    "call_hf_api": staticmethod(call_hf_api),
    "init_workspace": staticmethod(init_kaggle_workspace),
})()
