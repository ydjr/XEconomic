"""
XEconomic — Kaggle Pipeline Runner
====================================
Run LLM-heavy steps on Kaggle's free GPU (T4/P100).
Upload this as a Kaggle Notebook and schedule it monthly.

Steps covered:
  - Step 3: ABSA (requires Ollama — see note below)
  - Step 10: 3-month aspect summary
  - Step 11: Reasoning generation

NOTE: Kaggle doesn't have Ollama natively. Options:
  1. Run Ollama inside Kaggle (download + start in background)
  2. Use HuggingFace transformers directly instead of Ollama
  3. Use Kaggle only for non-LLM GPU steps (WangchanBERTa inference)

This template shows Option 1 (Ollama in Kaggle).

Usage:
  1. Create a new Kaggle Notebook
  2. Add your GitHub repo as a dataset or clone it
  3. Paste this script and run
  4. Schedule the notebook for monthly execution
"""

import subprocess
import os
import sys
import time

# ===========================================
# CONFIGURATION
# ===========================================
# For private repos, use a GitHub Token in Kaggle Secrets
# Example: "https://${GITHUB_TOKEN}@github.com/Jean-ktn/XEconomic-Auto.git"
REPO_URL = "https://github.com/Jean-ktn/XEconomic-Auto.git"
BRANCH = "main"
WORK_DIR = "/kaggle/working/XEconomic-Auto"

# Which phases to run on Kaggle
# Option A: LLM steps only (ABSA, summarization, reasoning)
PHASES = ["news", "explain"]
SKIP_LLM = False

# Option B: GPU steps only (WangchanBERTa relevance filter)
# PHASES = ["news"]
# SKIP_LLM = True  # skip Ollama, only run WangchanBERTa

# ===========================================
# SETUP
# ===========================================

def run(cmd, cwd=None):
    """Run a shell command and print output."""
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout[-2000:])
    if result.returncode != 0:
        print(f"ERROR: {result.stderr[-1000:]}")
    return result.returncode == 0


# Step 1: Clone repository
print("=" * 60)
print("SETUP: Cloning repository")
print("=" * 60)

if not os.path.exists(WORK_DIR):
    run(f"git clone --depth 1 -b {BRANCH} {REPO_URL} {WORK_DIR}")
else:
    run(f"git reset --hard HEAD && git pull", cwd=WORK_DIR)

# Step 2: Install dependencies
print("\nInstalling Python dependencies...")
run(f"pip install -q -r {WORK_DIR}/requirements.txt")

# Step 3: Install and start Ollama (if running LLM steps)
if not SKIP_LLM:
    print("\n" + "=" * 60)
    print("SETUP: Installing Ollama")
    print("=" * 60)
    
    # Install zstd which is required by new Ollama installer
    run("sudo apt-get update && sudo apt-get install -y zstd")
    run("curl -fsSL https://ollama.com/install.sh | sh")
    
    # Start Ollama server in background
    subprocess.Popen(
        "ollama serve",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(5)
    
    # Pull required models
    print("Pulling LLM models...")
    run("ollama pull llama3.1:8b")     # ABSA + summarization
    run("ollama pull gemma2:27b")       # Reasoning (if GPU has enough VRAM)
    
    # Verify
    run("ollama list")

# ===========================================
# RUN PIPELINE
# ===========================================
print("\n" + "=" * 60)
print("RUNNING PIPELINE")
print("=" * 60)

for phase in PHASES:
    print(f"\n--- Phase: {phase} ---")
    skip_flag = "--skip-llm" if SKIP_LLM else ""
    ok = run(f"python run_pipeline.py --phase {phase} --force {skip_flag}", cwd=WORK_DIR)
    if not ok:
        print(f"[!] Phase {phase} failed. Check logs.")
        break

# ===========================================
# SAVE OUTPUTS
# ===========================================
print("\n" + "=" * 60)
print("SAVING OUTPUTS")
print("=" * 60)

# Copy key outputs to Kaggle's output directory
import shutil
OUTPUT_DIR = "/kaggle/working/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

for src in [
    f"{WORK_DIR}/artifacts",
    f"{WORK_DIR}/data/avg_sent_indi.csv",
    f"{WORK_DIR}/models",
    f"{WORK_DIR}/logs",
]:
    if os.path.exists(src):
        dst = os.path.join(OUTPUT_DIR, os.path.basename(src))
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        print(f"  Saved: {dst}")

# Optional: Push results back to GitHub
# run(f"git add -A && git commit -m 'kaggle: monthly update' && git push", cwd=WORK_DIR)

print("\n" + "=" * 60)
print("DONE!")
print("=" * 60)
