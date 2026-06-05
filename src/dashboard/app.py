import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
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

    uploaded = st.file_uploader("Upload flight schedule (CSV)", type=["csv"])
    if uploaded:
        resp = requests.post(
            f"{API_BASE}/data/upload",
            files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")},
        )
        if resp.ok:
            d = resp.json()
            st.success(f"Loaded {d['flights_loaded']} flights")
        else:
            st.error(f"Upload failed: {resp.text}")

    if st.button("Run Forecast & Generate Alerts", type="primary", use_container_width=True):
        with st.spinner("Training XGBoost + generating alerts…"):
            r = requests.post(f"{API_BASE}/forecast/run")
        if r.ok:
            d = r.json()
            st.success(f"Forecast done: {d['windows_predicted']} windows, {d['alerts_generated']} alerts")
            st.rerun()
        else:
            st.error(f"Forecast failed: {r.text}")

    st.divider()
    page = st.radio("View", ["Dashboard", "Alerts", "AI Insights", "Settings"])

# ── Fetch data helpers ────────────────────────────────────────────────────────

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


# ── Pages ─────────────────────────────────────────────────────────────────────

if page == "Dashboard":
    st.header("Passenger Load Forecast")
    forecast = fetch_forecast()

    if forecast.empty:
        st.info("No forecast available yet. Upload a schedule and click **Run Forecast**.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Windows", len(forecast))
        col2.metric("Peak Load", int(forecast["predicted_load"].max()))
        col3.metric("Total Pax", int(forecast["predicted_load"].sum()))

        # Load chart
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

        # Alert overlay thresholds
        try:
            r = requests.get(f"{API_BASE}/thresholds", timeout=3)
            if r.ok:
                thresholds = r.json()["checkin"]
                for lvl in thresholds.values():
                    fig.add_hline(
                        y=lvl["threshold"],
                        line_dash="dot",
                        annotation_text=f"Threshold {lvl['threshold']}",
                        annotation_position="top right",
                    )
        except Exception:
            pass

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Window Detail")
        st.dataframe(
            forecast.rename(columns={"window_start": "Window", "predicted_load": "Predicted Pax"}),
            use_container_width=True,
            hide_index=True,
        )


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
                    if c2.button("Acknowledge", key=f"ack_{row['id']}"):
                        emp = st.session_state.get("employee_name", "employee")
                        requests.post(
                            f"{API_BASE}/alerts/{row['id']}/acknowledge",
                            json={"employee": emp},
                        )
                        st.rerun()

    with tab_open:
        emp = st.text_input("Your name (for audit trail)", value="Employee", key="employee_name")
        open_alerts = fetch_alerts("OPEN")
        render_alerts(open_alerts, show_ack=True)

    with tab_ack:
        render_alerts(fetch_alerts("ACKNOWLEDGED"))

    with tab_all:
        render_alerts(fetch_alerts())


elif page == "AI Insights":
    st.header("AI Operational Insights")
    st.caption("Powered by Claude (claude-opus-4-8) with adaptive thinking")

    question = st.text_area(
        "Ask a question (leave blank for auto-summary)",
        placeholder="e.g. Which hour needs the most check-in desks? Should we call in extra staff?",
        height=80,
    )

    if st.button("Get Insights", type="primary"):
        with st.spinner("Claude is thinking…"):
            try:
                r = requests.post(
                    f"{API_BASE}/insights",
                    json={
                        "question": question or None,
                        "api_key": st.session_state.get("api_key") or None,
                    },
                    timeout=120,
                )
                if r.ok:
                    st.markdown(r.json()["insight"])
                else:
                    st.error(f"API error: {r.text}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot reach API. Make sure the FastAPI server is running.")


elif page == "Settings":
    st.header("Alert Thresholds")
    st.caption("Configure passenger load thresholds for check-in desk alerts")

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
