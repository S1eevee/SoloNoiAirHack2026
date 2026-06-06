import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

from src.data.features import FEATURE_COLS, TARGET_COL

MODEL_PATH = Path(__file__).parents[2] / "models" / "model.pkl"


def train(
    feature_matrix: pd.DataFrame,
    save: bool = True,
    model_path: Path | None = None,
    feature_cols: list[str] | None = None,
) -> XGBRegressor:
    path = Path(model_path) if model_path else MODEL_PATH
    cols = feature_cols if feature_cols else FEATURE_COLS

    df = feature_matrix.dropna(subset=cols + [TARGET_COL])

    X = df[cols]
    y = df[TARGET_COL]

    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBRegressor(
        n_estimators=1000,
        max_depth=5,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        reg_alpha=0.1,
        reg_lambda=1.5,
        random_state=42,
        n_jobs=1,
        early_stopping_rounds=50,
        eval_metric="mae",
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    if save:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, path)
        print(f"Model saved → {path}")

    return model


_model_cache: dict = {"model": None, "mtime": None}

def load_model(model_path: Path | None = None) -> XGBRegressor:
    path = Path(model_path) if model_path else MODEL_PATH
    if not path.exists():
        raise FileNotFoundError(f"No trained model at {path}.")
    mtime = path.stat().st_mtime
    cache_key = str(path)
    if _model_cache.get(cache_key) is None or _model_cache.get(f"{cache_key}_mtime") != mtime:
        _model_cache[cache_key] = joblib.load(path)
        _model_cache[f"{cache_key}_mtime"] = mtime
    return _model_cache[cache_key]
