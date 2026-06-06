# src/llm/

Claude API integration. Generates natural language operational insights from XGBoost predictions and active alerts.

## Files

### `insights.py`

**Key function:** `get_insights(predictions, alerts, question=None, api_key=None)`

**Behaviour:**
- If an API key is available (from argument or `ANTHROPIC_API_KEY` env var): calls Claude `claude-opus-4-8` with adaptive thinking
- If no key: returns a rule-based auto-summary (top 3 peak windows, risk flags, staffing recommendations) — fully functional for demos without a paid API key

**Model:** `claude-opus-4-8` with `thinking={"type": "adaptive"}`  
**Max tokens:** 16,000

## Prompt Structure
The prompt sent to Claude contains:
1. Predicted passenger load table (all 30-min windows)
2. Active OPEN alerts list
3. Either a free-form manager question or a default operational summary request

## Fallback (no API key)
Returns a structured markdown summary built directly from prediction data:
- Top 3 busiest windows with pax counts
- HIGH LOAD risk flags (≥500 pax)
- Staffing recommendations based on active alert count and desks needed

## API Key Sources (checked in order)
1. `api_key` argument passed from the request body
2. `ANTHROPIC_API_KEY` environment variable
3. If neither → fallback mode

## Notes
- Get an API key at console.anthropic.com
- The key can be entered in the dashboard sidebar without restarting anything
- Claude is used for insights only — all predictions and alerts work without it
