import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.data.features import FEATURE_COLS, TARGET_COL

# exclude near-zero windows from MAPE — a window with 2 actual pax and 8
# predicted is a 300% error that dominates and doesn't reflect real performance
MAPE_MIN_PAX = 10


def evaluate(
    model: XGBRegressor,
    feature_matrix: pd.DataFrame,
    feature_cols: list[str] | None = None,
) -> dict:
    cols = feature_cols if feature_cols else FEATURE_COLS
    df = feature_matrix.dropna(subset=cols + [TARGET_COL])
    X  = df[cols]
    y  = df[TARGET_COL].values

    preds = model.predict(X)

    mae  = mean_absolute_error(y, preds)
    rmse = np.sqrt(mean_squared_error(y, preds))
    mask = y >= MAPE_MIN_PAX
    mape = np.mean(np.abs((y[mask] - preds[mask]) / y[mask])) * 100 if mask.any() else float("nan")

    return {"MAE": round(mae, 2), "RMSE": round(rmse, 2), "MAPE_%": round(mape, 2)}
