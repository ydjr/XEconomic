import os
import json
import numpy as np
import pandas as pd


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def save_csv(df: pd.DataFrame, path: str):
    folder = os.path.dirname(path)
    if folder:
        ensure_dir(folder)
    df.to_csv(path, index=False)
    print("Saved:", path)


def save_json(obj, path: str):
    folder = os.path.dirname(path)
    if folder:
        ensure_dir(folder)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print("Saved:", path)


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    denom = np.where(np.abs(y_true) < 1e-8, np.nan, np.abs(y_true))
    return float(np.nanmean(np.abs((y_pred - y_true) / denom)) * 100.0)
