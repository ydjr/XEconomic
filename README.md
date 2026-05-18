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


## 📂 Project Structure
 
```
XEconomic/
│
├─ api/
│  └─ main.py
│
├─ artifacts/
│  ├─ backtest/
│  ├─ cci_dashboard_latest.csv
│  ├─ predicted_latest.csv
│  ├─ reasoning_2017-01_to_2025-08.csv
│  ├─ shap_h1.csv
│  └─ shap_predicted_month_rank.csv
│
├─ dashboard/
│  ├─ index.html
│  │
│  ├─ src/
│  │  ├─ assets/
│  │  │  └─ cci-impact-wordcloud.png
│  │  ├─ api.js
│  │  ├─ App.jsx
│  │  ├─ index.css
│  │  ├─ main.jsx
│  │  ├─ newsFileApi.js
│  │  ├─ newsSupabaseApi.js
│  │  ├─ style.css
│  │  └─ supabaseClient.js
│  │
│  └─ data/
│     ├─ news_sentiment_summary_all.csv
│     ├─ avg_sent_indi.csv
│     └─ top_entities.json
│
├─ models/
│  └─ backtest/
│
├─ pipeline/
│  ├─ 1_news_analysis/
│  │  ├─ 1.preprocess_news.py
│  │  ├─ 2.eachnews_StelleX.py
│  │  ├─ 3.absa.py
│  │  ├─ 4.ft_extract.py
│  │  └─ 5.consolidate.py
│  │
│  ├─ 2_forecasting/
│  │  ├─ 6.predict_latest.py
│  │  └─ backtest.py
│  │
│  ├─ 3_explainable_ai/
│  │  ├─ 7.monthly_summary_v2.py
│  │  ├─ 8.3m_shap_aspect_summary_v3.py
│  │  ├─ 9.script4_oneshot.py
│  │  ├─ extract_entities.py
│  │  └─ generate_wordcloud.py
│  │
│  ├─ backtest.py
│  ├─ train.py
│  ├─ predict_latest.py
│  ├─ extract_entities.py
│  └─ generate_wordcloud.py
│
├─ _field_check.json
├─ requirements.txt
├─ README.md
└─ PIPELINE.md
```
 
---
 
## 🛠 Tech Stack
 
| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI |
| Database | Supabase |
| ML / Forecasting | Python (scikit-learn, XGBoost, Darts) |
| Explainability | SHAP |
