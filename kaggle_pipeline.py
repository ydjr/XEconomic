"""
XEconomic — Kaggle Pipeline Runner (HuggingFace API Edition)
===========================================================
This script automates running the pipeline on Kaggle Notebooks.
Since we've upgraded the system to use HuggingFace API (Serverless),
you no longer need to install or run Ollama, which saves massive GPU RAM!

Prerequisites in Kaggle:
1. Add Kaggle Secrets:
   - HF_TOKEN: Your HuggingFace API Token
   - GITHUB_TOKEN: Your GitHub Personal Access Token (for auto-pushing results)
2. Set Notebook Environment:
   - Turn ON Internet access
   - Select T4 x2 or P100 GPU (for WangchanBERTa)

Usage:
  Paste this entire file into a single Kaggle Notebook cell and run.
"""

import os
import subprocess
import shutil

# ===========================================
# CONFIGURATION
# ===========================================
# UPDATE THIS TO YOUR REPO URL!
REPO_URL = "https://github.com/Jean-ktn/XEconomic-Auto.git" 
BRANCH = "jeans/news-analytics-update"
WORK_DIR = "/kaggle/working/XEconomic"

# ===========================================
# SETUP SECRETS & ENVIRONMENT
# ===========================================
# 1. Enable Kaggle Workspace Isolation
os.environ["KAGGLE_ENV"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# 2. Load Tokens from Kaggle Secrets
try:
    from kaggle_secrets import UserSecretsClient
    secrets = UserSecretsClient()
    os.environ["HF_TOKEN"] = secrets.get_secret("HF_TOKEN")
    os.environ["GITHUB_TOKEN"] = secrets.get_secret("GITHUB_TOKEN")
    print("✅ Successfully loaded Kaggle Secrets (HF_TOKEN, GITHUB_TOKEN)")
except Exception as e:
    print("⚠️ WARNING: Could not load Kaggle Secrets. If running locally, make sure variables are set.")
    print(e)


def run(cmd, cwd=None):
    """Run a shell command and print output."""
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout[-2000:])
    if result.returncode != 0:
        print(f"ERROR: {result.stderr[-1000:]}")
    return result.returncode == 0

# ===========================================
# STEP 1: PREPARE REPOSITORY
# ===========================================
print("\n" + "=" * 60)
print("1. CLONING REPOSITORY")
print("=" * 60)

if not os.path.exists(WORK_DIR):
    # If GITHUB_TOKEN exists, use it to clone so we can push later
    token = os.getenv("GITHUB_TOKEN", "")
    if token:
        auth_url = REPO_URL.replace("https://", f"https://oauth2:{token}@")
    else:
        auth_url = REPO_URL
        
    run(f"git clone --depth 1 -b {BRANCH} {auth_url} {WORK_DIR}")
else:
    run(f"git pull", cwd=WORK_DIR)

# ===========================================
# STEP 2: INSTALL DEPENDENCIES
# ===========================================
print("\n" + "=" * 60)
print("2. INSTALLING DEPENDENCIES")
print("=" * 60)
run(f"pip install -q -r {WORK_DIR}/requirements.txt")
run(f"pip install -q -U huggingface_hub pythainlp darts xgboost lightgbm")
run(f"pip install -q -U accelerate bitsandbytes transformers")

# ===========================================
# STEP 3: INITIALIZE WORKSPACE
# ===========================================
print("\n" + "=" * 60)
print("3. INITIALIZING WORKSPACE")
print("=" * 60)
# This uses config.py to safely separate web data from Kaggle outputs
run(f"python -c \"import config; config.init_kaggle_workspace()\"", cwd=WORK_DIR)


# ===========================================
# STEP 4: RUN PIPELINE
# ===========================================
print("\n" + "=" * 60)
print("4. RUNNING PIPELINE")
print("=" * 60)

# Run ALL phases automatically (fetch -> news -> train -> explain -> assets)
# Since Ollama is removed, it goes straight to HF API!
success = run(f"python run_pipeline.py --all --force", cwd=WORK_DIR)

if not success:
    print("\n❌ Pipeline failed. Stopping here.")
    exit(1)

# ===========================================
# STEP 5: SAVE OUTPUTS TO GITHUB
# ===========================================
print("\n" + "=" * 60)
print("5. SAVING & PUSHING OUTPUTS")
print("=" * 60)

# Configure Git
run("git config --global user.email 'kaggle-bot@xeconomic.com'", cwd=WORK_DIR)
run("git config --global user.name 'Kaggle Pipeline Bot'", cwd=WORK_DIR)

# Only add the kaggle_workspace updates to avoid tracking useless intermediate files
# Add files that are supposed to be pushed back (artifacts, public data, indicators, pipeline state)
run("git add -f kaggle_workspace/artifacts kaggle_workspace/public kaggle_workspace/models kaggle_workspace/data pipeline/data", cwd=WORK_DIR)
run("git commit -m '🤖 Kaggle auto-update: new pipeline results'", cwd=WORK_DIR)

# Push back to origin
if os.getenv("GITHUB_TOKEN"):
    print("Pushing to GitHub...")
    run("git push", cwd=WORK_DIR)
else:
    print("No GITHUB_TOKEN found. Skipping git push.")

print("\n" + "=" * 60)
print("🎉 KAGGLE PIPELINE COMPLETE!")
print("=" * 60)
