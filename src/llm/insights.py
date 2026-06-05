import os
import pandas as pd

_client = None


def _has_api_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())


def _get_client():
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.Anthropic()
    return _client


def _build_prompt(predictions: pd.DataFrame, alerts: list[dict], question: str | None) -> str:
    pred_table = predictions.to_string(index=False)
    alert_lines = "\n".join(
        f"- [{a['status']}] {a['message']}" for a in alerts
    ) or "No alerts generated."

    base = f"""You are an airport operations analyst assistant.

PREDICTED PASSENGER LOAD (next operational period, 30-min windows):
{pred_table}

ACTIVE CHECK-IN ALERTS:
{alert_lines}

"""
    if question:
        base += f"Airport manager question: {question}\n\nProvide a concise, actionable answer."
    else:
        base += (
            "Provide a brief operational summary: identify the top 3 busiest windows, "
            "flag any risk periods, and give 2-3 specific staffing recommendations for check-in desks."
        )
    return base


def _fallback_insights(predictions: pd.DataFrame, alerts: list[dict], question: str | None) -> str:
    """Rule-based summary used when no API key is configured."""
    if predictions.empty:
        return "No prediction data available."

    top3 = predictions.nlargest(3, "predicted_load")
    peak_lines = "\n".join(
        f"  • {pd.Timestamp(r['window_start']).strftime('%H:%M')} — {r['predicted_load']} pax"
        for _, r in top3.iterrows()
    )

    high_load = predictions[predictions["predicted_load"] >= 500]
    risk_msg = (
        f"  ⚠️  HIGH LOAD windows (≥500 pax): "
        + ", ".join(pd.Timestamp(w).strftime("%H:%M") for w in high_load["window_start"])
        if not high_load.empty
        else "  No extreme load windows detected."
    )

    open_alerts = [a for a in alerts if a.get("status") == "OPEN"]
    alert_count = len(open_alerts)
    desks_needed = sum(a.get("desks_to_open", 0) for a in open_alerts)

    summary = f"""**Operational Summary (auto-generated)**

**Top 3 busiest windows:**
{peak_lines}

**Risk assessment:**
{risk_msg}

**Staffing recommendations:**
  1. {alert_count} active check-in alerts requiring {desks_needed} additional desk openings.
  2. Pre-position extra staff 15 minutes before peak windows to avoid queue build-up.
  3. Monitor the {pd.Timestamp(top3.iloc[0]['window_start']).strftime('%H:%M')} window closely — highest predicted load of {int(top3.iloc[0]['predicted_load'])} passengers.

---
*AI Insights unavailable — set ANTHROPIC_API_KEY to enable Claude-powered analysis.*"""

    if question:
        return (
            f"**Question:** {question}\n\n"
            f"*(Live AI answer unavailable — set ANTHROPIC_API_KEY to enable Claude)*\n\n"
            + summary
        )
    return summary


def get_insights(
    predictions: pd.DataFrame,
    alerts: list[dict],
    question: str | None = None,
    api_key: str | None = None,
) -> str:
    resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not resolved_key:
        return _fallback_insights(predictions, alerts, question)

    import anthropic
    client = anthropic.Anthropic(api_key=resolved_key)
    prompt = _build_prompt(predictions, alerts, question)

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=16000,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    )

    texts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(texts)
