import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

from src.data.features import FEATURE_COLS, TARGET_COL

MODEL_PATH = Path(__file__).parents[2] / "models" / "model.pkl"


def train(feature_matrix: pd.DataFrame, save: bool = True) -> XGBRegressor:
    df = feature_matrix.dropna(subset=FEATURE_COLS + [TARGET_COL])

    X = df[FEATURE_COLS]
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
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        print(f"Model saved → {MODEL_PATH}")

    return model


def load_model() -> XGBRegressor:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No trained model at {MODEL_PATH}. Run pipeline.py train first.")
    return joblib.load(MODEL_PATH)
