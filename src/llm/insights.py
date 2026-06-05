import anthropic
import pandas as pd

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
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


def get_insights(
    predictions: pd.DataFrame,
    alerts: list[dict],
    question: str | None = None,
) -> str:
    client = _get_client()
    prompt = _build_prompt(predictions, alerts, question)

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=16000,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    )

    # extract text blocks (skip thinking blocks)
    texts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(texts)
