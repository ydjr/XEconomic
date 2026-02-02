import argparse
import subprocess
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent

# Define pipeline order (production path)
STEPS = [
    ("preprocess", "1_preprocess.py"),
    ("relevance", "2_relevance_filter.py"),
    ("absa", "3_absa.py"),
    ("consolidate", "4_consolidate.py"),
    ("predict_latest", "predict_latest.py"),
]

OPTIONAL = [
    ("backtest", "backtest.py"),
]

def run_step(script_name: str):
    script_path = PIPELINE_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Missing script: {script_path}")

    print(f"\n=== RUN: {script_name} ===")
    cmd = [sys.executable, str(script_path)]
    subprocess.run(cmd, check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--start-from",
        default="preprocess",
        choices=[s[0] for s in STEPS] + [o[0] for o in OPTIONAL],
        help="Start pipeline from a specific step key",
    )
    ap.add_argument(
        "--mode",
        default="prod",
        choices=["prod", "backtest"],
        help="prod = preprocess→...→predict_latest | backtest = preprocess→...→backtest",
    )
    args = ap.parse_args()

    if args.mode == "prod":
        plan = STEPS
    else:
        plan = [
            ("preprocess", "1_preprocess.py"),
            ("relevance", "2_relevance_filter.py"),
            ("absa", "3_absa.py"),
            ("consolidate", "4_consolidate.py"),
            ("backtest", "backtest.py"),
        ]

    # Find start index
    keys = [k for k, _ in plan]
    if args.start_from not in keys:
        raise ValueError(f"--start-from must be one of: {keys}")

    start_idx = keys.index(args.start_from)
    plan_to_run = plan[start_idx:]

    print("=== PIPELINE PLAN ===")
    for k, s in plan_to_run:
        print(f"- {k}: {s}")

    for _, script in plan_to_run:
        run_step(script)

    print("\n=== DONE ===")

if __name__ == "__main__":
    main()
