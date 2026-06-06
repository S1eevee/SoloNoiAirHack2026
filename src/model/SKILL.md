# src/model/

XGBoost training, inference, and evaluation. Stateless — reads from `data/processed/` and writes `models/model.pkl`.

## Files

### `train.py`
Trains an `XGBRegressor` on the feature matrix produced by `src/data/features.py`.

- Splits 80/20 train/validation
- Uses early-stopping-compatible eval set
- Saves model to `models/model.pkl` via `joblib`

**Key functions:**
- `train(feature_matrix, save=True)` — fit and optionally save
- `load_model()` — load saved model; raises `FileNotFoundError` if not trained yet

### `predict.py`
Loads the saved model and runs inference.

**Key functions:**
- `predict(model, feature_matrix)` — returns DataFrame with `window_start` + `predicted_load`
- `predict_next_day(model, schedule_df)` — convenience wrapper: clean → features → predict

### `evaluate.py`
Computes regression metrics on any labelled feature matrix.

**Returns:** `{ MAE, RMSE, MAPE_% }`

## XGBoost Hyperparameters
| Param | Value | Why |
|---|---|---|
| n_estimators | 300 | Enough trees without overfitting on small data |
| max_depth | 6 | Captures non-linear interactions |
| learning_rate | 0.05 | Conservative — needs more trees but generalises better |
| subsample | 0.8 | Reduces overfitting via row sampling |
| colsample_bytree | 0.8 | Reduces overfitting via feature sampling |

## Notes
- Model accuracy improves significantly with more historical data (2+ weeks recommended)
- Retrain whenever new historical data is available via the Train Model tab in the dashboard
