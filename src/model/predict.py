import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from src.data.features import FEATURE_COLS


def predict(model: XGBRegressor, feature_matrix: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame with window_start + predicted_load."""
    X = feature_matrix[FEATURE_COLS]
    preds = model.predict(X)
    preds = np.clip(preds, 0, None).round().astype(int)

    result = feature_matrix[["window_start"]].copy()
    result["predicted_load"] = preds
    return result


def predict_next_day(model: XGBRegressor, schedule_df: pd.DataFrame) -> pd.DataFrame:
    """Build features from tomorrow's schedule and predict load per 30-min window."""
    from src.data.cleaner import clean_flights
    from src.data.features import build_feature_matrix

    clean = clean_flights(schedule_df)
    features = build_feature_matrix(clean)
    return predict(model, features)
