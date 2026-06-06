import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="AirHack 2026 — Passenger Flow",
    page_icon="✈️",
    layout="wide",
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("✈️ Passenger Flow Predictor")
    st.caption("AirHack 2026 | Check-in Operations")
    st.divider()

    with st.expander("Claude API Key", expanded=not st.session_state.get("api_key")):
        key_input = st.text_input(
            "Anthropic API key",
            value=st.session_state.get("api_key", ""),
            type="password",
            placeholder="sk-ant-...",
            help="Get yours at console.anthropic.com — only needed for AI Insights",
        )
        if key_input != st.session_state.get("api_key", ""):
            st.session_state["api_key"] = key_input
            st.rerun()
        if st.session_state.get("api_key"):
            st.success("API key set")
        else:
            st.info("No key — AI Insights will use auto-summary")

    st.divider()
    page = st.radio("View", ["Train Model", "Forecast", "Alerts", "AI Insights", "Settings"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def fetch_json(url, **kwargs):
    try:
        r = requests.get(url, timeout=5, **kwargs)
        return r.json() if r.ok else None
    except Exception:
        return None


def fetch_forecast() -> pd.DataFrame:
    try:
        r = requests.get(f"{API_BASE}/forecast", timeout=5)
        if r.ok:
            df = pd.DataFrame(r.json())
            if not df.empty:
                df["window_start"] = pd.to_datetime(df["window_start"])
            return df
    except Exception:
        pass
    return pd.DataFrame()


def fetch_alerts(status=None) -> pd.DataFrame:
    try:
        params = {"status": status} if status else {}
        r = requests.get(f"{API_BASE}/alerts", params=params, timeout=5)
        if r.ok:
            return pd.DataFrame(r.json())
    except Exception:
        pass
    return pd.DataFrame()


# ── Train Model ───────────────────────────────────────────────────────────────

if page == "Train Model":
    st.header("Train Model on Historical Data")
    st.caption("Upload past flight schedules so the model learns passenger load patterns.")

    # training data status
    info = fetch_json(f"{API_BASE}/data/training/info")
    if info and info.get("loaded"):
        st.success(f"Training dataset: **{info['flights']:,} flights** | {info['date_from'][:10]} → {info['date_to'][:10]}")
        if st.button("Clear training data", type="secondary"):
            requests.post(f"{API_BASE}/data/upload/training/clear")
            st.rerun()
    else:
        st.warning("No training data loaded yet.")

    st.divider()

    uploaded = st.file_uploader(
        "Upload historical flight CSV (can upload multiple files — they stack)",
        type=["csv"],
        key="training_upload",
    )
    if uploaded:
        with st.spinner("Loading…"):
            resp = requests.post(
                f"{API_BASE}/data/upload/training",
                files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")},
            )
        if resp.ok:
            d = resp.json()
            st.success(f"Loaded — dataset now has **{d['flights_loaded']:,} flights** from {d['date_range']['from'][:10]} to {d['date_range']['to'][:10]}")
            st.rerun()
        else:
            st.error(f"Upload failed: {resp.text}")

    st.divider()

    if st.button("Train Model", type="primary", use_container_width=True):
        with st.spinner("Training XGBoost…"):
            r = requests.post(f"{API_BASE}/forecast/train", timeout=120)
        if r.ok:
            d = r.json()
            st.success("Model trained successfully!")
            m = d.get("metrics", {})
            c1, c2, c3 = st.columns(3)
            c1.metric("MAE", f"{m.get('MAE', '—')} pax")
            c2.metric("RMSE", f"{m.get('RMSE', '—')} pax")
            c3.metric("MAPE", f"{m.get('MAPE_%', '—')}%")
        else:
            st.error(f"Training failed: {r.text}")


# ── Forecast ──────────────────────────────────────────────────────────────────

elif page == "Forecast":
    st.header("Forecast Upcoming Schedule")
    st.caption("Upload tomorrow's flight schedule and predict passenger load per 30-min window.")

    info = fetch_json(f"{API_BASE}/data/schedule/info")
    if info and info.get("loaded"):
        st.success(f"Schedule loaded: **{info['flights']:,} flights** | {info['date_from'][:10]} → {info['date_to'][:10]}")
    else:
        st.warning("No schedule uploaded yet.")

    uploaded = st.file_uploader("Upload upcoming flight schedule CSV", type=["csv"], key="schedule_upload")
    if uploaded:
        with st.spinner("Loading…"):
            resp = requests.post(
                f"{API_BASE}/data/upload/schedule",
                files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")},
            )
        if resp.ok:
            d = resp.json()
            st.success(f"Schedule loaded: **{d['flights_loaded']} flights**")
            st.rerun()
        else:
            st.error(f"Upload failed: {resp.text}")

    if st.button("Run Forecast & Generate Alerts", type="primary", use_container_width=True):
        with st.spinner("Predicting…"):
            r = requests.post(f"{API_BASE}/forecast/run", timeout=120)
        if r.ok:
            d = r.json()
            st.success(f"Done — {d['windows_predicted']} windows predicted, {d['alerts_generated']} alerts generated")
            st.rerun()
        else:
            st.error(f"Forecast failed: {r.text}")

    st.divider()

    forecast = fetch_forecast()
    if not forecast.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Windows", len(forecast))
        c2.metric("Peak Load", int(forecast["predicted_load"].max()))
        c3.metric("Total Pax", int(forecast["predicted_load"].sum()))

        fig = px.bar(
            forecast,
            x="window_start",
            y="predicted_load",
            labels={"window_start": "Time Window", "predicted_load": "Predicted Passengers"},
            color="predicted_load",
            color_continuous_scale="RdYlGn_r",
            title="Predicted Passenger Load — 30-min Windows",
        )
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            forecast.rename(columns={"window_start": "Window", "predicted_load": "Predicted Pax"}),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No forecast yet — upload a schedule and click Run Forecast.")


# ── Alerts ────────────────────────────────────────────────────────────────────

elif page == "Alerts":
    st.header("Check-in Desk Alerts")

    tab_open, tab_ack, tab_all = st.tabs(["OPEN", "ACKNOWLEDGED", "ALL"])

    def render_alerts(df: pd.DataFrame, show_ack: bool = False):
        if df.empty:
            st.info("No alerts in this category.")
            return
        for _, row in df.iterrows():
            status_color = {"OPEN": "🔴", "ACKNOWLEDGED": "🟡", "RESOLVED": "🟢"}.get(row["status"], "⚪")
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"{status_color} **{row['message']}**")
                c1.caption(f"Window: {row['window_start']} | Desks needed: {row.get('desks_to_open', '?')} | Pax: {row.get('predicted_load', '?')}")
                if show_ack and row["status"] == "OPEN":
                    emp = st.session_state.get("employee_name", "employee")
                    if c2.button("Acknowledge", key=f"ack_{row['id']}"):
                        requests.post(
                            f"{API_BASE}/alerts/{row['id']}/acknowledge",
                            json={"employee": emp},
                        )
                        st.rerun()

    with tab_open:
        st.session_state["employee_name"] = st.text_input("Your name (for audit trail)", value="Employee")
        render_alerts(fetch_alerts("OPEN"), show_ack=True)

    with tab_ack:
        render_alerts(fetch_alerts("ACKNOWLEDGED"))

    with tab_all:
        render_alerts(fetch_alerts())


# ── AI Insights ───────────────────────────────────────────────────────────────

elif page == "AI Insights":
    st.header("AI Operational Insights")
    st.caption("Powered by Claude (claude-opus-4-8) with adaptive thinking")

    question = st.text_area(
        "Ask a question (leave blank for auto-summary)",
        placeholder="e.g. Which hour needs the most check-in desks?",
        height=80,
    )

    if st.button("Get Insights", type="primary"):
        with st.spinner("Thinking…"):
            try:
                r = requests.post(
                    f"{API_BASE}/insights",
                    json={"question": question or None, "api_key": st.session_state.get("api_key") or None},
                    timeout=120,
                )
                if r.ok:
                    st.markdown(r.json()["insight"])
                else:
                    st.error(f"API error: {r.text}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot reach API. Make sure the FastAPI server is running.")


# ── Settings ──────────────────────────────────────────────────────────────────

elif page == "Settings":
    st.header("Alert Thresholds")

    try:
        r = requests.get(f"{API_BASE}/thresholds", timeout=5)
        if not r.ok:
            st.error("Could not load thresholds")
            st.stop()
        cfg = r.json()["checkin"]
    except Exception as e:
        st.error(f"Could not connect to API: {e}")
        st.stop()

    with st.form("thresholds_form"):
        cols = st.columns(3)
        levels = {}
        for i, (key, col) in enumerate(zip(["level_1", "level_2", "level_3"], cols)):
            with col:
                st.subheader(f"Level {i+1}")
                lvl = cfg[key]
                levels[key] = {
                    "threshold": st.number_input("Threshold (pax)", value=lvl["threshold"], min_value=1, key=f"t_{key}"),
                    "desks_to_open": st.number_input("Desks to open", value=lvl["desks_to_open"], min_value=1, key=f"d_{key}"),
                    "message": st.text_input("Alert message", value=lvl["message"], key=f"m_{key}"),
                }

        if st.form_submit_button("Save Thresholds", type="primary"):
            resp = requests.post(f"{API_BASE}/thresholds", json=levels)
            if resp.ok:
                st.success("Thresholds saved!")
            else:
                st.error(f"Save failed: {resp.text}")
