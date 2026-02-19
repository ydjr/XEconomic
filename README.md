# XEconomic – CCI Forecast & SHAP Dashboard

This project displays **Consumer Confidence Index (CCI)** predictions and **SHAP explanations** in a web dashboard. 

The system consists of a data pipeline, a FastAPI backend, and a React frontend. They **must** be run in the specific order outlined below to ensure data is available for visualization.

dataset >> https://drive.google.com/drive/folders/19Alecj2bQcHKSXlUxC9wWxjYVbDT_RT9?usp=sharing  (load avg_sent_indi.csv)

---
### STEP 1 — ACTIVATE PYTHON ENVIRONMENT

From the project root (`XEconomic/`):

Windows:
python -m venv .venv

.venv/scripts/activate

pip install -r requirements.txt



### STEP 2 - RUN PREDICTION PIPELINE (this will predict for 2025-08 only)
This step generate data for the website

python pipeline/backtest.py

python pipeline/train.py

python pipeline/predict_latest.py


### STEP 3 - START BACKEND SERVER (FASTAPI)

Keep this terminal open:
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000


### STEP 4 - START FRONTEND (VITE)
Open new terminal to run this command:

cd dashboard

npm install @supabase/supabase-js

npm run dev

Open browser: http://localhost:5173


## 📂 Project Structure (not the latest version)

```text
XEconomic/
│
├─ pipeline/            # Prediction pipeline
│  └─ predict_latest.py
|  └─ backtest.py
|  └─ utils.py
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
│  ├─ vite.config.js
│  ├─ index.html
│  ├─ package.json
│  └─ src/
|     ├─ api.js
|     ├─ app.jsx
|     ├─ main.jsx
|     ├─ style.css
|     └─ components/
|        ├─ ShapBar.jsx
|        └─ TimeSeriesChart.jsx
│
├─ requirements.txt
├─ README.md
└─ .gitignore
