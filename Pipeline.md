# XEconomics – Full NLP/ML Pipeline

This document covers running the full data pipeline that powers XEconomics —
from raw Thai news processing through news analysis, forecasting, and LLM-based explainability AI.

> **For web dashboard** See [README.md](./README.md) instead.

---

## ⚙️ Requirements

### Ollama (for LLM steps)
Install Ollama from https://ollama.com and pull the required models:

```bash
ollama pull gemma2:27b
```

Make sure Ollama is running before executing Steps 7–9:
```bash
ollama serve
```

---

## 🗂 Pipeline Overview

```
Raw Thai News
     │
     ▼
1_news_analysis/
  1. preprocess_news       — clean & deduplicate raw articles
  2. eachnews_StelleX      — summarize each article (MT5)
  3. absa                  — aspect-based sentiment analysis (8 TPSO aspects)
  4. ft_extract            — extract features from ABSA results
  5. consolidate           — merge news features with macroeconomic indicators
     │
     ▼
2_forecasting/
  6. predict_latest        — forecast CCI with XGBoost + SHAP attribution
     │
     ▼
3_explainable_ai/
  7. monthly_summary_v2    — classify aspect, sentiment score, and effect type per month (LLM)
  8. 3m_shap_aspect_summary— aggregate 3-month SHAP evidence per indicator (LLM)
  9. script4_oneshot       — generate structured Thai reasoning report (LLM)
```

---

## 🚀 Run Steps

### STEP 1 — Preprocess News

Cleans raw crawled articles: removes boilerplate, deduplicates by URL,
filters short articles, normalizes Thai characters.

```bash
python pipeline/1_news_analysis/1.preprocess_news.py
```

**Input:** raw crawled news CSV
**Output:** cleaned news CSV

---

### STEP 2 — Summarize Each Article

Summarizes each article using an MT5 model to reduce token length
before ABSA.

```bash
python pipeline/1_news_analysis/2.eachnews_StelleX.py
```

**Input:** cleaned news CSV
**Output:** news CSV with summary column

---

### STEP 3 — ABSA (Aspect-Based Sentiment Analysis)

Classifies each article's sentiment across 8 economic dimensions
defined by Thailand's TPSO:
การจ้างงาน, รายได้, ค่าครองชีพ, การออม, การลงทุน, ความเชื่อมั่น, การค้า, นโยบายภาครัฐ

```bash
python pipeline/1_news_analysis/3.absa.py
```

**Input:** summarized news CSV
**Output:** ABSA results CSV (aspect + sentiment score per article)

---

### STEP 4 — Feature Extraction

Aggregates ABSA scores into monthly sentiment features per aspect.

```bash
python pipeline/1_news_analysis/4.ft_extract.py
```

**Input:** ABSA results CSV
**Output:** monthly feature CSV

---

### STEP 5 — Consolidate Features

Merges news-derived sentiment features with macroeconomic indicators
into one unified dataset ready for forecasting.

```bash
python pipeline/1_news_analysis/5.consolidate.py
```

**Input:** monthly features CSV + macroeconomic indicators CSV
**Output:** `avg_sent_indi.csv` (consolidated dataset)

---

### STEP 6 — Forecast & SHAP

Trains XGBoost forecasting model, predicts CCI for the latest month,
and computes SHAP feature attributions to identify top-3 influential features.

```bash
python pipeline/2_forecasting/6.predict_latest.py
```

**Input:** `avg_sent_indi.csv`
**Output:** `artifacts/predicted_latest.csv`, `artifacts/shap_predicted_month_rank.csv`

---

### STEP 7 — Monthly Aspect Summarization (LLM)

For each month runs aspect-based sentiment analysis to classify aspect,
sentiment score, and effect type.

```bash
python pipeline/3_explainable_ai/7.monthly_summary_v2.py
```

**Requires:** Ollama running with `gemma2:27b`
**Input:** ABSA results CSV
**Output:** monthly summary CSV per aspect

---

### STEP 8 — 3-Month SHAP Evidence Summarization (LLM)

For each SHAP-identified top feature, retrieves the 3 months of
news evidence prior to the forecast month and summarizes it into
a structured evidence block.

```bash
python pipeline/3_explainable_ai/8.3m_shap_aspect_summary_v3.py
```

**Requires:** Ollama running with `gemma2:27b`
**Input:** monthly summary CSV + SHAP results
**Output:** 3-month evidence summary CSV

---

### STEP 9 — LLM Reasoning Report Generation

Generates the final structured Thai-language reasoning report
(FACTOR1, FACTOR2, FACTOR3, CONCLUSION) using one-shot prompting.

```bash
python pipeline/3_explainable_ai/9.script4_oneshot.py
```

**Requires:** Ollama running with `gemma2:27b`
**Input:** 3-month evidence CSV + forecast values
**Output:** `artifacts/reasoning_2017-01_to_2025-08.csv`

---

### OPTIONAL — Extract Entities & Word Cloud

```bash
python pipeline/3_explainable_ai/extract_entities.py
python pipeline/3_explainable_ai/generate_wordcloud.py
```

---

## 📋 Script Summary Table

| # | Script | Model | Est. Runtime |
|---|---|---|---|
| 1 | preprocess_news.py | — | Fast |
| 2 | eachnews_StelleX.py | MT5 | Hours (35k articles) |
| 3 | absa.py | gemma2:27b | Hours |
| 4 | ft_extract.py | — | Fast |
| 5 | consolidate.py | — | Fast |
| 6 | predict_latest.py | XGBoost | Fast |
| 7 | monthly_summary_v2.py | gemma2:27b | Hours |
| 8 | 3m_shap_aspect_summary_v3.py | gemma2:27b | Hours |
| 9 | script4_oneshot.py | gemma2:27b | Minutes–Hours |
