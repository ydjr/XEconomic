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
    INDICATORS  = ROOT / "data" / "indicators"
    ABSA_FEAT   = ROOT / "data" / "4_absa_features"
    PIPELINE    = ROOT / "pipeline"
    NEWS_PREP   = ROOT / "pipeline" / "news_prep"
    PIPELINE_DATA = ROOT / "pipeline" / "data"
    NEWS_SUM    = ROOT / "pipeline" / "data" / "news_sum"
    CLEANED_NEWS = ROOT / "pipeline" / "data" / "1_cleaned_news"
    ARTIFACTS   = ROOT / "artifacts"
    BACKTEST_ART = ROOT / "artifacts" / "backtest"
    MODELS      = ROOT / "models"
    BACKTEST_MDL = ROOT / "models" / "backtest"
    EXPLAINABLE = ROOT / "explainable"
    SHAP_DIR    = ROOT / "explainable" / "shap"
    SHAP_RESULT = ROOT / "explainable" / "shap" / "shap_result"
    REASONING   = ROOT / "explainable" / "reasoning"
    TEXT_SUM    = ROOT / "explainable" / "text_summarization"
    DASHBOARD   = ROOT / "dashboard"
    DASHBOARD_SRC = ROOT / "dashboard" / "src"
    PUBLIC      = ROOT / "public"
    PUBLIC_DATA = ROOT / "public" / "data"
    LOGS        = ROOT / "logs"
    API         = ROOT / "api"


# ─────────────────────────────────────────────
# KEY DATA FILES
# ─────────────────────────────────────────────
class Files:
    # Indicators
    CCI_CSV           = Dirs.INDICATORS / "cci.csv"
    CPI_CSV           = Dirs.INDICATORS / "cpi.csv"
    GDP_CSV           = Dirs.INDICATORS / "gdp_monthly.csv"
    POLICY_RATE_CSV   = Dirs.INDICATORS / "policy_rate.csv"
    UNEMPLOYMENT_CSV  = Dirs.INDICATORS / "unemployment_rate.csv"
    IMPI_CSV          = Dirs.INDICATORS / "impi.csv"
    EXPI_CSV          = Dirs.INDICATORS / "expi.csv"

    # Combined dataset for training
    AVG_SENT_INDI     = Dirs.DATA / "avg_sent_indi.csv"
    FULL_NEWS_CSV     = Dirs.DATA / "2017-2026.csv"
    ASPECT_FEATURES   = Dirs.ABSA_FEAT / "aspect_monthly_features.csv"

    # Pipeline intermediates
    CLEANED_NEWS_CSV  = Dirs.CLEANED_NEWS / "all_news.csv"
    RELEVANCE_CSV     = Dirs.PIPELINE_DATA / "2_news_cci_r.csv"
    ABSA_OUTPUT_DIR   = Dirs.PIPELINE_DATA  # 3_absa.py outputs here

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
    REASONING_JSON_TH = Dirs.ARTIFACTS / "one_reasoning_2024-01_to_2025-08.json"
    REASONING_JSON_EN = Dirs.ARTIFACTS / "reasoning_merged_EN.json"
    REASONING_CSV     = Dirs.ARTIFACTS / "reasoning_oneshot.csv"

    # Dashboard static data
    NEWS_PUBLIC_CSV   = Dirs.PUBLIC_DATA / "2017-2026.csv"
    NEWS_SUMMARY_CSV  = Dirs.PUBLIC_DATA / "news_sentiment_summary_all.csv"
    TOP_ENTITIES_JSON = Dirs.PUBLIC_DATA / "top_entities.json"
    WORDCLOUD_PNG     = Dirs.DASHBOARD_SRC / "assets" / "cci_impact_wordcloud.png"


# ─────────────────────────────────────────────
# OLLAMA (LLM) SETTINGS
# ─────────────────────────────────────────────
class Ollama:
    URL           = "http://localhost:11434/api/generate"
    ABSA_MODEL    = "llama3.1:8b"
    SUMMARY_MODEL = "llama3.1:8b"
    REASON_MODEL  = "gemma2:27b"
    TEMPERATURE   = 0.1
    MAX_RETRIES   = 3
    TIMEOUT       = 360


# ─────────────────────────────────────────────
# SUPABASE (News Database)
# ─────────────────────────────────────────────
class Supabase:
    URL      = "https://ahsnxgiqznzcjppzgctg.supabase.co"
    ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFoc254Z2lxem56Y2pwcHpnY3RnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc3MDQ0NzksImV4cCI6MjA4MzI4MDQ3OX0.i2rXE_neXNw_8BfR-XYaf8k-4HaE8a62MqB97x8KWZ0"
    TABLE    = "articles"
    PAGE_SIZE = 1000  # rows per API call (Supabase limit)


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
    END_MONTH   = "2025-08"

    # Date range for news fetching from Supabase
    # "auto" = fetch previous month automatically
    NEWS_START = "2017-01-01"
    NEWS_END   = "auto"  # or e.g. "2026-04-30"

    # Backtest config
    FORECAST_HORIZON = 1
    STRIDE           = 1
    BACKTEST_START   = 0.65

    # Target / features
    DATE_COL   = "date"
    TARGET_COL = "cci_overall"

    # ABSA aspects
    ASPECTS = [
        "เศรษฐกิจไทย", "มาตรการของรัฐ", "สังคม/ความมั่นคง",
        "การเมือง", "ราคาสินค้าเกษตร", "เศรษฐกิจโลก",
        "ภัยพิบัติ/โรคระบาด", "ราคาน้ำมันเชื้อเพลิง",
    ]


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
    "ollama": Ollama,
    "supabase": Supabase,
    "wangchanberta": WangchanBERTa,
    "pipeline": Pipeline,
    "server": Server,
    "ROOT": ROOT,
})()
