# src/dashboard/

Streamlit employee-facing web application. Communicates exclusively with the FastAPI backend at `http://localhost:8000`.

## Entry Point
```bash
python3 -m streamlit run src/dashboard/app.py
```
Opens at: http://localhost:8501

## Navigation Tabs

### Train Model
For airport administrators. Upload historical flight CSVs to build the training dataset. Multiple uploads stack (deduplicated by `flight_id`). Shows dataset stats and triggers XGBoost training. Displays MAE/RMSE/MAPE after training.

### Forecast
For operations managers. Upload tomorrow's flight schedule and run the prediction. Shows a colour-coded bar chart of predicted passenger load per 30-min window. Automatically generates check-in desk alerts.

### Alerts
For check-in desk supervisors. Shows OPEN alerts with acknowledge button. Employee enters their name for the audit trail. Tabs for OPEN / ACKNOWLEDGED / ALL.

### AI Insights
Natural language operational summary powered by Claude `claude-opus-4-8`. Ask free-form questions or get an automatic summary. Works without an API key (falls back to rule-based summary).

### Settings
Configure alert thresholds for all three levels. Changes are saved to `config/thresholds.yaml` via the API and take effect on the next forecast run.

## Sidebar
- **Claude API Key** — password field, stored in session state, used for AI Insights
- Navigation radio buttons

## Notes
- All state is server-side (FastAPI + SQLite) — refreshing the page is safe
- The dashboard does not import any `src/` Python modules directly — everything goes through HTTP
- Run both the API server and the dashboard simultaneously for full functionality
