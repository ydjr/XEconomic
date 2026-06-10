"""
XEconomic โ€” Pipeline Orchestrator
===================================
Master script that runs all pipeline steps in sequence.

Usage:
    python run_pipeline.py --all                # Run everything
    python run_pipeline.py --phase news         # Only news processing
    python run_pipeline.py --phase train        # Only training + prediction
    python run_pipeline.py --phase explain      # Only LLM explainability
    python run_pipeline.py --phase assets       # Only entity + wordcloud
    python run_pipeline.py --phase serve        # Only start servers
    python run_pipeline.py --from train         # Start from training phase onwards
    python run_pipeline.py --skip-llm           # Skip LLM-heavy steps
    python run_pipeline.py --check              # Validate environment only
    python run_pipeline.py --force              # Force re-run (ignore existing outputs)
"""

import argparse
import subprocess
import sys
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# โ”€โ”€โ”€ import config โ”€โ”€โ”€
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from config import Dirs, Files, HF_LLM, WangchanBERTa, Server

# โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€
# LOGGING
# โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€
Dirs.LOGS.mkdir(parents=True, exist_ok=True)
LOG_FILE = Dirs.LOGS / f"pipeline_{datetime.now().strftime('%Y-%m')}.log"

# Fix Windows console encoding for Thai characters
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("pipeline")


# โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€
# HELPERS
# โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€
PYTHON = sys.executable
DIVIDER = "=" * 60


def run_script(script_path: Path, label: str, args: list = None, cwd: Path = None):
    """Run a Python script as a subprocess."""
    cmd = [PYTHON, str(script_path)]
    if args:
        cmd.extend(args)
    work_dir = str(cwd or ROOT)

    log.info(f">>> {label}")
    log.info(f"    CMD: {' '.join(cmd)}")
    log.info(f"    CWD: {work_dir}")

    start = time.time()
    result = subprocess.run(
        cmd,
        cwd=work_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.time() - start

    if result.stdout:
        for line in result.stdout.strip().split("\n")[-10:]:  # last 10 lines
            log.info(f"    | {line}")

    if result.returncode != 0:
        log.error(f"    [FAIL] in {elapsed:.1f}s (exit code {result.returncode})")
        if result.stderr:
            for line in result.stderr.strip().split("\n")[-15:]:
                log.error(f"    | {line}")
        return False

    log.info(f"    [OK] Done in {elapsed:.1f}s")
    return True


def run_command(cmd: list, label: str, cwd: Path = None):
    """Run a shell command."""
    work_dir = str(cwd or ROOT)
    log.info(f">>> {label}")
    log.info(f"    CMD: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        cwd=work_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        log.error(f"    [FAIL]: {result.stderr[:200] if result.stderr else 'unknown error'}")
        return False
    return True


def check_file(path: Path, label: str) -> bool:
    """Check if a file exists."""
    exists = path.exists()
    status = "[OK]" if exists else "[--]"
    log.info(f"    {status} {label}: {path.name}")
    return exists


def check_ollama() -> bool:
    """Check if Ollama server is running."""
    try:
        import requests
        r = requests.get(Ollama.URL.replace("/api/generate", ""), timeout=5)
        return r.status_code == 200
    except Exception:
        return False


# โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€
# PIPELINE STEPS
# โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€

# Step definitions: (phase, label, script_path, requires_llm, output_check_file)
STEPS = [
    # Phase: news
    ("news", "Step 1: Preprocess news data",
     Dirs.NEWS_PREP / "1_preprocess.py", False,
     Dirs.CLEANED_NEWS / "all_news.csv"),

    ("news", "Step 2: Relevance filter (WangchanBERTa)",
     Dirs.NEWS_PREP / "2_relevance_filter.py", False,
     Dirs.PIPELINE_DATA / "2_news_cci_r.csv"),

    ("news", "Step 3: ABSA via LLM (Ollama)",
     Dirs.NEWS_PREP / "3_absa.py", True,
     Dirs.PIPELINE_DATA / "3_absa_results"),

    ("news", "Step 4: Extract aspect features",
     Dirs.NEWS_PREP / "4_ft_extract.py", False,
     Files.ASPECT_FEATURES),

    ("news", "Step 5: Consolidate dataset",
     Dirs.NEWS_PREP / "5_consolidate.py", False,
     Files.AVG_SENT_INDI),

    # Phase: train
    ("train", "Step 6: Backtest models (GridSearch)",
     Dirs.PIPELINE / "backtest.py", False,
     Files.XGB_BEST_PARAMS),

    ("train", "Step 7: Train best model",
     Dirs.PIPELINE / "train.py", False,
     Files.XGB_WEIGHTS),

    ("train", "Step 8: Predict + SHAP",
     Dirs.PIPELINE / "predict_latest.py", False,
     Files.SHAP_RANK_CSV),

    # Phase: explain
    ("explain", "Step 9: SHAP post-processing",
     Dirs.SHAP_DIR / "prep.py", False,
     Dirs.SHAP_RESULT / "shap_latest.csv"),

    ("explain", "Step 10: 3-month aspect summary (Ollama LLM)",
     Dirs.TEXT_SUM / "3mshapaspectsum.py", True,
     None),

    ("explain", "Step 11: Reasoning generation (Ollama LLM)",
     Dirs.REASONING / "script4_oneshot.py", True,
     None),

    # Phase: assets
    ("assets", "Step 12: Extract entities",
     Dirs.PIPELINE / "extract_entities.py", False,
     Files.TOP_ENTITIES_JSON),

    ("assets", "Step 13: Generate word cloud",
     Dirs.PIPELINE / "generate_wordcloud.py", False,
     Files.WORDCLOUD_PNG),
]

PHASE_ORDER = ["fetch", "news", "train", "explain", "assets", "serve"]


# โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€
# ENVIRONMENT CHECK
# โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€
def check_environment(phases_to_run: list, skip_llm: bool) -> bool:
    """Validate that everything needed is in place."""
    log.info(DIVIDER)
    log.info("ENVIRONMENT CHECK")
    log.info(DIVIDER)
    all_ok = True

    # Python
    log.info(f"  Python: {sys.version.split()[0]}")

    # Key directories
    log.info("\n  Directories:")
    for name, d in [
        ("data/", Dirs.DATA),
        ("data/indicators/", Dirs.INDICATORS),
        ("pipeline/", Dirs.PIPELINE),
        ("artifacts/", Dirs.ARTIFACTS),
        ("models/", Dirs.MODELS),
        ("dashboard/", Dirs.DASHBOARD),
    ]:
        exists = d.exists()
        log.info(f"    {'[OK]' if exists else '[--]'} {name}")
        if not exists:
            all_ok = False

    # Key data files
    log.info("\n  Data files:")
    for label, f in [
        ("avg_sent_indi.csv", Files.AVG_SENT_INDI),
        ("indicators/cci.csv", Files.CCI_CSV),
        ("2017-2026.csv (news)", Files.FULL_NEWS_CSV),
    ]:
        check_file(f, label)

    # Ollama (if LLM steps are included)
    if not skip_llm and any(p in phases_to_run for p in ["news", "explain"]):
        log.info("\n  Ollama LLM server:")
        ollama_ok = check_ollama()
        log.info(f"    {'[OK]' if ollama_ok else '[--]'} Ollama at {Ollama.URL}")
        if not ollama_ok:
            log.warning("    [!] Ollama not running -- LLM steps will fail")
            log.warning("    [!] Start with: ollama serve")

    # Node.js (if serving)
    if "serve" in phases_to_run:
        log.info("\n  Node.js:")
        node_ok = run_command(["node", "--version"], "Node.js version check")
        if not node_ok:
            log.warning("    [!] Node.js not found -- dashboard won't start")

        # Check node_modules
        nm = Dirs.DASHBOARD / "node_modules"
        log.info(f"    {'[OK]' if nm.exists() else '[--]'} dashboard/node_modules")
        if not nm.exists():
            log.info("    -> Running npm install...")
            run_command(["npm", "install"], "npm install", cwd=Dirs.DASHBOARD)

    log.info(DIVIDER)
    return all_ok


# โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€
# SERVE
# โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€
def start_servers():
    """Start FastAPI backend + Vite frontend."""
    log.info(DIVIDER)
    log.info("STARTING SERVERS")
    log.info(DIVIDER)

    # Start FastAPI in background
    log.info("  Starting FastAPI backend...")
    api_proc = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "api.main:app",
         "--host", Server.API_HOST,
         "--port", str(Server.API_PORT),
         "--reload"],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    log.info(f"    [OK] FastAPI PID={api_proc.pid} -> http://localhost:{Server.API_PORT}")

    time.sleep(2)

    # Start Vite frontend in background
    log.info("  Starting Vite frontend...")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    vite_proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=str(Dirs.DASHBOARD),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    log.info(f"    [OK] Vite PID={vite_proc.pid} -> http://localhost:{Server.VITE_PORT}")

    log.info(DIVIDER)
    log.info(f"  Dashboard ready at: http://localhost:{Server.VITE_PORT}")
    log.info(f"  API health check:   http://localhost:{Server.API_PORT}/health")
    log.info("  Press Ctrl+C to stop all servers")
    log.info(DIVIDER)

    try:
        api_proc.wait()
    except KeyboardInterrupt:
        log.info("\n  Shutting down servers...")
        api_proc.terminate()
        vite_proc.terminate()
        api_proc.wait(timeout=5)
        vite_proc.wait(timeout=5)
        log.info("  [OK] Servers stopped")


# โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€
# MAIN PIPELINE RUNNER
# โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€
def run_pipeline(phases: list, skip_llm: bool = False, force: bool = False):
    """Run pipeline steps for the given phases."""
    log.info(DIVIDER)
    log.info("RUNNING PIPELINE")
    log.info(f"  Phases: {', '.join(phases)}")
    log.info(f"  Skip LLM: {skip_llm}")
    log.info(f"  Force: {force}")
    log.info(DIVIDER)

    total = 0
    passed = 0
    skipped = 0
    failed = 0

    for phase, label, script_path, requires_llm, output_check in STEPS:
        if phase not in phases:
            continue

        total += 1
        log.info("")

        # Skip LLM steps if requested
        if requires_llm and skip_llm:
            log.info(f"--- {label}  [SKIPPED - LLM]")
            skipped += 1
            continue

        # Skip if output already exists (unless --force)
        if not force and output_check and Path(output_check).exists():
            log.info(f"--- {label}  [SKIPPED - output exists]")
            skipped += 1
            continue

        # Check script exists
        if not script_path.exists():
            log.error(f"[FAIL] {label}  [MISSING: {script_path}]")
            failed += 1
            continue

        # Run the step
        ok = run_script(script_path, label, cwd=ROOT)
        if ok:
            passed += 1
        else:
            failed += 1
            log.error(f"\n{'=' * 60}")
            log.error(f"PIPELINE STOPPED -- Step failed: {label}")
            log.error(f"Fix the error above and re-run with: python run_pipeline.py --from {phase}")
            log.error(f"{'=' * 60}")
            break

    # Summary
    log.info("")
    log.info(DIVIDER)
    log.info("PIPELINE SUMMARY")
    log.info(f"  Total:   {total}")
    log.info(f"  Passed:  {passed}")
    log.info(f"  Skipped: {skipped}")
    log.info(f"  Failed:  {failed}")
    log.info(f"  Log:     {LOG_FILE}")
    log.info(DIVIDER)

    # Start servers if 'serve' is in phases
    if "serve" in phases and failed == 0:
        start_servers()

    return failed == 0


# โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€
# CLI
# โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€โ”€
def main():
    parser = argparse.ArgumentParser(
        description="XEconomic Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py --all              Run entire pipeline
  python run_pipeline.py --phase train      Run only training phase
  python run_pipeline.py --phase serve      Start dashboard servers
  python run_pipeline.py --from train       Run from training phase onwards
  python run_pipeline.py --skip-llm         Skip LLM-heavy steps
  python run_pipeline.py --check            Validate environment only
  python run_pipeline.py --force --all      Force re-run all steps
        """,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true",
                       help="Run all phases")
    group.add_argument("--phase", choices=PHASE_ORDER,
                       help="Run a specific phase")
    group.add_argument("--from", dest="from_phase", choices=PHASE_ORDER,
                       help="Run from this phase onwards")
    group.add_argument("--check", action="store_true",
                       help="Only validate environment")

    parser.add_argument("--skip-llm", action="store_true",
                        help="Skip LLM-heavy steps (ABSA, summarization, reasoning)")
    parser.add_argument("--force", action="store_true",
                        help="Force re-run even if outputs exist")

    args = parser.parse_args()

    log.info("=" * 60)
    log.info("   XEconomic Pipeline Orchestrator")
    log.info(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)

    # Determine which phases to run
    if args.all:
        phases = PHASE_ORDER[:]
    elif args.phase:
        phases = [args.phase]
    elif args.from_phase:
        idx = PHASE_ORDER.index(args.from_phase)
        phases = PHASE_ORDER[idx:]
    elif args.check:
        phases = PHASE_ORDER[:]
    else:
        phases = []

    # Environment check
    check_environment(phases, args.skip_llm)

    if args.check:
        log.info("Environment check complete. Use --all or --phase to run.")
        return

    # Run pipeline
    success = run_pipeline(phases, skip_llm=args.skip_llm, force=args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
