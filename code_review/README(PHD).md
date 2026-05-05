# Thai News-Based Consumer Confidence Index (CCI) Forecasting with Explainable AI

A pipeline that forecasts Thailand's Consumer Confidence Index (CCI) from economic news and macroeconomic indicators, then generates Thai-language XAI reasoning reports explaining each forecast.

---

## Project Structure

```
.
├── news_analysis/
│   ├── 1.eachnews_StelleX.py       # News summarization (MT5 model)
│   └── 2.absa.py                   # Aspect-Based Sentiment Analysis (ABSA)
│
├── forecasting/
│   └── 3.backtest.py               # CCI forecasting with grid search backtest
│
└── explainable/
    ├── 4.monthly_summary_v2.py     # Monthly aspect sentiment summarization
    ├── 5.3m_shap_aspect_summary_v3.py  # 3-month SHAP-aligned evidence summarization
    └── 6.script4_oneshot.py        # XAI reasoning report generation
```

---

## Pipeline Overview

```
Raw News Articles
      ↓
[1] Summarize each article (MT5)
      ↓
[2] ABSA — classify aspect + sentiment per article
      ↓
[3] Backtest forecasting models → best model → predicted CCI + SHAP values
      ↓
[4] Monthly aspect sentiment summarization (pos/neg per aspect per month)
      ↓
[5] 3-month SHAP-aligned evidence summarization (per top indicator per month)
      ↓
[6] XAI reasoning report (FACTOR1–3 + CONCLUSION in Thai)
```

---

## Scripts

### `1.eachnews_StelleX.py` — News Summarization
Summarizes each raw Thai news article using the `StelleX/mt5-base-thaisum-text-summarization` model (seq2seq). Processes articles in batches on GPU, with checkpoint saving every 20 rows. Skips articles that already have a summary (resume-safe).

**Input:** `All3econnews2017_2026cleaned.csv` (raw news with `content` column)  
**Output:** Same CSV with `summary` column filled

---

### `2.absa.py` — Aspect-Based Sentiment Analysis
Sends each article summary to an LLM (llama3.1:70b via Ollama) and classifies it into:
- **Aspect** — one of 8 economic categories (e.g. เศรษฐกิจไทย, การเมือง, ราคาน้ำมันเชื้อเพลิง)
- **sentiment_score** — 0.00–1.00
- **impact_type** — Positive / Neutral / Negative
- **effect_type** — Short-term / Long-term

Includes retry logic, JSON repair prompting, and resume support.

**Input:** Summarized news CSV  
**Output:** ABSA-labeled CSV with one row per article

---

### `3.backtest.py` — CCI Forecasting & Grid Search
Trains and evaluates 4 model types (ARIMAX, XGBoost, LSTM/BlockRNN, N-HiTS) across 4 feature sets and 6 forecast horizons (1–6 months ahead) using walk-forward backtesting.

**Feature sets:** `cci_only`, `macro`, `news`, `macro_plus_news`  
**Metrics:** MAPE, RMSE  
**Output:** Best params per model/horizon/feature-set, prediction CSVs, summary comparison table

Also produces SHAP values for the best model, used downstream in scripts 5 and 6.

---

### `4.monthly_summary_v2.py` — Monthly Aspect Summarization
For each month × aspect combination, splits news into positive and negative groups and summarizes each side independently using an LLM (gemma2:27b via Ollama).

**Summarization logic:**
- `n=0` → blank, no LLM call
- `n=1` → copy directly, no LLM call
- `n≥2, tokens ≤ 6,000` → single LLM call
- `n≥2, tokens > 6,000` → map-reduce (chunk → summarize each → reduce)

Neutral articles are excluded. `Overall_Lean` (บวก/ลบ/ทรงตัว) is computed by majority count, no LLM needed. Resume-safe via done-key tracking.

**Input:** ABSA CSV  
**Output:** `results<year>.csv` — one row per month × aspect with `Positive_Summary`, `Negative_Summary`, `Overall_Lean`

---

### `5.3m_shap_aspect_summary_v3.py` — 3-Month SHAP Evidence Summarization
For each forecast month, looks up the top-3 SHAP features (most impactful indicators), maps each indicator to relevant news aspects, then pulls 3 months of evidence from the monthly summary CSV and asks an LLM to compress it into a single pos/neg summary per indicator.

The LLM is given the indicator's definition and must first verify alignment — if the evidence doesn't clearly connect to the indicator, it returns a fixed fallback string instead of hallucinating.

**Input:** Monthly summary CSV, SHAP CSV, predicted CCI CSV  
**Output:** `3m_summary_<range>.csv` — one row per indicator per month

---

### `6.script4_oneshot.py` — XAI Reasoning Report Generation
The final stage. For each forecast month, takes the 3 top SHAP indicators and their 3-month evidence summaries and generates a structured Thai-language reasoning report using a one-shot prompted LLM (gemma4:31b).

**Output format (4 delimited sections):**
```
[FACTOR1] Main factor — most detailed explanation [/FACTOR1]
[FACTOR2] Supporting factor [/FACTOR2]
[FACTOR3] Supporting factor [/FACTOR3]
[CONCLUSION] 2–3 sentence causal summary of why CCI moved in this direction [/CONCLUSION]
```

An `intro` sentence is generated deterministically in Python (no LLM). Results are saved as both CSV and JSON.

**Input:** 3M summary CSV, predicted CCI CSV  
**Output:** `reasoning_<range>.csv` + `.json`

---

## Models Used

| Purpose | Model |
|---|---|
| News summarization | StelleX/mt5-base-thaisum-text-summarization |
| ABSA | llama3.1:70b (Ollama) |
| Monthly summarization | gemma2:27b (Ollama) |
| 3M evidence summarization | gemma2:27b (Ollama) |
| XAI report generation | gemma4:31b (Ollama) |
| CCI forecasting | ARIMAX / XGBoost / LSTM / N-HiTS (Darts) |

---

## Requirements

- Python 3.10+
- PyTorch with CUDA
- `transformers`, `darts`, `statsmodels`, `scikit-learn`, `pythainlp`, `tiktoken`, `tqdm`, `pandas`, `requests`
- [Ollama](https://ollama.ai) running locally on port 11434 with the required models pulled