# XEconomic – CCI Forecast & SHAP Dashboard

This project displays **Consumer Confidence Index (CCI)** predictions and **SHAP explanations** in a web dashboard. 

The system consists of a data pipeline, a FastAPI backend, and a React frontend. They **must** be run in the specific order outlined below to ensure data is available for visualization.

---
### STEP 1 — ACTIVATE PYTHON ENVIRONMENT

From the project root (`XEconomic/`):

Windows
.venv/scripts/activate

### STEP 2 - RUN PREDICTION PIPELINE (NOT STABLE YET)
This step generate data for the website

python pipeline/predict_latest.py

Expected outputs files:
artifacts/
  latest_forecast.json
  latest_explain.json
  latest_features.json

### STEP 3 - START BACKEND SERVER (FASTAPI)

Keep this terminal open:
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

### STEP 4 - START FRONTEND (VITE)
Open new terminal to run this command:

cd dashboard
npm run dev

Open browser: http://localhost:5173


## 📂 Project Structure

```text
XEconomic/
│
├─ pipeline/            # Prediction pipeline
│  └─ predict_latest.py
|  └─ backtest.py
│
├─ api/                 # FastAPI backend
│  └─ main.py
│
├─ artifacts/           # GENERATED FILES (Internal use)
│  ├─ latest_forecast.json
│  ├─ latest_explain.json
│  ├─ latest_explain.csv
|  └─ latest_forecast.csv
│
├─ dashboard/           # React + Vite frontend
│  ├─ src/
│  ├─ vite.config.js
│  └─ package.json
│
├─ requirements.txt
├─ README.md
└─ .gitignore
