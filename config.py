"""
XEconomic — Central Configuration
==================================
All paths, settings, and constants used across the project.
Every script should import from here instead of hardcoding paths.

Usage:
    from config import cfg
    print(cfg.DATA_DIR)
"""

from pathlib import Path

# ─────────────────────────────────────────────
# PROJECT ROOT  (this file lives at project root)
# ─────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent


# ─────────────────────────────────────────────
# DIRECTORY STRUCTURE
# ─────────────────────────────────────────────
class Dirs:
    ROOT        = ROOT
    DATA        = ROOT / "data"
    # Indicator CSVs live inside public/data/indicators (served by frontend + API)
    INDICATORS  = ROOT / "public" / "data" / "indicators"
    ABSA_FEAT   = ROOT / "data" / "4_absa_features"
    
    PIPELINE    = ROOT / "pipeline"
    # New Pipeline Structure
    NEWS_ANALYSIS   = PIPELINE / "1_news_analysis"
    FORECASTING     = PIPELINE / "2_forecasting"
    EXPLAINABLE_AI  = PIPELINE / "3_explainable_ai" / "explainable"

    NEWS_SUM    = PIPELINE / "data" / "news_sum"
    CLEANED_NEWS = PIPELINE / "data" / "1_cleaned_news"
    PIPELINE_DATA = PIPELINE / "data"

    ARTIFACTS   = ROOT / "artifacts"
    BACKTEST_ART = ROOT / "artifacts" / "backtest"
    MODELS      = ROOT / "models"
    BACKTEST_MDL = ROOT / "models" / "backtest"
    
    EXPLAINABLE = ROOT / "explainable"
    SHAP_DIR    = EXPLAINABLE / "shap"
    SHAP_RESULT = EXPLAINABLE / "shap" / "shap_result"
    REASONING   = EXPLAINABLE / "reasoning"
    TEXT_SUM    = EXPLAINABLE / "text_summarization"
    
    DASHBOARD      = ROOT / "dashboard"
    DASHBOARD_SRC  = ROOT / "dashboard" / "src"
    DASHBOARD_DATA = ROOT / "artifacts"   # reasoning JSON / forecast outputs read by API
    PUBLIC         = ROOT / "public"
    PUBLIC_DATA    = ROOT / "public" / "data"
    LOGS           = ROOT / "logs"
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
    REASON_MODEL  = "google/gemma-2-9b-it"
    TEMPERATURE   = 0.1
    MAX_NEW_TOKENS = 800
    MAX_RETRIES   = 3


import os

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
})()
