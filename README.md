# XEconomic – CCI Forecast & SHAP Dashboard

This project displays **Consumer Confidence Index (CCI)** predictions and **SHAP explanations** in a web dashboard. 

The system consists of a data pipeline, a FastAPI backend, and a React frontend.

Dataset >> https://drive.google.com/drive/folders/19Alecj2bQcHKSXlUxC9wWxjYVbDT_RT9?usp=sharing  (load avg_sent_indi.csv)

---

## Quick Start

### Option A: One-Click Dashboard
Double-click **`start.bat`** to launch both backend + frontend.

### Option B: Full Pipeline + Dashboard
```bash
python run_pipeline.py --all
```

### Option C: Step by Step
```bash
# 1. Setup environment (first time only)
setup.bat

# 2. Run specific phases
python run_pipeline.py --phase train    # Training + prediction
python run_pipeline.py --phase serve    # Start dashboard

# 3. Or run from a specific phase onwards
python run_pipeline.py --from train
```

---

## Pipeline Orchestrator

`run_pipeline.py` connects all processes into a single automated pipeline:

```bash
python run_pipeline.py --all                # Run everything end-to-end
python run_pipeline.py --phase news         # Only news processing
python run_pipeline.py --phase train        # Only training + prediction
python run_pipeline.py --phase explain      # Only LLM explainability
python run_pipeline.py --phase assets       # Only entity + wordcloud
python run_pipeline.py --phase serve        # Only start servers
python run_pipeline.py --from train         # Start from training phase onwards
python run_pipeline.py --skip-llm           # Skip LLM-heavy steps
python run_pipeline.py --check              # Validate environment only
python run_pipeline.py --force --all        # Force re-run all steps
```

### Pipeline Phases

| Phase | Steps | Description |
|-------|-------|-------------|
| `news` | 1-5 | News preprocessing, relevance filter, ABSA, feature extraction, consolidation |
| `train` | 6-8 | Model backtest (GridSearch), training, prediction + SHAP |
| `explain` | 9-11 | SHAP prep, 3-month summary, reasoning generation (LLM) |
| `assets` | 12-13 | Entity extraction, word cloud generation |
| `serve` | 14-15 | Start FastAPI backend + Vite frontend |

---

## Monthly Automation

Run `schedule_setup.bat` as Administrator to register a Windows Task Scheduler task:
- Runs the full pipeline on the **5th of every month** at 2:00 AM
- Logs output to `logs/pipeline_YYYY-MM.log`

---

## Manual Step-by-Step (Legacy)

### STEP 1 — ACTIVATE PYTHON ENVIRONMENT

From the project root (`XEconomic/`):

Windows:
```
python -m venv .venv
.venv/scripts/activate
pip install -r requirements.txt
```

### STEP 2 - RUN PREDICTION PIPELINE
```
python pipeline/backtest.py
python pipeline/train.py
python pipeline/predict_latest.py
```

### STEP 3 - START BACKEND SERVER (FASTAPI)
```
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### STEP 4 - START FRONTEND (VITE)
```
cd dashboard
npm install
npm run dev
```

Open browser: http://localhost:5173

---

## Project Structure

```text
XEconomic/
│
├─ config.py                    # Central configuration (all paths)
├─ run_pipeline.py              # Pipeline orchestrator
├─ start.bat                    # One-click dashboard launcher
├─ setup.bat                    # Environment setup
├─ run_monthly.bat              # Monthly pipeline runner
├─ schedule_setup.bat           # Register monthly scheduler
│
├─ api/
│  └─ main.py                  # FastAPI backend
│
├─ artifacts/
│  ├─ backtest/                 # Model comparison results
│  ├─ pred_latest.csv
│  ├─ pred_direction.csv
│  ├─ shap_h1.csv
│  ├─ shap_predicted_month_rank.csv
│  └─ shap_top3_unique.csv
│
├─ dashboard/
│  ├─ src/
│  │  ├─ App.jsx               # Main dashboard component
│  │  ├─ api.js                # Backend API client
│  │  ├─ newsFileApi.js
│  │  └─ newsSupabaseApi.js
│  └─ data/
│
├─ data/
│  ├─ indicators/              # Economic indicators (CCI, CPI, GDP, etc.)
│  ├─ 4_absa_features/         # ABSA-derived monthly features
│  └─ avg_sent_indi.csv        # Combined training dataset
│
├─ explainable/
│  ├─ reasoning/               # LLM reasoning generation
│  ├─ shap/                    # SHAP post-processing
│  └─ text_summarization/      # 3-month aspect summaries
│
├─ models/
│  └─ backtest/                # Trained model weights
│
├─ pipeline/
│  ├─ news_prep/               # News processing pipeline (steps 1-5)
│  ├─ backtest.py              # Model GridSearch
│  ├─ train.py                 # Train best model
│  ├─ predict_latest.py        # Predict + SHAP explanation
│  ├─ extract_entities.py
│  └─ generate_wordcloud.py
│
├─ logs/                        # Pipeline execution logs
├─ requirements.txt
└─ README.md
```
