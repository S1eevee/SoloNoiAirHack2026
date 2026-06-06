import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="SoloNoi — Passenger Flow",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global styles ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* sidebar */
[data-testid="stSidebar"] {
    background: #0f1117;
}
[data-testid="stSidebar"] * {
    color: #e0e0e0 !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 0.95rem;
    padding: 4px 0;
}

/* page background */
.main .block-container { padding-top: 1.5rem; }

/* alert cards */
.alert-card {
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
    border-left: 5px solid #ccc;
    background: #1e2130;
    color: #e0e0e0;
}
.alert-open  { border-left-color: #e05252; background: #1e1414; }
.alert-close { border-left-color: #52c07a; background: #131e18; }
.alert-ack   { border-left-color: #f0a500; background: #1e1a0e; }
.alert-title { font-size: 1rem; font-weight: 600; margin-bottom: 4px; }
.alert-sub   { font-size: 0.85rem; opacity: 0.75; margin-top: 4px; }
.desk-tag {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 6px;
}
.desk-open  { background: #e0525240; color: #ff8080; }
.desk-close { background: #52c07a40; color: #80ffaa; }
.desk-ok    { background: #52805240; color: #80c080; }

/* metric row */
.kpi-row { display: flex; gap: 16px; margin-bottom: 1rem; }
.kpi-box {
    flex: 1;
    background: #1e2130;
    border-radius: 8px;
    padding: 16px 20px;
    text-align: center;
}
.kpi-val { font-size: 1.8rem; font-weight: 700; color: #fff; }
.kpi-lbl { font-size: 0.78rem; color: #888; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.05em; }

/* status dot */
.dot-green { color: #52c07a; font-size: 0.7rem; }
.dot-red   { color: #e05252; font-size: 0.7rem; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

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


def fetch_security_alerts(status=None) -> pd.DataFrame:
    try:
        params = {"status": status} if status else {}
        r = requests.get(f"{API_BASE}/security/alerts", params=params, timeout=5)
        if r.ok:
            return pd.DataFrame(r.json())
    except Exception:
        pass
    return pd.DataFrame()


def fetch_security_forecast() -> pd.DataFrame:
    try:
        r = requests.get(f"{API_BASE}/security/forecast", timeout=5)
        if r.ok:
            df = pd.DataFrame(r.json())
            if not df.empty:
                df["window_start"] = pd.to_datetime(df["window_start"])
            return df
    except Exception:
        pass
    return pd.DataFrame()


def fetch_gate_alerts(status=None) -> pd.DataFrame:
    try:
        params = {"status": status} if status else {}
        r = requests.get(f"{API_BASE}/gate/alerts", params=params, timeout=5)
        if r.ok:
            return pd.DataFrame(r.json())
    except Exception:
        pass
    return pd.DataFrame()


def fetch_gate_forecast() -> pd.DataFrame:
    try:
        r = requests.get(f"{API_BASE}/gate/forecast", timeout=5)
        if r.ok:
            df = pd.DataFrame(r.json())
            if not df.empty:
                df["window_start"] = pd.to_datetime(df["window_start"])
            return df
    except Exception:
        pass
    return pd.DataFrame()


def api_online() -> bool:
    try:
        return requests.get(f"{API_BASE}/health", timeout=2).ok
    except Exception:
        return False


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## SoloNoi")
    st.markdown("**Passenger Flow Predictor**")
    st.caption("Iași International Airport · IAS")
    st.divider()

    online = api_online()
    desk_resp = fetch_json(f"{API_BASE}/alerts/desks")
    current_desks = desk_resp["desks_open"] if desk_resp else 0
    lane_resp = fetch_json(f"{API_BASE}/security/lanes")
    current_lanes = lane_resp["lanes_open"] if lane_resp else 0
    agent_resp = fetch_json(f"{API_BASE}/gate/agents")
    current_agents = agent_resp["agents_open"] if agent_resp else 0
    open_alerts = len(fetch_alerts("OPEN"))
    open_sec_alerts = len(fetch_security_alerts("OPEN"))
    open_gate_alerts = len(fetch_gate_alerts("OPEN"))

    status_dot = '<span class="dot-green">●</span>' if online else '<span class="dot-red">●</span>'
    status_txt = "API online" if online else "API offline"
    st.markdown(f"{status_dot} {status_txt}", unsafe_allow_html=True)
    st.markdown(f"**{current_desks}** desk(s) &nbsp;·&nbsp; **{open_alerts}** check-in alert(s)", unsafe_allow_html=True)
    st.markdown(f"**{current_lanes}** lane(s) &nbsp;·&nbsp; **{open_sec_alerts}** security alert(s)", unsafe_allow_html=True)
    st.markdown(f"**{current_agents}** agent(s) &nbsp;·&nbsp; **{open_gate_alerts}** gate alert(s)", unsafe_allow_html=True)
    st.divider()

    nav_options = {
        "Train Model": "Train Model",
        "Forecast": "Forecast",
        f"Alerts ({open_alerts} open)" if open_alerts else "Alerts": "Alerts",
        f"Security ({open_sec_alerts} open)" if open_sec_alerts else "Security": "Security",
        f"Gate ({open_gate_alerts} open)" if open_gate_alerts else "Gate": "Gate",
        "Simulation": "Simulation",
        "Settings": "Settings",
    }
    nav_keys = list(nav_options.keys())
    nav_vals  = list(nav_options.values())
    saved_page = st.session_state.get("current_page", "Train Model")
    nav_index  = nav_vals.index(saved_page) if saved_page in nav_vals else 0
    page_raw = st.radio("Navigation", nav_keys, index=nav_index, label_visibility="collapsed")
    page = nav_options[page_raw]
    st.session_state["current_page"] = page

    st.divider()
    demo_status = fetch_json(f"{API_BASE}/demo/status")
    demo_active = demo_status.get("demo_active", False) if demo_status else False
    if demo_active:
        if st.button("✕ Unload Demo", use_container_width=True, help="Clear demo data and return to a clean state"):
            r = requests.post(f"{API_BASE}/demo/unload", timeout=30)
            if r.ok:
                st.session_state["current_page"] = "Train Model"
                st.rerun()
            else:
                st.error(f"Unload failed: {r.text}")
    else:
        if st.button("⚡ Load Demo", use_container_width=True, help="Pre-load 14 days of sample data, train the model, and run forecast in one click"):
            with st.spinner("Loading demo — training model…"):
                r = requests.post(f"{API_BASE}/demo/load", timeout=180)
            if r.ok:
                d = r.json()
                st.success(f"Demo ready · {d['windows_predicted']} windows · {d['alerts_generated']} alerts")
                st.session_state["current_page"] = "Forecast"
                st.rerun()
            else:
                st.error(f"Demo failed: {r.text}")
    st.divider()
    st.caption(f"Today · {datetime.now().strftime('%d %b %Y')}")


# ── Train Model ────────────────────────────────────────────────────────────────

if page == "Train Model":
    st.markdown("## Train Model")
    st.caption("Upload historical flight schedules so the model learns passenger load patterns.")

    info = fetch_json(f"{API_BASE}/data/training/info")
    if info and info.get("loaded"):
        st.success(f"**{info['flights']:,} flights** loaded · {info['date_from'][:10]} → {info['date_to'][:10]}")
        files_in_dataset = info.get("files", [])
        if files_in_dataset:
            with st.expander(f"{len(files_in_dataset)} file(s) in training set", expanded=False):
                for f in files_in_dataset:
                    st.markdown(f"**{f['filename']}** — {f['flights']:,} flights · {f['date_from'][:10]} → {f['date_to'][:10]}")
        if st.button("Clear training data", type="secondary"):
            requests.post(f"{API_BASE}/data/upload/training/clear")
            st.rerun()
    else:
        st.warning("No training data loaded yet.")

    st.divider()

    uploaded_files = st.file_uploader(
        "Drop historical CSVs here — hold Ctrl/Cmd to select multiple",
        type=["csv"],
        key="training_upload",
        accept_multiple_files=True,
    )
    if uploaded_files:
        upload_key = ",".join(f.name + str(f.size) for f in uploaded_files)
        if st.session_state.get("training_last_upload") != upload_key:
            with st.spinner(f"Uploading {len(uploaded_files)} file(s)…"):
                resp = requests.post(
                    f"{API_BASE}/data/upload/training",
                    files=[("files", (f.name, f.getvalue(), "text/csv")) for f in uploaded_files],
                )
            if resp.ok:
                d = resp.json()
                st.session_state["training_last_upload"] = upload_key
                st.success(f"Dataset now has **{d['flights_loaded']:,} flights** · {d['date_range']['from'][:10]} → {d['date_range']['to'][:10]}")
            else:
                st.error(f"Upload failed: {resp.text}")

    st.divider()

    if st.button("Train Model", type="primary", use_container_width=True):
        with st.spinner("Training XGBoost…"):
            r = requests.post(f"{API_BASE}/forecast/train", timeout=120)
        if r.ok:
            d = r.json()
            m = d.get("metrics", {})
            st.success("Model trained successfully")
            st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-box"><div class="kpi-val">{m.get('MAE', '—')}</div><div class="kpi-lbl">Mean Absolute Error (passengers)</div></div>
  <div class="kpi-box"><div class="kpi-val">{m.get('RMSE', '—')}</div><div class="kpi-lbl">Root Mean Square Error (passengers)</div></div>
  <div class="kpi-box"><div class="kpi-val">{m.get('MAPE_%', '—')}%</div><div class="kpi-lbl">Mean Absolute Percentage Error</div></div>
</div>""", unsafe_allow_html=True)
        else:
            st.error(f"Training failed: {r.text}")


# ── Forecast ───────────────────────────────────────────────────────────────────

elif page == "Forecast":
    st.markdown("## Forecast")
    st.caption("Predict passenger load per 30-min window based on tomorrow's schedule.")

    info = fetch_json(f"{API_BASE}/data/schedule/info")
    if info and info.get("loaded"):
        st.success(f"Schedule: **{info['flights']:,} flights** · {info['date_from'][:10]} → {info['date_to'][:10]}")
    else:
        st.warning("No schedule uploaded yet.")

    uploaded = st.file_uploader("Upload upcoming flight schedule CSV", type=["csv"], key="schedule_upload")
    if uploaded and st.session_state.get("schedule_last_upload") != uploaded.name + str(uploaded.size):
        with st.spinner("Loading…"):
            resp = requests.post(
                f"{API_BASE}/data/upload/schedule",
                files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")},
            )
        if resp.ok:
            d = resp.json()
            st.session_state["schedule_last_upload"] = uploaded.name + str(uploaded.size)
            st.success(f"Schedule loaded: **{d['flights_loaded']} flights** — click Run Forecast below")
        else:
            st.error(f"Upload failed: {resp.text}")

    if st.button("Run Forecast & Generate Alerts", type="primary", use_container_width=True):
        with st.spinner("Predicting…"):
            r = requests.post(f"{API_BASE}/forecast/run", timeout=120)
        if r.ok:
            d = r.json()
            st.success(f"{d['windows_predicted']} windows predicted · {d['alerts_generated']} alerts generated")
            st.rerun()
        else:
            st.error(f"Forecast failed: {r.text}")

    forecast = fetch_forecast()
    if not forecast.empty:
        st.divider()

        peak = int(forecast["predicted_load"].max())
        total = int(forecast["predicted_load"].sum())
        windows = len(forecast)
        st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-box"><div class="kpi-val">{windows}</div><div class="kpi-lbl">Time windows</div></div>
  <div class="kpi-box"><div class="kpi-val">{peak}</div><div class="kpi-lbl">Peak pax / window</div></div>
  <div class="kpi-box"><div class="kpi-val">{total:,}</div><div class="kpi-lbl">Total pax today</div></div>
</div>""", unsafe_allow_html=True)

        # ── Cost Savings ──────────────────────────────────────────────
        DESK_HOURLY_RATE = 18  # €/hr per desk (fully-loaded cost estimate)
        WINDOW_HRS = 0.5

        thresholds_cfg = fetch_json(f"{API_BASE}/thresholds")
        checkin_cfg = thresholds_cfg.get("checkin", {}) if thresholds_cfg else {}
        lvl1 = checkin_cfg.get("level_1", {}).get("threshold", 75)
        lvl2 = checkin_cfg.get("level_2", {}).get("threshold", 125)
        lvl3 = checkin_cfg.get("level_3", {}).get("threshold", 200)
        d1   = checkin_cfg.get("level_1", {}).get("desks_to_open", 2)
        d2   = checkin_cfg.get("level_2", {}).get("desks_to_open", 3)
        d3   = checkin_cfg.get("level_3", {}).get("desks_to_open", 4)
        base_desks = checkin_cfg.get("baseline_desks", 1)

        def _desks_for_load(load):
            if load >= lvl3: return d3
            if load >= lvl2: return d2
            if load >= lvl1: return d1
            return base_desks

        recommended_desk_hours = sum(_desks_for_load(r) * WINDOW_HRS for r in forecast["predicted_load"])
        flat_desk_hours = d3 * len(forecast) * WINDOW_HRS
        saved_desk_hours = max(0, flat_desk_hours - recommended_desk_hours)
        daily_saving = saved_desk_hours * DESK_HOURLY_RATE
        annual_saving = daily_saving * 365

        rdh = f"{recommended_desk_hours:.0f}"
        fdh = f"{flat_desk_hours:.0f}"
        ds  = f"{daily_saving:,.0f}"
        ans = f"{annual_saving:,.0f}"
        st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-box"><div class="kpi-val">{rdh} h</div><div class="kpi-lbl">AI-recommended desk-hours today</div></div>
  <div class="kpi-box"><div class="kpi-val">{fdh} h</div><div class="kpi-lbl">Flat staffing desk-hours today</div></div>
  <div class="kpi-box" style="border:1px solid #2a5a2a"><div class="kpi-val" style="color:#52c07a">€{ds}</div><div class="kpi-lbl">Estimated daily savings</div></div>
  <div class="kpi-box" style="border:1px solid #2a5a2a"><div class="kpi-val" style="color:#52c07a">€{ans}</div><div class="kpi-lbl">Projected annual savings</div></div>
</div>""", unsafe_allow_html=True)

        # load thresholds for reference lines
        thresholds = fetch_json(f"{API_BASE}/thresholds")
        checkin = thresholds.get("checkin", {}) if thresholds else {}

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=forecast["window_start"],
            y=forecast["predicted_load"],
            marker=dict(
                color=forecast["predicted_load"],
                colorscale=[[0, "#3a7bd5"], [0.5, "#f0a500"], [1, "#e05252"]],
                showscale=False,
            ),
            hovertemplate="<b>%{x|%H:%M}</b><br>%{y} pax<extra></extra>",
        ))

        colors = {"level_1": "#f0c040", "level_2": "#f08040", "level_3": "#e05252"}
        for key, color in colors.items():
            lvl = checkin.get(key)
            if lvl:
                fig.add_hline(
                    y=lvl["threshold"],
                    line_dash="dot",
                    line_color=color,
                    line_width=1.5,
                    annotation_text=f"L{key[-1]}: {lvl['threshold']} pax",
                    annotation_position="right",
                    annotation_font_color=color,
                    annotation_font_size=11,
                )

        fig.update_layout(
            title="Predicted Passenger Load — 30-min Windows",
            plot_bgcolor="#0f1117",
            paper_bgcolor="#0f1117",
            font_color="#e0e0e0",
            xaxis=dict(gridcolor="#2a2d3a", title=""),
            yaxis=dict(gridcolor="#2a2d3a", title="Passengers"),
            margin=dict(l=10, r=80, t=40, b=10),
            height=340,
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Raw data table", expanded=False):
            st.dataframe(
                forecast.rename(columns={"window_start": "Window", "predicted_load": "Predicted Pax"}),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("No forecast yet — upload a schedule and click Run Forecast.")


# ── Alerts ─────────────────────────────────────────────────────────────────────

elif page == "Alerts":
    st.markdown("## Check-in Desk Alerts")

    desk_resp = fetch_json(f"{API_BASE}/alerts/desks")
    current_desks = desk_resp["desks_open"] if desk_resp else 0

    dc1, dc2, dc3 = st.columns([2, 1, 3])
    with dc1:
        new_desk_count = st.number_input(
            "Desks currently open",
            min_value=0, max_value=50,
            value=current_desks,
        )
    with dc2:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        if st.button("Update", use_container_width=True):
            requests.post(f"{API_BASE}/alerts/desks", json={"desks_open": new_desk_count})
            st.rerun()
    with dc3:
        st.markdown(f"<div style='margin-top:32px; color:#888; font-size:0.85rem'>Currently tracking <b style='color:#e0e0e0'>{current_desks}</b> open desk(s)</div>", unsafe_allow_html=True)

    st.divider()

    emp_name = st.text_input("Your name (audit trail)", value=st.session_state.get("employee_name", ""), placeholder="Enter your name…")
    if emp_name:
        st.session_state["employee_name"] = emp_name

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)
    tab_open, tab_ack, tab_all = st.tabs(["Open", "Acknowledged", "All"])

    def render_alerts(df: pd.DataFrame, show_ack: bool = False):
        if df.empty:
            st.markdown("<div style='color:#666; padding:20px 0'>No alerts in this category.</div>", unsafe_allow_html=True)
            return
        for _, row in df.iterrows():
            alert_type  = row.get("type", "")
            status      = row.get("status", "OPEN")
            desks_open  = (row.get("desks_to_open") or 0) - (row.get("desks_to_add") or 0)
            desks_need  = row.get("desks_to_open") or 0
            desks_add   = row.get("desks_to_add") or 0
            desks_close = row.get("desks_to_close") or 0
            load        = row.get("predicted_load", "?")
            win         = str(row.get("window_start", ""))[:16]

            if status == "ACKNOWLEDGED":
                card_cls, tag_cls, tag_txt = "alert-ack", "desk-ok", "✓ Acknowledged"
            elif alert_type == "checkin_close":
                card_cls = "alert-close"
                tag_cls  = "desk-close"
                tag_txt  = f"Close {desks_close} desk(s)"
            else:
                card_cls = "alert-open"
                tag_cls  = "desk-open"
                tag_txt  = f"Open {desks_add} more desk(s)"

            desk_detail = f"{desks_open} open → need {desks_need}" if alert_type != "checkin_close" else f"{desks_open} open → reduce to {desks_need}"

            col_card, col_btn = st.columns([5, 1])
            with col_card:
                st.markdown(f"""
<div class="alert-card {card_cls}">
  <div class="alert-title">{row['message']}</div>
  <span class="desk-tag {tag_cls}">{tag_txt}</span>
  <div class="alert-sub">Window: {win} &nbsp;·&nbsp; {load} pax &nbsp;·&nbsp; {desk_detail}</div>
</div>""", unsafe_allow_html=True)
            with col_btn:
                if show_ack and status == "OPEN":
                    st.markdown("<div style='margin-top:18px'></div>", unsafe_allow_html=True)
                    emp = st.session_state.get("employee_name", "employee") or "employee"
                    if st.button("Confirm", key=f"ack_{row['id']}"):
                        requests.post(f"{API_BASE}/alerts/{row['id']}/acknowledge", json={"employee": emp})
                        st.session_state.pop("desk_count_cache", None)
                        st.session_state["current_page"] = "Alerts"
                        st.rerun()

    with tab_open:
        render_alerts(fetch_alerts("OPEN"), show_ack=True)
    with tab_ack:
        render_alerts(fetch_alerts("ACKNOWLEDGED"))
    with tab_all:
        render_alerts(fetch_alerts())


# ── Simulation ─────────────────────────────────────────────────────────────────

elif page == "Simulation":
    st.markdown("## Check-in Flow Simulation")
    st.caption("Select a forecast time window to simulate exactly that window's passenger load and recommended desk count.")

    _SIM_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Terminal Simulation</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',Arial,sans-serif;background:#0a0d14;color:#c8d0e0;padding:10px;overflow-x:hidden}
.wrap{display:flex;gap:12px;align-items:flex-start}
.sim-panel{flex:1;min-width:0;background:#111825;border-radius:10px;padding:12px;border:1px solid #1e2840}
canvas#c{display:block;border-radius:6px;border:1px solid #1e2840;width:100%}
.btns{display:flex;justify-content:center;gap:8px;margin:10px 0 8px}
.btn{padding:7px 18px;font-size:12px;border:none;border-radius:5px;cursor:pointer;font-weight:700;letter-spacing:.04em;transition:all .15s}
.btn:active{transform:scale(.96)}
.btn-s{background:#163324;color:#5ddd8a;border:1px solid #2a5a3a}.btn-s:hover{background:#1e4430}
.btn-s:disabled{background:#111e18;color:#3a5545;border-color:#1a2e22;cursor:not-allowed}
.btn-p{background:#33220a;color:#f0b84a;border:1px solid #5a3a14}.btn-p:hover{background:#42300f}
.btn-p:disabled{background:#1e180a;color:#5a4520;border-color:#2a2010;cursor:not-allowed}
.btn-r{background:#141c2e;color:#7a9acc;border:1px solid #1e3050}.btn-r:hover{background:#1a2438}
.stats-bar{display:grid;grid-template-columns:repeat(6,1fr);gap:5px;padding:8px;background:#0d1118;border-radius:6px}
.sbox{text-align:center;padding:6px 3px;background:#111825;border-radius:5px;border:1px solid #1a2338}
.slbl{color:#445566;font-size:9px;text-transform:uppercase;letter-spacing:.06em;margin-bottom:3px}
.sval{font-size:16px;font-weight:700}
.c-b{color:#5599ff}.c-y{color:#f0c040}.c-g{color:#44cc88}.c-r{color:#ee5544}.c-w{color:#d0dae8}.c-o{color:#ff9944}
.progress-wrap{height:6px;background:#0d1118;border-radius:3px;margin-top:6px;overflow:hidden}
.progress-bar{height:100%;background:linear-gradient(90deg,#3a7bd5,#44cc88);border-radius:3px;transition:width .3s}
.prog-lbl{font-size:9px;color:#445566;text-align:center;margin-top:2px}
.right{width:268px;flex-shrink:0;background:#111825;border-radius:10px;padding:12px;border:1px solid #1e2840;display:flex;flex-direction:column;gap:9px;max-height:820px;overflow-y:auto}
.sec-title{font-size:10px;font-weight:700;color:#445566;text-transform:uppercase;letter-spacing:.08em;margin-bottom:2px}
.api-row{display:flex;gap:5px}
.abtn{flex:1;padding:6px;font-size:11px;border:none;border-radius:5px;cursor:pointer;font-weight:700;transition:all .15s}
.abtn:active{transform:scale(.97)}
.abtn-g{background:#132a1c;color:#66ee99;border:1px solid #255a30}.abtn-g:hover{background:#1a3a25}
.abtn-b{background:#112235;color:#66aaee;border:1px solid #1e4060}.abtn-b:hover{background:#172d45}
.abtn:disabled{opacity:.4;cursor:not-allowed}
.smsg{padding:5px 7px;border-radius:4px;font-size:10px;text-align:center;display:none}
.smsg.ok{background:#0d2216;color:#44dd77;border:1px solid #1a4a2a;display:block}
.smsg.err{background:#220d0d;color:#ff7070;border:1px solid #4a1a1a;display:block}
.timeline-scroll{overflow-x:auto;padding-bottom:4px}
.timeline-scroll::-webkit-scrollbar{height:4px}
.timeline-scroll::-webkit-scrollbar-track{background:#0d1118}
.timeline-scroll::-webkit-scrollbar-thumb{background:#2a3a50;border-radius:2px}
.timeline-row{display:flex;gap:3px;min-width:max-content;padding:2px 0}
.tblock{width:30px;flex-shrink:0;cursor:pointer;border-radius:3px;border:1px solid transparent;transition:all .15s;position:relative;overflow:visible}
.tblock:hover .tblock-bar{opacity:.85}
.tblock-bar{height:30px;border-radius:2px;transition:opacity .15s}
.tblock-lbl{font-size:7px;color:#445566;text-align:center;margin-top:2px;white-space:nowrap}
.tblock.selected{border-color:#5599ff !important}
.tblock.selected .tblock-lbl{color:#5599ff}
.alert-dot{position:absolute;top:-4px;right:2px;width:6px;height:6px;border-radius:50%;border:1px solid #0a0d14}
.win-card{background:#0d1118;border-radius:6px;padding:9px;border:1px solid #1a2840}
.win-card-time{font-size:18px;font-weight:700;color:#e0eeff;margin-bottom:4px}
.win-card-row{display:flex;justify-content:space-between;font-size:11px;padding:2px 0;border-bottom:1px solid #161e2c}
.win-card-row:last-child{border:none}
.win-card-lbl{color:#445566}
.win-card-val{font-weight:600;color:#c8d0e0}
.win-card-val.alert-open{color:#ee7766}
.win-card-val.alert-close{color:#66dd88}
.alert-msg{font-size:10px;margin-top:5px;padding:5px 7px;border-radius:4px;line-height:1.4}
.alert-msg.open{background:#2a100a;border-left:3px solid #cc4422;color:#ffaa88}
.alert-msg.close{background:#0a2010;border-left:3px solid #228844;color:#88ffaa}
.load-btn{width:100%;padding:8px;font-size:12px;border:none;border-radius:5px;cursor:pointer;font-weight:700;background:#1a3060;color:#88bbff;border:1px solid #2a4880;margin-top:6px;transition:all .15s}
.load-btn:hover{background:#203878}
.load-btn:disabled{opacity:.4;cursor:not-allowed}
.no-fc{font-size:11px;color:#334455;text-align:center;padding:16px 0}
.speed-box{background:#0d1118;padding:9px;border-radius:5px}
.speed-row{display:flex;flex-direction:column;gap:3px}
.speed-row label{font-size:10px;color:#445566;font-weight:700;display:flex;justify-content:space-between;margin-bottom:2px}
.speed-row label span{color:#f0c040;font-weight:700;font-size:12px}
.speed-row input[type=range]{width:100%;accent-color:#f0c040;cursor:pointer}
.speed-hint{font-size:9px;color:#33445566;margin-top:2px}
.day-btn{width:100%;padding:8px;font-size:12px;border:none;border-radius:5px;cursor:pointer;font-weight:700;background:#2a1060;color:#cc88ff;border:1px solid #4a20a0;transition:all .15s;margin-top:4px}
.day-btn:hover{background:#3a1878}
.day-btn:disabled{opacity:.4;cursor:not-allowed}
.day-prog{font-size:10px;color:#8866cc;text-align:center;margin-top:3px;display:none}
.legend{display:flex;flex-wrap:wrap;gap:4px 8px}
.leg{display:flex;align-items:center;gap:3px;font-size:9px;color:#556677}
.ldot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.lsq{width:8px;height:7px;border-radius:1px;flex-shrink:0}
</style>
</head>
<body>
<div class="wrap">
  <!-- LEFT: simulation canvas -->
  <div class="sim-panel">
    <canvas id="c" width="800" height="490"></canvas>
    <div class="btns">
      <button class="btn btn-s" id="btnStart">&#9654; Start</button>
      <button class="btn btn-p" id="btnPause" disabled>&#9646;&#9646; Pause</button>
      <button class="btn btn-r" id="btnReset">&#8635; Reset</button>
    </div>
    <div class="stats-bar">
      <div class="sbox"><div class="slbl">In System</div><div class="sval c-b" id="ss">0</div></div>
      <div class="sbox"><div class="slbl">In Queue</div><div class="sval c-y" id="sq">0</div></div>
      <div class="sbox"><div class="slbl">Processed</div><div class="sval c-g" id="sp">0</div></div>
      <div class="sbox"><div class="slbl">Turned Away</div><div class="sval c-r" id="sb">0</div></div>
      <div class="sbox"><div class="slbl">Open Desks</div><div class="sval c-w" id="sd">--</div></div>
      <div class="sbox"><div class="slbl">Avg Wait</div><div class="sval c-o" id="sw">--</div></div>
    </div>
    <div class="progress-wrap"><div class="progress-bar" id="progBar" style="width:0%"></div></div>
    <div class="prog-lbl" id="progLbl"></div>
  </div>

  <!-- RIGHT: controls -->
  <div class="right">

    <!-- Forecast loading -->
    <div>
      <div class="sec-title">Forecast Data</div>
      <div class="api-row" style="margin-top:4px">
        <button class="abtn abtn-g" id="btnTrain">Train</button>
        <button class="abtn abtn-b" id="btnForecast">Load Forecast</button>
      </div>
      <div id="smsg" class="smsg" style="margin-top:5px"></div>
    </div>

    <!-- Speed -->
    <div>
      <div class="sec-title" style="margin-bottom:5px">Simulation Speed</div>
      <div class="speed-box">
        <div class="speed-row">
          <label>Time speed <span id="lblSpeed">5x</span></label>
          <input type="range" id="slSpeed" min="1" max="30" step="1" value="5">
        </div>
        <div class="speed-hint">1x = real-ish &nbsp;·&nbsp; 10x = fast &nbsp;·&nbsp; 30x = turbo</div>
      </div>
    </div>

    <!-- Full day -->
    <div>
      <div class="sec-title" style="margin-bottom:5px">Full Day</div>
      <button class="day-btn" id="btnDay">&#9654;&#9654; Simulate Entire Day</button>
      <div class="day-prog" id="dayProg"></div>
    </div>

    <!-- Timeline -->
    <div>
      <div class="sec-title">Select Time Window</div>
      <div class="timeline-scroll" style="margin-top:5px">
        <div class="timeline-row" id="timeline">
          <div class="no-fc">Load forecast to see timeline</div>
        </div>
      </div>
    </div>

    <!-- Selected window card -->
    <div id="winCard" style="display:none">
      <div class="win-card">
        <div class="win-card-time" id="wcTime">--:--</div>
        <div class="win-card-row"><span class="win-card-lbl">Predicted pax</span><span class="win-card-val" id="wcPax">--</span></div>
        <div class="win-card-row"><span class="win-card-lbl">Desks to open</span><span class="win-card-val" id="wcDesks">--</span></div>
        <div class="win-card-row"><span class="win-card-lbl">Window status</span><span class="win-card-val" id="wcStatus">--</span></div>
        <div id="wcAlert" class="alert-msg" style="display:none"></div>
        <button class="load-btn" id="btnLoad">Simulate this window</button>
      </div>
    </div>


    <!-- Legend -->
    <div>
      <div class="sec-title" style="margin-bottom:4px">Legend</div>
      <div class="legend">
        <div class="leg"><div class="ldot" style="background:#5599ff"></div>Solo</div>
        <div class="leg"><div class="ldot" style="background:#ff8844"></div>Family</div>
        <div class="leg"><div class="ldot" style="background:#88ffcc"></div>Business</div>
        <div class="leg"><div class="ldot" style="background:#44cc88"></div>At desk</div>
        <div class="leg"><div class="ldot" style="background:#ff5544"></div>Turned away</div>
        <div class="leg"><div class="lsq" style="background:#1d6640"></div>Desk open</div>
        <div class="leg"><div class="lsq" style="background:#662020"></div>Desk closed</div>
        <div class="leg"><div class="lsq" style="background:#c07010"></div>Desk busy</div>
      </div>
    </div>

  </div>
</div>

<script>
const API='http://localhost:8000';
const W=800,H=490,N=20,FPS=60,QGAP=15,SPD=2.8,BALK=14;

// sim state
let ciTime=90, spawnRate=30, running=false, frame=0;
let processed=0, balked=0, totalWait=0, ciCount=0, openCount=10;
const pax=[], desks=[];

// window mode state
let fData=[];       // forecast predictions
let aData=[];       // alerts
let selIdx=-1;      // selected window index
let winRemain=0;    // pax still to spawn
let winTotal=0;     // total pax for selected window
let winLabel='';    // HH:MM label
let winDone=false;  // window fully spawned

// pulse for entrance animation
let pulse=0;

// speed & full-day
let simSpeed=5;
let fullDay=false;
let dayIdx=0;

const TYPES=[
  {name:'solo', r:4,  mult:1.0, col:'#5599ff', w:.60},
  {name:'fam',  r:6,  mult:1.9, col:'#ff8844', w:.25},
  {name:'biz',  r:4,  mult:.55, col:'#88ffcc', w:.15},
];
function pickType(){let c=0,rnd=Math.random();for(const t of TYPES){c+=t.w;if(rnd<c)return t;}return TYPES[0];}

// ── Desk ──────────────────────────────────────────────────────────────────────
class Desk{
  constructor(i,x,y,open){this.i=i;this.x=x;this.y=y;this.w=32;this.h=18;this.open=open;this.q=[];this.served=0;}
  get sc(){
    if(!this.open)return'#662020';
    const n=this.q.length;
    if(n===0)return'#1d6640';
    if(n<=3)return'#2a9455';
    if(n<=6)return'#c07010';
    return'#c03020';
  }
  draw(cx){
    const{x,y,w,h,sc,open,q,served,i}=this;
    const lx=x-w/2,ty=y-h/2;
    // Queue bar behind desk
    if(open&&q.length>0){
      const f=Math.min(q.length/BALK,1),bh=f*52;
      const g=cx.createLinearGradient(lx,ty-bh-16,lx,ty-16);
      g.addColorStop(0,sc+'00');g.addColorStop(1,sc+'55');
      cx.fillStyle=g;cx.fillRect(lx+2,ty-bh-16,w-4,bh);
      cx.strokeStyle=sc+'44';cx.lineWidth=.8;cx.strokeRect(lx+2,ty-bh-16,w-4,bh);
    }
    // Shadow
    cx.fillStyle='#05080e';cx.fillRect(lx+2,ty+h+1,w,3);
    // Front face
    cx.fillStyle='#121a2c';cx.fillRect(lx,ty+h*.7,w,h*.3+2);
    // Top face
    const dg=cx.createLinearGradient(lx,ty,lx,ty+h*.72);
    dg.addColorStop(0,'#1c2540');dg.addColorStop(1,'#141d36');
    cx.fillStyle=dg;cx.fillRect(lx,ty,w,h*.72);
    // Status stripe
    cx.fillStyle=sc;cx.fillRect(lx,ty,w,3);
    // Glint
    cx.fillStyle='#ffffff07';cx.fillRect(lx+2,ty+4,w-4,4);
    // Status light
    cx.save();cx.shadowColor=sc;cx.shadowBlur=open?9:3;
    cx.fillStyle=sc;cx.beginPath();cx.arc(x,ty-9,3.5,0,Math.PI*2);cx.fill();
    cx.restore();
    // Number
    cx.fillStyle='#5577aa';cx.font='bold 7px Segoe UI,Arial';cx.textAlign='center';
    cx.fillText(i+1,x,ty+h*.5+2.5);
    if(served>0){cx.fillStyle='#33446688';cx.font='6px Arial';cx.fillText(served,x,ty-19);}
    if(!open){cx.fillStyle='#ee444466';cx.font='bold 6px Arial';cx.fillText('CLOSED',x,ty+h*.5+10);}
  }
}

// ── Passenger ─────────────────────────────────────────────────────────────────
class Pax{
  constructor(sx,sy){
    this.type=pickType();
    this.x=sx+(Math.random()-.5)*40;this.y=sy;
    this.desk=null;this.state='WALK';
    this.timer=0;this.wpts=[];this.wf=0;
    this.qox=(Math.random()-.5)*6;this.alpha=1;this.trail=[];
  }
  get myCI(){return Math.max(1,Math.round(ciTime*this.type.mult/simSpeed));}
  assign(ds){
    const op=ds.filter(d=>d.open);
    if(!op.length){this.state='BALK';balked++;return;}
    const best=op.reduce((m,d)=>d.q.length<m.q.length?d:m);
    if(best.q.length>=BALK){this.state='BALK';balked++;return;}
    this.desk=best;best.q.push(this);
  }
  update(){
    this.trail.push({x:this.x,y:this.y});
    if(this.trail.length>5)this.trail.shift();
    if(this.state==='BALK'){
      this.x+=(Math.random()-.5)*1.2;this.y+=SPD*.6;
      this.alpha=Math.max(0,this.alpha-.022);return;
    }
    if(this.state==='WALK'){
      const qi=this.desk.q.indexOf(this);if(qi===-1)return;
      const tx=this.desk.x+this.qox,ty=this.desk.y+26+qi*QGAP;
      this._mv(tx,ty);this.wf++;
      if(qi===0&&Math.hypot(tx-this.x,ty-this.y)<SPD){this.x=tx;this.y=ty;this.state='CI';}
    }else if(this.state==='CI'){
      this.timer++;this.wf++;
      if(this.timer>=this.myCI){
        this.desk.q.shift();this.desk.served++;
        totalWait+=this.wf;ciCount++;
        this.state='OUT';
        this.wpts=[[this.desk.x+30,this.desk.y-4],[this.desk.x+30,86]];
      }
    }else if(this.state==='OUT'){
      if(this.wpts.length){const[tx,ty]=this.wpts[0];if(this._mv(tx,ty))this.wpts.shift();}
      else this.state='EXIT';
    }else if(this.state==='EXIT'){
      this.y-=SPD*1.3;
    }
  }
  _mv(tx,ty){
    const dx=tx-this.x,dy=ty-this.y,d=Math.hypot(dx,dy);
    if(d>SPD){this.x+=dx/d*SPD;this.y+=dy/d*SPD;return false;}
    this.x=tx;this.y=ty;return true;
  }
  draw(cx){
    cx.globalAlpha=this.alpha;
    const col={WALK:this.type.col,CI:'#44cc88',OUT:'#ffcc44',EXIT:'#99aabb',BALK:'#ff5544'}[this.state]||this.type.col;
    for(let i=1;i<this.trail.length;i++){
      const a=i/this.trail.length*.2;
      cx.strokeStyle=col;cx.globalAlpha=this.alpha*a;
      cx.lineWidth=this.type.r*.9;cx.lineCap='round';
      cx.beginPath();cx.moveTo(this.trail[i-1].x,this.trail[i-1].y);
      cx.lineTo(this.trail[i].x,this.trail[i].y);cx.stroke();
    }
    cx.globalAlpha=this.alpha;
    if(this.state==='CI'){cx.shadowColor=col;cx.shadowBlur=14;}
    cx.fillStyle=col;
    cx.beginPath();cx.arc(this.x,this.y,this.type.r,0,Math.PI*2);cx.fill();
    if(this.type.name==='fam'){cx.fillStyle='#ffffff25';cx.beginPath();cx.arc(this.x,this.y,this.type.r*.4,0,Math.PI*2);cx.fill();}
    cx.shadowBlur=0;cx.globalAlpha=1;
  }
}

// ── Canvas & desks ────────────────────────────────────────────────────────────
const canvas=document.getElementById('c');
const cx=canvas.getContext('2d');

function initDesks(n){
  desks.length=0;
  const sx=38,sp=Math.floor((W-76)/(N-1));
  for(let i=0;i<N;i++)desks.push(new Desk(i,sx+i*sp,H/2,i<n));
  openCount=n;
  document.getElementById('sd').textContent=n;
}

function setOpenDesks(n){
  openCount=n;
  for(let i=0;i<desks.length;i++){
    const was=desks[i].open;
    desks[i].open=i<n;
    if(was&&!desks[i].open){
      for(const p of desks[i].q){p.state='WALK';p.assign(desks);}
      desks[i].q=[];
    }
  }
  document.getElementById('sd').textContent=n;
}

// ── Forecast helpers ──────────────────────────────────────────────────────────
function desksAtWindow(idx){
  if(!fData.length)return 1;
  const winTime=fData[idx].window_start;
  // replay alert history — only alerts that set a total desk count
  const relevant=aData
    .filter(a=>a.window_start<=winTime && a.desks_to_open!=null)
    .sort((a,b)=>a.window_start.localeCompare(b.window_start));
  if(relevant.length)return relevant[relevant.length-1].desks_to_open;
  // fallback: derive from load thresholds when no alert data available
  const load=fData[idx].predicted_load||0;
  if(load>=200)return 4;
  if(load>=125)return 3;
  if(load>=75)return 2;
  return 1;
}

function alertAtWindow(idx){
  if(!fData.length)return null;
  const winTime=fData[idx].window_start;
  return aData.find(a=>a.window_start===winTime)||null;
}

function loadColor(pax){
  if(pax<=0)return'#1a2030';
  if(pax<50)return'rgba(50,100,190,0.8)';
  if(pax<100)return'rgba(60,140,100,0.85)';
  if(pax<150)return'rgba(200,150,30,0.85)';
  return'rgba(200,70,50,0.85)';
}

// ── Timeline ──────────────────────────────────────────────────────────────────
function buildTimeline(){
  const row=document.getElementById('timeline');
  if(!fData.length){row.innerHTML='<div class="no-fc">Load forecast to see timeline</div>';return;}
  row.innerHTML='';
  const maxLoad=Math.max(...fData.map(w=>w.predicted_load||0),1);
  fData.forEach((w,i)=>{
    const load=w.predicted_load||0;
    const timeStr=(w.window_start||'').split(' ')[1]?.slice(0,5)||'';
    const alert=alertAtWindow(i);
    const fillH=Math.max(4,Math.round((load/maxLoad)*28));
    const col=loadColor(load);

    const block=document.createElement('div');
    block.className='tblock'+(i===selIdx?' selected':'');
    block.title=timeStr+' — '+load+' pax'+(alert?' — '+alert.message:'');
    block.dataset.idx=i;

    const bar=document.createElement('div');
    bar.className='tblock-bar';
    bar.style.cssText='height:30px;background:#1a2030;border-radius:2px;display:flex;align-items:flex-end;overflow:hidden';
    const fill=document.createElement('div');
    fill.style.cssText='width:100%;height:'+fillH+'px;background:'+col+';border-radius:1px';
    bar.appendChild(fill);

    const lbl=document.createElement('div');
    lbl.className='tblock-lbl';
    lbl.textContent=timeStr;

    if(alert){
      const dot=document.createElement('div');
      dot.className='alert-dot';
      dot.style.background=alert.type==='checkin_open'?'#ff6644':'#44dd88';
      block.appendChild(dot);
    }

    block.appendChild(bar);
    block.appendChild(lbl);
    block.addEventListener('click',()=>selectWindow(i));
    row.appendChild(block);
  });
}

function selectWindow(idx){
  selIdx=idx;
  buildTimeline();  // re-render with new selected
  showWindowCard(idx);
  // scroll selected into view
  const blocks=document.querySelectorAll('.tblock');
  if(blocks[idx])blocks[idx].scrollIntoView({behavior:'smooth',block:'nearest',inline:'center'});
}

function showWindowCard(idx){
  const w=fData[idx];
  const load=w.predicted_load||0;
  const desks=desksAtWindow(idx);
  const alert=alertAtWindow(idx);
  const timeStr=(w.window_start||'').split(' ')[1]?.slice(0,5)||'--:--';

  document.getElementById('wcTime').textContent=timeStr;
  document.getElementById('wcPax').textContent=load+' pax';

  const dEl=document.getElementById('wcDesks');
  dEl.textContent=desks+' desk'+(desks!==1?'s':'');
  dEl.className='win-card-val';

  const sEl=document.getElementById('wcStatus');
  if(alert){
    sEl.textContent=alert.status;
    sEl.className='win-card-val '+(alert.type==='checkin_open'?'alert-open':'alert-close');
    const aEl=document.getElementById('wcAlert');
    aEl.textContent=alert.message;
    aEl.className='alert-msg '+(alert.type==='checkin_open'?'open':'close');
    aEl.style.display='block';
  } else {
    sEl.textContent='No alert';sEl.className='win-card-val';
    document.getElementById('wcAlert').style.display='none';
  }

  document.getElementById('winCard').style.display='block';
}

// ── Load window into simulation ───────────────────────────────────────────────
function loadWindowSim(idx){
  const w=fData[idx];
  const load=w.predicted_load||0;
  const desksN=desksAtWindow(idx);
  const timeStr=(w.window_start||'').split(' ')[1]?.slice(0,5)||'';

  if(load===0){msg('No passengers expected in this window',false);return;}

  // Reset sim state
  running=false;frame=0;processed=0;balked=0;totalWait=0;ciCount=0;
  pax.length=0;

  // Apply forecast data
  setOpenDesks(desksN);

  // ciTime: scaled so desks run at ~80% utilisation regardless of load/speed
  ciTime=Math.max(20,Math.round(desksN*FPS*90/Math.max(load,1)/1.25));

  // Compress 30 min into ~90 seconds at 1x, divided by simSpeed
  spawnRate=Math.max(1,Math.round(FPS*90/load/simSpeed));

  winRemain=load;winTotal=load;winLabel=timeStr;winDone=false;

  document.getElementById('btnStart').disabled=false;
  document.getElementById('btnPause').disabled=true;
  updateProgress();
  msg('Window '+timeStr+' loaded — press Start',true);
}

function loadWindowForDay(idx){
  const w=fData[idx];
  const load=w.predicted_load||0;
  const desksN=desksAtWindow(idx);
  const timeStr=(w.window_start||'').split(' ')[1]?.slice(0,5)||'';
  setOpenDesks(desksN);
  frame=0;pax.length=0;winDone=false;
  if(load>0){
    ciTime=Math.max(20,Math.round(desksN*FPS*90/Math.max(load,1)/1.25));
    spawnRate=Math.max(1,Math.round(FPS*90/load/simSpeed));
    winTotal=load;winRemain=load;
  } else {
    winTotal=0;winRemain=0;  // empty window — skip instantly
  }
  winLabel=timeStr;selIdx=idx;
  buildTimeline();
  showWindowCard(idx);
  // scroll timeline to current block
  const blocks=document.querySelectorAll('.tblock');
  if(blocks[idx])blocks[idx].scrollIntoView({behavior:'smooth',block:'nearest',inline:'center'});
  // update day progress label
  const dp=document.getElementById('dayProg');
  dp.style.display='block';
  dp.textContent='Window '+(idx+1)+' / '+fData.length+' — '+timeStr;
}

function startFullDay(){
  if(!fData.length){msg('Load forecast first',false);return;}
  fullDay=true;dayIdx=0;
  processed=0;balked=0;totalWait=0;ciCount=0;
  winDone=false;
  running=true;
  document.getElementById('btnStart').disabled=true;
  document.getElementById('btnPause').disabled=false;
  document.getElementById('btnDay').disabled=true;
  loadWindowForDay(0);
  msg('Simulating full day at '+simSpeed+'x…',true);
}

function updateProgress(){
  const spawned=winTotal-winRemain;
  const pct=winTotal>0?Math.round(spawned/winTotal*100):0;
  document.getElementById('progBar').style.width=pct+'%';
  if(winTotal>0){
    document.getElementById('progLbl').textContent=
      winLabel ? winLabel+' — '+spawned+' / '+winTotal+' pax spawned ('+pct+'%)' : '';
  } else {
    document.getElementById('progLbl').textContent='';
  }
}

// ── Simulation loop ───────────────────────────────────────────────────────────
function tick(){
  if(!running)return;
  frame++;

  // Spawn passengers
  if(frame%Math.max(2,spawnRate)===0){
    if(winTotal>0){
      // window mode: spawn exactly winTotal passengers
      if(winRemain>0){
        const p=new Pax(W/2,H-20);p.assign(desks);pax.push(p);
        winRemain--;
        updateProgress();
      }
    } else {
      // free-run mode
      const p=new Pax(W/2,H-20);p.assign(desks);pax.push(p);
    }
  }

  // Mark window done when all spawned AND system empty (or window was empty)
  if(!winDone){
    const isEmpty=winTotal===0;
    const allClear=winTotal>0&&winRemain===0&&pax.length===0&&frame>30;
    if(isEmpty||allClear) winDone=true;
  }

  // Advance full-day or stop single-window
  if(winDone){
    if(fullDay){
      if(dayIdx<fData.length-1){
        dayIdx++;
        loadWindowForDay(dayIdx);
      } else {
        // Day finished
        fullDay=false;running=false;
        document.getElementById('btnStart').disabled=false;
        document.getElementById('btnPause').disabled=true;
        document.getElementById('btnDay').disabled=false;
        document.getElementById('dayProg').textContent='Day complete — '+processed+' processed, '+balked+' turned away';
        msg('Full day complete — '+processed+' processed, '+balked+' turned away',true);
      }
    } else if(winTotal>0&&running){
      // Single window mode — stop once
      running=false;
      document.getElementById('btnStart').disabled=false;
      document.getElementById('btnPause').disabled=true;
      msg('Window complete — '+processed+' processed, '+balked+' turned away',true);
    }
  }

  for(let i=pax.length-1;i>=0;i--){
    pax[i].update();
    if(pax[i].y<0||(pax[i].state==='BALK'&&pax[i].alpha<=0)){
      if(pax[i].state==='EXIT'||pax[i].state==='OUT')processed++;
      pax.splice(i,1);
    }
  }
}

// ── Rendering ─────────────────────────────────────────────────────────────────
function drawBg(){
  cx.fillStyle='#0b0e16';cx.fillRect(0,0,W,H);
  cx.strokeStyle='#121828';cx.lineWidth=.5;
  for(let x=0;x<W;x+=36){cx.beginPath();cx.moveTo(x,80);cx.lineTo(x,H);cx.stroke();}
  for(let y=80;y<H;y+=36){cx.beginPath();cx.moveTo(0,y);cx.lineTo(W,y);cx.stroke();}
  const sg=cx.createLinearGradient(0,0,0,80);
  sg.addColorStop(0,'#070e1c');sg.addColorStop(1,'#0c172a');
  cx.fillStyle=sg;cx.fillRect(0,0,W,80);
  cx.save();cx.beginPath();cx.rect(0,0,W,80);cx.clip();
  cx.strokeStyle='#0a1425';cx.lineWidth=7;
  for(let x=-80;x<W+80;x+=20){cx.beginPath();cx.moveTo(x,0);cx.lineTo(x+80,80);cx.stroke();}
  cx.restore();
  cx.fillStyle='#274a68';cx.font='bold 11px Segoe UI,Arial';cx.textAlign='center';
  cx.fillText('SECURITY CHECKPOINT',W/2,26);
  cx.fillStyle='#1c3550';cx.font='9px Arial';
  cx.fillText('Proceed here after check-in',W/2,44);
  cx.fillStyle='#1a3a5566';cx.font='13px Arial';
  for(let x=W/2-120;x<=W/2+120;x+=40)cx.fillText('▲',x,65);
  cx.strokeStyle='#1a3a5044';cx.lineWidth=1.2;cx.setLineDash([9,7]);
  cx.beginPath();cx.moveTo(16,81);cx.lineTo(W-16,81);cx.stroke();
  cx.setLineDash([]);
  cx.fillStyle='#253a5566';cx.font='8px Arial';cx.textAlign='left';
  cx.fillText('CHECK-IN HALL',10,96);
  pulse=(pulse+.035)%(Math.PI*2);
  const pr=28+Math.sin(pulse)*4;
  const eg=cx.createRadialGradient(W/2,H-10,3,W/2,H-10,pr*2.4);
  eg.addColorStop(0,'#1a3350');eg.addColorStop(1,'#0b0e16');
  cx.fillStyle=eg;cx.beginPath();cx.ellipse(W/2,H-10,pr*2.8,20,0,0,Math.PI*2);cx.fill();
  cx.strokeStyle='#1a324e';cx.lineWidth=1.2;
  cx.beginPath();cx.moveTo(W/2-76,H);cx.lineTo(W/2-76,H-30);cx.stroke();
  cx.beginPath();cx.moveTo(W/2+76,H);cx.lineTo(W/2+76,H-30);cx.stroke();
  cx.fillStyle='#3d7799';cx.font='bold 9px Segoe UI,Arial';cx.textAlign='center';
  cx.fillText('TERMINAL ENTRANCE',W/2,H-3);
}

function drawOverlay(){
  if(!winLabel)return;
  const spawned=winTotal>0?winTotal-winRemain:0;
  let txt=winLabel+'  |  '+openCount+' desks  |  '+simSpeed+'x';
  if(winTotal>0)txt=winLabel+'  |  '+spawned+'/'+winTotal+' pax  |  '+openCount+' desks  |  '+simSpeed+'x';
  if(fullDay)txt='Day: '+(dayIdx+1)+'/'+fData.length+'  '+txt;
  cx.font='bold 11px Segoe UI,Arial';cx.textAlign='right';
  const tw=cx.measureText(txt).width+16;
  cx.fillStyle='#0d1420cc';
  cx.beginPath();cx.roundRect(W-tw-6,6,tw+6,22,4);cx.fill();
  cx.fillStyle=fullDay?'#cc88ff':'#88bbee';
  cx.fillText(txt,W-10,21);
}

function render(){
  drawBg();
  for(const d of desks)d.draw(cx);
  for(const p of pax)p.draw(cx);
  drawOverlay();
  const qc=desks.reduce((s,d)=>s+d.q.length,0);
  const live=pax.filter(p=>p.state!=='BALK').length;
  document.getElementById('ss').textContent=live;
  document.getElementById('sq').textContent=qc;
  document.getElementById('sp').textContent=processed;
  document.getElementById('sb').textContent=balked;
  if(ciCount>0){
    const avg=(totalWait/ciCount/FPS).toFixed(1);
    const el=document.getElementById('sw');
    el.textContent=avg+'s';
    el.className='sval '+(+avg<10?'c-g':+avg<25?'c-y':'c-r');
  }
}

function loop(){tick();render();requestAnimationFrame(loop);}

// ── Buttons ───────────────────────────────────────────────────────────────────
document.getElementById('btnStart').addEventListener('click',()=>{
  running=true;
  document.getElementById('btnStart').disabled=true;
  document.getElementById('btnPause').disabled=false;
});
document.getElementById('btnPause').addEventListener('click',()=>{
  running=false;
  document.getElementById('btnStart').disabled=false;
  document.getElementById('btnPause').disabled=true;
});
document.getElementById('btnReset').addEventListener('click',()=>{
  running=false;frame=0;processed=0;balked=0;totalWait=0;ciCount=0;
  winRemain=0;winTotal=0;winLabel='';winDone=false;fullDay=false;
  pax.length=0;initDesks(openCount);
  document.getElementById('btnStart').disabled=false;
  document.getElementById('btnPause').disabled=true;
  document.getElementById('btnDay').disabled=false;
  document.getElementById('progBar').style.width='0%';
  document.getElementById('progLbl').textContent='';
  document.getElementById('dayProg').style.display='none';
});
document.getElementById('btnLoad').addEventListener('click',()=>{
  if(selIdx>=0)loadWindowSim(selIdx);
});


// ── Speed & full-day ─────────────────────────────────────────────────────────
document.getElementById('slSpeed').addEventListener('input',function(){
  simSpeed=parseInt(this.value);
  document.getElementById('lblSpeed').textContent=simSpeed+'x';
  // If a window is loaded but not yet started, recalculate spawn rate
  if(winTotal>0&&winRemain===winTotal){
    spawnRate=Math.max(1,Math.round(FPS*90/winTotal/simSpeed));
  }
});
document.getElementById('btnDay').addEventListener('click',startFullDay);

// ── Status message ─────────────────────────────────────────────────────────────
function msg(txt,ok){
  const el=document.getElementById('smsg');
  el.textContent=txt;el.className='smsg '+(ok?'ok':'err');
  setTimeout(()=>el.className='smsg',5000);
}

// ── API ───────────────────────────────────────────────────────────────────────
async function loadForecast(){
  try{
    const [fr,ar]=await Promise.all([
      fetch(`${API}/forecast`),
      fetch(`${API}/alerts`)
    ]);
    if(!fr.ok)throw new Error('Forecast not available');
    fData=await fr.json();
    aData=ar.ok?await ar.json():[];
    if(!Array.isArray(fData)||fData.length===0)throw new Error('No forecast data');
    buildTimeline();
    msg('Loaded '+fData.length+' windows, '+aData.length+' alerts',true);
  }catch(e){
    msg(e.message,false);
    buildTimeline();
  }
}

document.getElementById('btnTrain').addEventListener('click',async()=>{
  const b=document.getElementById('btnTrain');b.disabled=true;
  try{
    const r=await fetch(`${API}/forecast/train`,{method:'POST'});
    const d=await r.json();if(!r.ok)throw new Error(d.detail||'failed');
    msg('Trained on '+d.training_flights+' flights',true);
  }catch(e){msg('Train failed: '+e.message,false);}
  finally{b.disabled=false;}
});

document.getElementById('btnForecast').addEventListener('click',async()=>{
  const b=document.getElementById('btnForecast');b.disabled=true;
  try{
    const r=await fetch(`${API}/forecast/run`,{method:'POST'});
    const d=await r.json();if(!r.ok)throw new Error(d.detail||'failed');
    fData=d.predictions||[];
    const ar=await fetch(`${API}/alerts`);
    aData=ar.ok?await ar.json():[];
    buildTimeline();
    msg(d.windows_predicted+' windows  •  '+d.alerts_generated+' alerts',true);
  }catch(e){msg('Forecast failed: '+e.message,false);}
  finally{b.disabled=false;}
});

// ── Boot ──────────────────────────────────────────────────────────────────────
initDesks(10);
loadForecast();  // auto-load on page open
loop();
</script>
</body>
</html>"""

    components.html(_SIM_HTML, height=860, scrolling=False)


# ── Security ───────────────────────────────────────────────────────────────────

elif page == "Security":
    st.markdown("## Security Checkpoint")
    st.caption("Passenger flow through security — derived from check-in forecast with a 20-min delay and 90% flow factor.")

    # Lane state control
    lane_resp = fetch_json(f"{API_BASE}/security/lanes")
    current_lanes = lane_resp["lanes_open"] if lane_resp else 0

    lc1, lc2, lc3 = st.columns([2, 1, 3])
    with lc1:
        new_lane_count = st.number_input("Lanes currently open", min_value=0, max_value=20, value=current_lanes)
    with lc2:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        if st.button("Update", key="update_lanes", use_container_width=True):
            requests.post(f"{API_BASE}/security/lanes", json={"lanes_open": new_lane_count})
            st.rerun()
    with lc3:
        st.markdown(f"<div style='margin-top:32px; color:#888; font-size:0.85rem'>Currently tracking <b style='color:#e0e0e0'>{current_lanes}</b> open lane(s)</div>", unsafe_allow_html=True)

    st.divider()

    if st.button("Run Security Forecast & Generate Alerts", type="primary", use_container_width=True):
        with st.spinner("Deriving security predictions from check-in…"):
            r = requests.post(f"{API_BASE}/security/run", timeout=120)
        if r.ok:
            d = r.json()
            st.success(f"{d['windows_predicted']} windows predicted · {d['alerts_generated']} alerts generated")
            st.rerun()
        else:
            st.error(f"Security forecast failed: {r.text}")

    # Charts
    sec_forecast = fetch_security_forecast()
    checkin_forecast = fetch_forecast()

    if not sec_forecast.empty:
        st.divider()

        peak_sec = int(sec_forecast["predicted_load"].max())
        total_sec = int(sec_forecast["predicted_load"].sum())
        open_sec = len(fetch_security_alerts("OPEN"))

        st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-box"><div class="kpi-val">{len(sec_forecast)}</div><div class="kpi-lbl">Time windows</div></div>
  <div class="kpi-box"><div class="kpi-val">{peak_sec}</div><div class="kpi-lbl">Peak pax / window</div></div>
  <div class="kpi-box"><div class="kpi-val">{total_sec:,}</div><div class="kpi-lbl">Total pax today</div></div>
  <div class="kpi-box"><div class="kpi-val">{open_sec}</div><div class="kpi-lbl">Open alerts</div></div>
</div>""", unsafe_allow_html=True)

        fig = go.Figure()

        # Check-in reference line
        if not checkin_forecast.empty:
            fig.add_trace(go.Scatter(
                x=checkin_forecast["window_start"],
                y=checkin_forecast["predicted_load"],
                name="Check-in load",
                line=dict(color="#3a7bd5", width=1.5, dash="dot"),
                opacity=0.5,
                hovertemplate="<b>Check-in %{x|%H:%M}</b><br>%{y} pax<extra></extra>",
            ))

        # Security bars
        fig.add_trace(go.Bar(
            x=sec_forecast["window_start"],
            y=sec_forecast["predicted_load"],
            name="Security load",
            marker=dict(
                color=sec_forecast["predicted_load"],
                colorscale=[[0, "#1a4a6a"], [0.5, "#c07830"], [1, "#c03030"]],
                showscale=False,
            ),
            hovertemplate="<b>Security %{x|%H:%M}</b><br>%{y} pax<extra></extra>",
        ))

        # Security threshold lines
        thresholds = fetch_json(f"{API_BASE}/thresholds")
        sec_cfg = thresholds.get("security", {}) if thresholds else {}
        sec_colors = {"level_1": "#f0c040", "level_2": "#f08040", "level_3": "#e05252"}
        for key, color in sec_colors.items():
            lvl = sec_cfg.get(key)
            if lvl:
                fig.add_hline(
                    y=lvl["threshold"],
                    line_dash="dot",
                    line_color=color,
                    line_width=1.5,
                    annotation_text=f"L{key[-1]}: {lvl['threshold']} pax",
                    annotation_position="right",
                    annotation_font_color=color,
                    annotation_font_size=11,
                )

        fig.update_layout(
            title="Security Checkpoint Load — 30-min Windows (20-min offset from check-in)",
            plot_bgcolor="#0f1117",
            paper_bgcolor="#0f1117",
            font_color="#e0e0e0",
            xaxis=dict(gridcolor="#2a2d3a", title=""),
            yaxis=dict(gridcolor="#2a2d3a", title="Passengers"),
            legend=dict(bgcolor="#1e2130", bordercolor="#2a2d3a"),
            margin=dict(l=10, r=80, t=40, b=10),
            height=340,
            barmode="overlay",
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Raw data table", expanded=False):
            st.dataframe(
                sec_forecast.rename(columns={
                    "window_start": "Window",
                    "checkin_load": "Check-in Pax",
                    "predicted_load": "Security Pax",
                }),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("No security forecast yet — click Run Security Forecast above.")

    st.divider()
    st.markdown("### Security Sensor Data")
    st.caption("VS133-P sensor at the security entrance — actual counts vs predicted load.")

    scol1, scol2, scol3 = st.columns(3)
    with scol1:
        if st.button("Simulate Security Sensor (full day)", use_container_width=True):
            with st.spinner("Injecting security sensor data…"):
                r = requests.post(f"{API_BASE}/security/sensor/simulate", timeout=30)
            if r.ok:
                d = r.json()
                st.success(f"{d.get('windows_injected', 0)} windows injected")
                st.rerun()
            else:
                st.error(f"Failed: {r.text}")
    with scol2:
        if st.button("Reconcile vs Predictions", use_container_width=True):
            with st.spinner("Reconciling…"):
                r = requests.post(f"{API_BASE}/security/sensor/reconcile", timeout=30)
            if r.ok:
                st.session_state["sec_reconcile"] = r.json()
                st.rerun()
            else:
                st.error(f"Failed: {r.text}")
    with scol3:
        if st.button("Auto-calibrate Flow Factor", use_container_width=True, help="Derives empirical flow_factor from matched check-in vs security sensor counts"):
            with st.spinner("Calibrating…"):
                r = requests.post(f"{API_BASE}/security/sensor/calibrate", timeout=30)
            if r.ok:
                d = r.json()
                if d.get("status") == "calibrated":
                    st.success(f"Flow factor updated: {d['old_flow_factor']} → **{d['new_flow_factor']}** ({d['windows_matched']} windows)")
                else:
                    st.warning(f"Not enough data yet ({d.get('windows_matched', 0)} windows matched, need ≥5)")
            else:
                st.error(f"Failed: {r.text}")

    # sensor counts chart
    sec_counts_raw = fetch_json(f"{API_BASE}/security/sensor/counts?hours=24")
    if sec_counts_raw:
        sec_counts = pd.DataFrame(sec_counts_raw)
        sec_counts["window_start"] = pd.to_datetime(sec_counts["window_start"])

        fig_s = go.Figure()
        fig_s.add_trace(go.Bar(
            x=sec_counts["window_start"],
            y=sec_counts["total_in"],
            name="Actual (sensor)",
            marker_color="#52c07a",
            hovertemplate="<b>%{x|%H:%M}</b><br>%{y} pax (actual)<extra></extra>",
        ))
        if not sec_forecast.empty:
            fig_s.add_trace(go.Scatter(
                x=sec_forecast["window_start"],
                y=sec_forecast["predicted_load"],
                name="Predicted",
                line=dict(color="#f0a500", width=2, dash="dot"),
                hovertemplate="<b>%{x|%H:%M}</b><br>%{y} pax (predicted)<extra></extra>",
            ))
        fig_s.update_layout(
            title="Security Sensor: Actual vs Predicted",
            plot_bgcolor="#0f1117", paper_bgcolor="#0f1117", font_color="#e0e0e0",
            xaxis=dict(gridcolor="#2a2d3a"), yaxis=dict(gridcolor="#2a2d3a", title="Passengers"),
            legend=dict(bgcolor="#1e2130", bordercolor="#2a2d3a"),
            margin=dict(l=10, r=10, t=40, b=10), height=260, barmode="overlay",
        )
        st.plotly_chart(fig_s, use_container_width=True)

    # reconcile results
    if "sec_reconcile" in st.session_state:
        rec = pd.DataFrame(st.session_state["sec_reconcile"])
        if not rec.empty:
            confirmed = len(rec[rec["status"] == "confirmed"])
            escalated = len(rec[rec["status"] == "escalated"])
            no_data   = len(rec[rec["status"] == "no_sensor_data"])
            st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-box"><div class="kpi-val" style="color:#52c07a">{confirmed}</div><div class="kpi-lbl">Confirmed</div></div>
  <div class="kpi-box"><div class="kpi-val" style="color:#e05252">{escalated}</div><div class="kpi-lbl">Escalated</div></div>
  <div class="kpi-box"><div class="kpi-val" style="color:#888">{no_data}</div><div class="kpi-lbl">No sensor data</div></div>
</div>""", unsafe_allow_html=True)
            with st.expander("Reconcile detail", expanded=False):
                st.dataframe(rec, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Security Lane Alerts")

    emp_name = st.text_input("Your name (audit trail)", value=st.session_state.get("employee_name", ""), placeholder="Enter your name…", key="sec_emp")
    if emp_name:
        st.session_state["employee_name"] = emp_name

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)
    stab_open, stab_ack, stab_all = st.tabs(["Open", "Acknowledged", "All"])

    def render_security_alerts(df: pd.DataFrame, show_ack: bool = False):
        if df.empty:
            st.markdown("<div style='color:#666; padding:20px 0'>No alerts in this category.</div>", unsafe_allow_html=True)
            return
        for _, row in df.iterrows():
            alert_type  = row.get("type", "")
            status      = row.get("status", "OPEN")
            lanes_add   = row.get("lanes_to_add") or 0
            lanes_close = row.get("lanes_to_close") or 0
            lanes_open  = row.get("lanes_to_open") or 0
            load        = row.get("predicted_load", "?")
            win         = str(row.get("window_start", ""))[:16]

            if status == "ACKNOWLEDGED":
                card_cls, tag_cls, tag_txt = "alert-ack", "desk-ok", "✓ Acknowledged"
            elif alert_type == "security_close":
                card_cls, tag_cls, tag_txt = "alert-close", "desk-close", f"Close {lanes_close} lane(s)"
            else:
                card_cls, tag_cls, tag_txt = "alert-open", "desk-open", f"Open {lanes_add} more lane(s)"

            col_card, col_btn = st.columns([5, 1])
            with col_card:
                st.markdown(f"""
<div class="alert-card {card_cls}">
  <div class="alert-title">{row['message']}</div>
  <span class="desk-tag {tag_cls}">{tag_txt}</span>
  <div class="alert-sub">Window: {win} &nbsp;·&nbsp; {load} pax &nbsp;·&nbsp; {lanes_open} lane(s) needed</div>
</div>""", unsafe_allow_html=True)
            with col_btn:
                if show_ack and status == "OPEN":
                    st.markdown("<div style='margin-top:18px'></div>", unsafe_allow_html=True)
                    emp = st.session_state.get("employee_name", "employee") or "employee"
                    if st.button("Confirm", key=f"sec_ack_{row['id']}"):
                        requests.post(f"{API_BASE}/security/alerts/{row['id']}/acknowledge", json={"employee": emp})
                        st.rerun()

    with stab_open:
        render_security_alerts(fetch_security_alerts("OPEN"), show_ack=True)
    with stab_ack:
        render_security_alerts(fetch_security_alerts("ACKNOWLEDGED"))
    with stab_all:
        render_security_alerts(fetch_security_alerts())


# ── Gate ───────────────────────────────────────────────────────────────────────

elif page == "Gate":
    st.markdown("## Gate (Boarding Control)")
    st.caption("Ticket scan / boarding agents — derived from security forecast with a 30-min delay and 98% flow factor.")

    # Agent state control
    agent_resp = fetch_json(f"{API_BASE}/gate/agents")
    current_agents = agent_resp["agents_open"] if agent_resp else 0

    gc1, gc2, gc3 = st.columns([2, 1, 3])
    with gc1:
        new_agent_count = st.number_input("Agents currently deployed", min_value=0, max_value=20, value=current_agents)
    with gc2:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        if st.button("Update", key="update_agents", use_container_width=True):
            requests.post(f"{API_BASE}/gate/agents", json={"agents_open": new_agent_count})
            st.rerun()
    with gc3:
        st.markdown(f"<div style='margin-top:32px; color:#888; font-size:0.85rem'>Currently tracking <b style='color:#e0e0e0'>{current_agents}</b> deployed agent(s)</div>", unsafe_allow_html=True)

    st.divider()

    if st.button("Run Gate Forecast & Generate Alerts", type="primary", use_container_width=True):
        with st.spinner("Deriving gate predictions from security…"):
            r = requests.post(f"{API_BASE}/gate/run", timeout=120)
        if r.ok:
            d = r.json()
            st.success(f"{d['windows_predicted']} windows predicted · {d['alerts_generated']} alerts generated")
            st.rerun()
        else:
            st.error(f"Gate forecast failed: {r.text}")

    # Charts
    gate_forecast = fetch_gate_forecast()
    sec_forecast = fetch_security_forecast()

    if not gate_forecast.empty:
        st.divider()

        peak_gate = int(gate_forecast["predicted_load"].max())
        total_gate = int(gate_forecast["predicted_load"].sum())
        open_gate = len(fetch_gate_alerts("OPEN"))

        st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-box"><div class="kpi-val">{len(gate_forecast)}</div><div class="kpi-lbl">Time windows</div></div>
  <div class="kpi-box"><div class="kpi-val">{peak_gate}</div><div class="kpi-lbl">Peak pax / window</div></div>
  <div class="kpi-box"><div class="kpi-val">{total_gate:,}</div><div class="kpi-lbl">Total pax today</div></div>
  <div class="kpi-box"><div class="kpi-val">{open_gate}</div><div class="kpi-lbl">Open alerts</div></div>
</div>""", unsafe_allow_html=True)

        fig = go.Figure()

        # Security reference line
        if not sec_forecast.empty:
            fig.add_trace(go.Scatter(
                x=sec_forecast["window_start"],
                y=sec_forecast["predicted_load"],
                name="Security load",
                line=dict(color="#c07830", width=1.5, dash="dot"),
                opacity=0.5,
                hovertemplate="<b>Security %{x|%H:%M}</b><br>%{y} pax<extra></extra>",
            ))

        # Gate bars
        fig.add_trace(go.Bar(
            x=gate_forecast["window_start"],
            y=gate_forecast["predicted_load"],
            name="Gate load",
            marker=dict(
                color=gate_forecast["predicted_load"],
                colorscale=[[0, "#1a3a6a"], [0.5, "#8030c0"], [1, "#c03080"]],
                showscale=False,
            ),
            hovertemplate="<b>Gate %{x|%H:%M}</b><br>%{y} pax<extra></extra>",
        ))

        # Gate threshold lines
        thresholds = fetch_json(f"{API_BASE}/thresholds")
        gate_cfg = thresholds.get("gate", {}) if thresholds else {}
        gate_colors = {"level_1": "#f0c040", "level_2": "#f08040", "level_3": "#e05252"}
        for key, color in gate_colors.items():
            lvl = gate_cfg.get(key)
            if lvl:
                fig.add_hline(
                    y=lvl["threshold"],
                    line_dash="dot",
                    line_color=color,
                    line_width=1.5,
                    annotation_text=f"L{key[-1]}: {lvl['threshold']} pax",
                    annotation_position="right",
                    annotation_font_color=color,
                    annotation_font_size=11,
                )

        fig.update_layout(
            title="Gate Boarding Load — 30-min Windows (30-min offset from security)",
            plot_bgcolor="#0f1117",
            paper_bgcolor="#0f1117",
            font_color="#e0e0e0",
            xaxis=dict(gridcolor="#2a2d3a", title=""),
            yaxis=dict(gridcolor="#2a2d3a", title="Passengers"),
            legend=dict(bgcolor="#1e2130", bordercolor="#2a2d3a"),
            margin=dict(l=10, r=80, t=40, b=10),
            height=340,
            barmode="overlay",
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Raw data table", expanded=False):
            st.dataframe(
                gate_forecast.rename(columns={
                    "window_start": "Window",
                    "security_load": "Security Pax",
                    "predicted_load": "Gate Pax",
                }),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("No gate forecast yet — click Run Gate Forecast above (requires security forecast first).")

    st.divider()
    st.markdown("### Gate Sensor Data")
    st.caption("VS133-P sensor at the boarding gate — actual scanned counts vs predicted load.")

    gcol1, gcol2, gcol3 = st.columns(3)
    with gcol1:
        if st.button("Simulate Gate Sensor (full day)", use_container_width=True):
            with st.spinner("Injecting gate sensor data…"):
                r = requests.post(f"{API_BASE}/gate/sensor/simulate", timeout=30)
            if r.ok:
                d = r.json()
                st.success(f"{d.get('windows_injected', 0)} windows injected")
                st.rerun()
            else:
                st.error(f"Failed: {r.text}")
    with gcol2:
        if st.button("Reconcile vs Predictions", key="gate_reconcile_btn", use_container_width=True):
            with st.spinner("Reconciling…"):
                r = requests.post(f"{API_BASE}/gate/sensor/reconcile", timeout=30)
            if r.ok:
                st.session_state["gate_reconcile"] = r.json()
                st.rerun()
            else:
                st.error(f"Failed: {r.text}")
    with gcol3:
        if st.button("Auto-calibrate Flow Factor", key="gate_calibrate_btn", use_container_width=True,
                     help="Derives empirical gate flow_factor from matched security vs gate sensor counts"):
            with st.spinner("Calibrating…"):
                r = requests.post(f"{API_BASE}/gate/sensor/calibrate", timeout=30)
            if r.ok:
                d = r.json()
                if d.get("status") == "calibrated":
                    st.success(f"Gate flow factor updated: {d['old_flow_factor']} → **{d['new_flow_factor']}** ({d['windows_matched']} windows)")
                else:
                    st.warning(f"Not enough data yet ({d.get('windows_matched', 0)} windows matched, need ≥5)")
            else:
                st.error(f"Failed: {r.text}")

    # sensor counts chart
    gate_counts_raw = fetch_json(f"{API_BASE}/gate/sensor/counts?hours=24")
    if gate_counts_raw:
        gate_counts = pd.DataFrame(gate_counts_raw)
        gate_counts["window_start"] = pd.to_datetime(gate_counts["window_start"])

        fig_g = go.Figure()
        fig_g.add_trace(go.Bar(
            x=gate_counts["window_start"],
            y=gate_counts["total_in"],
            name="Actual (sensor)",
            marker_color="#a052e0",
            hovertemplate="<b>%{x|%H:%M}</b><br>%{y} pax (actual)<extra></extra>",
        ))
        if not gate_forecast.empty:
            fig_g.add_trace(go.Scatter(
                x=gate_forecast["window_start"],
                y=gate_forecast["predicted_load"],
                name="Predicted",
                line=dict(color="#f0a500", width=2, dash="dot"),
                hovertemplate="<b>%{x|%H:%M}</b><br>%{y} pax (predicted)<extra></extra>",
            ))
        fig_g.update_layout(
            title="Gate Sensor: Actual vs Predicted",
            plot_bgcolor="#0f1117", paper_bgcolor="#0f1117", font_color="#e0e0e0",
            xaxis=dict(gridcolor="#2a2d3a"), yaxis=dict(gridcolor="#2a2d3a", title="Passengers"),
            legend=dict(bgcolor="#1e2130", bordercolor="#2a2d3a"),
            margin=dict(l=10, r=10, t=40, b=10), height=260, barmode="overlay",
        )
        st.plotly_chart(fig_g, use_container_width=True)

    # reconcile results
    if "gate_reconcile" in st.session_state:
        rec = pd.DataFrame(st.session_state["gate_reconcile"])
        if not rec.empty:
            confirmed = len(rec[rec["status"] == "confirmed"])
            escalated = len(rec[rec["status"] == "escalated"])
            no_data   = len(rec[rec["status"] == "no_sensor_data"])
            st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-box"><div class="kpi-val" style="color:#52c07a">{confirmed}</div><div class="kpi-lbl">Confirmed</div></div>
  <div class="kpi-box"><div class="kpi-val" style="color:#e05252">{escalated}</div><div class="kpi-lbl">Escalated</div></div>
  <div class="kpi-box"><div class="kpi-val" style="color:#888">{no_data}</div><div class="kpi-lbl">No sensor data</div></div>
</div>""", unsafe_allow_html=True)
            with st.expander("Reconcile detail", expanded=False):
                st.dataframe(rec, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### Gate Agent Alerts")

    emp_name = st.text_input("Your name (audit trail)", value=st.session_state.get("employee_name", ""), placeholder="Enter your name…", key="gate_emp")
    if emp_name:
        st.session_state["employee_name"] = emp_name

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)
    gtab_open, gtab_ack, gtab_all = st.tabs(["Open", "Acknowledged", "All"])

    def render_gate_alerts(df: pd.DataFrame, show_ack: bool = False):
        if df.empty:
            st.markdown("<div style='color:#666; padding:20px 0'>No alerts in this category.</div>", unsafe_allow_html=True)
            return
        for _, row in df.iterrows():
            alert_type   = row.get("type", "")
            status       = row.get("status", "OPEN")
            agents_add   = row.get("agents_to_add") or 0
            agents_close = row.get("agents_to_close") or 0
            agents_open  = row.get("agents_to_open") or 0
            load         = row.get("predicted_load", "?")
            win          = str(row.get("window_start", ""))[:16]

            if status == "ACKNOWLEDGED":
                card_cls, tag_cls, tag_txt = "alert-ack", "desk-ok", "✓ Acknowledged"
            elif alert_type == "gate_close":
                card_cls, tag_cls, tag_txt = "alert-close", "desk-close", f"Release {agents_close} agent(s)"
            else:
                card_cls, tag_cls, tag_txt = "alert-open", "desk-open", f"Deploy {agents_add} more agent(s)"

            col_card, col_btn = st.columns([5, 1])
            with col_card:
                st.markdown(f"""
<div class="alert-card {card_cls}">
  <div class="alert-title">{row['message']}</div>
  <span class="desk-tag {tag_cls}">{tag_txt}</span>
  <div class="alert-sub">Window: {win} &nbsp;·&nbsp; {load} pax &nbsp;·&nbsp; {agents_open} agent(s) needed</div>
</div>""", unsafe_allow_html=True)
            with col_btn:
                if show_ack and status == "OPEN":
                    st.markdown("<div style='margin-top:18px'></div>", unsafe_allow_html=True)
                    emp = st.session_state.get("employee_name", "employee") or "employee"
                    if st.button("Confirm", key=f"gate_ack_{row['id']}"):
                        requests.post(f"{API_BASE}/gate/alerts/{row['id']}/acknowledge", json={"employee": emp})
                        st.rerun()

    with gtab_open:
        render_gate_alerts(fetch_gate_alerts("OPEN"), show_ack=True)
    with gtab_ack:
        render_gate_alerts(fetch_gate_alerts("ACKNOWLEDGED"))
    with gtab_all:
        render_gate_alerts(fetch_gate_alerts())


# ── Settings ───────────────────────────────────────────────────────────────────

elif page == "Settings":
    st.markdown("## Settings")

    try:
        r = requests.get(f"{API_BASE}/thresholds", timeout=5)
        if not r.ok:
            st.error("Could not load thresholds")
            st.stop()
        cfg = r.json()["checkin"]
    except Exception as e:
        st.error(f"Could not connect to API: {e}")
        st.stop()

    with st.expander("Auto-detect thresholds from data", expanded=True):
        st.caption("Analyses historical windows to recommend thresholds. Congestion delays are factored in automatically.")
        if st.button("Analyse & recommend", use_container_width=True):
            with st.spinner("Analysing…"):
                resp = requests.post(f"{API_BASE}/thresholds/auto-detect", timeout=30)
            if resp.ok:
                data = resp.json()
                rec  = data["recommended"]
                ana  = data["analysis"]

                st.success(f"Analysed **{ana['windows_analysed']}** windows")

                st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-box"><div class="kpi-val">{ana['pax_min']}</div><div class="kpi-lbl">Min pax</div></div>
  <div class="kpi-box"><div class="kpi-val">{ana['pax_p50']}</div><div class="kpi-lbl">Median</div></div>
  <div class="kpi-box"><div class="kpi-val">{ana['pax_p75']}</div><div class="kpi-lbl">75th pct</div></div>
  <div class="kpi-box"><div class="kpi-val">{ana['pax_p90']}</div><div class="kpi-lbl">90th pct</div></div>
  <div class="kpi-box"><div class="kpi-val">{ana['pax_max']}</div><div class="kpi-lbl">Max</div></div>
</div>""", unsafe_allow_html=True)

                if ana["delay_adjusted"]:
                    st.info(f"Congestion delay active — avg {ana['avg_delay_min']} min across {ana['pct_windows_with_delay']}% of windows")

                st.markdown("**Recommended thresholds**")
                rc1, rc2, rc3 = st.columns(3)
                rc1.metric("Level 1", f"{rec['level_1']['threshold']} pax → {rec['level_1']['desks_to_open']} desk(s)")
                rc2.metric("Level 2", f"{rec['level_2']['threshold']} pax → {rec['level_2']['desks_to_open']} desk(s)")
                rc3.metric("Level 3", f"{rec['level_3']['threshold']} pax → {rec['level_3']['desks_to_open']} desk(s)")
                st.caption(f"Baseline: **{rec['baseline_desks']}** desk · Capacity estimate: **{ana['pax_per_desk_estimate']} pax/desk**")

                st.session_state["auto_rec"] = rec
            else:
                st.error(f"Detection failed: {resp.text}")

        if st.session_state.get("auto_rec"):
            if st.button("Apply recommended thresholds", type="primary", use_container_width=True):
                requests.post(f"{API_BASE}/thresholds/auto-detect?apply=true", timeout=30)
                del st.session_state["auto_rec"]
                st.success("Thresholds updated")
                st.rerun()

    st.divider()
    st.markdown("**Manual override**")
    with st.form("thresholds_form"):
        cols = st.columns(3)
        levels = {}
        for i, (key, col) in enumerate(zip(["level_1", "level_2", "level_3"], cols)):
            with col:
                st.markdown(f"**Level {i+1}**")
                lvl = cfg[key]
                levels[key] = {
                    "threshold":    st.number_input("Threshold (pax)", value=lvl["threshold"], min_value=1, key=f"t_{key}"),
                    "desks_to_open": st.number_input("Desks to open",  value=lvl["desks_to_open"], min_value=1, key=f"d_{key}"),
                    "message":      st.text_input("Message",           value=lvl["message"], key=f"m_{key}"),
                }
        if st.form_submit_button("Save", type="primary"):
            resp = requests.post(f"{API_BASE}/thresholds", json=levels)
            st.success("Saved") if resp.ok else st.error(f"Failed: {resp.text}")
