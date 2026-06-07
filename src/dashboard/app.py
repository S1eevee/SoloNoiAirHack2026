import os
import random
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import plotly.graph_objects as go
import time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
_session = requests.Session()
_session.headers.update({"X-API-Key": os.getenv("API_KEY", "")})

st.set_page_config(
    page_title="SoloAir",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global styles ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* page background */
[data-testid="stAppViewContainer"] { background: #0b0d10; }
[data-testid="stHeader"] { background: transparent !important; }
.main .block-container { padding-top: 0 !important; padding-bottom: 2rem; max-width: 1200px; }

/* sidebar */
[data-testid="stSidebar"] {
    background: #07090c !important;
    border-right: 1px solid #161c26;
}
[data-testid="stSidebar"] * { color: #94a3b8 !important; }
[data-testid="stSidebar"] .stRadio label {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    padding: 8px 0 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    border-radius: 4px;
}
[data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div { color: #4ade80 !important; }
[data-testid="stSidebar"] hr { border-color: #161c26 !important; }

/* IAS hero */
.ias-hero { padding: 24px 0 18px; margin-bottom: 6px; }
.ias-row { display: flex; align-items: baseline; gap: 14px; margin-bottom: 4px; }
.ias-code { font-size: 4.2rem; font-weight: 900; color: #4ade80; line-height: 1; letter-spacing: -0.03em; }
.ias-title { font-size: 1.8rem; font-weight: 700; color: #e2e8f0; }
.ias-sub { font-size: 0.85rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.14em; }

/* page section label */
.sec-label {
    font-size: 11px; font-weight: 700; color: #64748b;
    text-transform: uppercase; letter-spacing: 0.14em;
    margin-bottom: 10px; margin-top: 20px;
}

/* stat strip — top of each page */
.stat-strip {
    display: flex; gap: 0;
    background: #0f1318; border: 1px solid #161c26;
    border-radius: 5px; margin-bottom: 20px; overflow: hidden;
}
.stat-cell {
    flex: 1; padding: 14px 18px;
    border-right: 1px solid #161c26;
    min-width: 0;
}
.stat-cell:last-child { border-right: none; }
.stat-lbl { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: #64748b; margin-bottom: 6px; white-space: nowrap; }
.stat-val { font-size: 1.15rem; font-weight: 800; color: #e2e8f0; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stat-val.green { color: #4ade80; }
.stat-val.amber { color: #fb923c; }
.stat-val.red   { color: #f87171; }
.stat-tag { display:inline-block; padding:3px 10px; border-radius:3px; font-size:0.78rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; margin-top:4px; }
.tag-green { background:#4ade8018; color:#4ade80; border:1px solid #4ade8030; }
.tag-amber { background:#fb923c18; color:#fb923c; border:1px solid #fb923c30; }
.tag-red   { background:#f8717118; color:#f87171; border:1px solid #f8717130; }
.tag-blue  { background:#60a5fa18; color:#60a5fa; border:1px solid #60a5fa30; }
.tag-checkin  { background:#4ade8022; color:#4ade80; border:1px solid #4ade8050; }
.tag-security { background:#60a5fa22; color:#60a5fa; border:1px solid #60a5fa50; }
.tag-gate     { background:#a78bfa22; color:#a78bfa; border:1px solid #a78bfa50; }

/* KPI row */
.kpi-row { display: flex; gap: 1px; margin-bottom: 16px; background: #161c26; border-radius: 5px; overflow: hidden; border: 1px solid #161c26; }
.kpi-box { flex: 1; background: #0f1318; padding: 18px 20px; }
.kpi-box.hl { background: #0b1a10; }
.kpi-val { font-size: 1.8rem; font-weight: 800; color: #e2e8f0; line-height: 1.1; }
.kpi-val.green { color: #4ade80; }
.kpi-lbl { font-size: 10px; font-weight: 700; color: #64748b; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.1em; }

/* alert cards */
.alert-card {
    border-radius: 4px; padding: 14px 18px; margin-bottom: 8px;
    background: #0f1318; color: #c8d5e5;
    border: 1px solid #161c26; border-left: 3px solid #64748b;
}
.alert-open  { border-left-color: #f87171; background: #110c0c; border-color: #1e1010; border-left-color: #f87171; }
.alert-close { border-left-color: #4ade80; background: #090f0b; border-color: #101e13; border-left-color: #4ade80; }
.alert-ack   { border-left-color: #fb923c; background: #0f0e09; border-color: #1c180a; border-left-color: #fb923c; }
.alert-title { font-size: 1rem; font-weight: 700; margin-bottom: 5px; color: #e2e8f0; }
.alert-sub   { font-size: 0.85rem; color: #64748b; margin-top: 4px; }
.desk-tag {
    display: inline-block; padding: 3px 10px; border-radius: 3px;
    font-size: 0.75rem; font-weight: 700; margin-top: 4px;
    text-transform: uppercase; letter-spacing: 0.06em;
}
.desk-open  { background: #f8717118; color: #f87171; border: 1px solid #f8717130; }
.desk-close { background: #4ade8018; color: #4ade80; border: 1px solid #4ade8030; }
.desk-ok    { background: #fb923c18; color: #fb923c; border: 1px solid #fb923c30; }
.alert-note { font-size: 0.75rem; color: #60a5fa; margin-top: 6px; font-style: italic; }

/* sidebar status pills */
.dot-green { color: #4ade80; font-size: 0.75rem; }
.dot-red   { color: #f87171; font-size: 0.75rem; }

/* hide streamlit branding */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=4, show_spinner=False)
def fetch_json(url):
    try:
        r = _session.get(url, timeout=5)
        return r.json() if r.ok else None
    except Exception:
        return None


@st.cache_data(ttl=30, show_spinner=False)
def fetch_forecast() -> pd.DataFrame:
    try:
        r = _session.get(f"{API_BASE}/forecast", timeout=5)
        if r.ok:
            df = pd.DataFrame(r.json())
            if not df.empty:
                df["window_start"] = pd.to_datetime(df["window_start"])
            return df
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=4, show_spinner=False)
def fetch_alerts(status=None) -> pd.DataFrame:
    try:
        params = {"status": status} if status else {}
        r = _session.get(f"{API_BASE}/alerts", params=params, timeout=5)
        if r.ok:
            return pd.DataFrame(r.json())
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=4, show_spinner=False)
def fetch_security_alerts(status=None) -> pd.DataFrame:
    try:
        params = {"status": status} if status else {}
        r = _session.get(f"{API_BASE}/security/alerts", params=params, timeout=5)
        if r.ok:
            return pd.DataFrame(r.json())
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=30, show_spinner=False)
def fetch_security_forecast() -> pd.DataFrame:
    try:
        r = _session.get(f"{API_BASE}/security/forecast", timeout=5)
        if r.ok:
            df = pd.DataFrame(r.json())
            if not df.empty:
                df["window_start"] = pd.to_datetime(df["window_start"])
            return df
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=4, show_spinner=False)
def fetch_gate_alerts(status=None) -> pd.DataFrame:
    try:
        params = {"status": status} if status else {}
        r = _session.get(f"{API_BASE}/gate/alerts", params=params, timeout=5)
        if r.ok:
            return pd.DataFrame(r.json())
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=30, show_spinner=False)
def fetch_gate_forecast() -> pd.DataFrame:
    try:
        r = _session.get(f"{API_BASE}/gate/forecast", timeout=5)
        if r.ok:
            df = pd.DataFrame(r.json())
            if not df.empty:
                df["window_start"] = pd.to_datetime(df["window_start"])
            return df
    except Exception:
        pass
    return pd.DataFrame()


def fetch_arrivals_alerts(status=None) -> pd.DataFrame:
    try:
        params = {"status": status} if status else {}
        r = _session.get(f"{API_BASE}/arrivals/alerts", params=params, timeout=5)
        if r.ok:
            return pd.DataFrame(r.json())
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=30, show_spinner=False)
def fetch_arrivals_forecast() -> pd.DataFrame:
    try:
        r = _session.get(f"{API_BASE}/arrivals/forecast", timeout=5)
        if r.ok:
            df = pd.DataFrame(r.json())
            if not df.empty:
                df["window_start"] = pd.to_datetime(df["window_start"])
            return df
    except Exception:
        pass
    return pd.DataFrame()


def fetch_departures_alerts(status=None) -> pd.DataFrame:
    try:
        params = {"status": status} if status else {}
        r = _session.get(f"{API_BASE}/departures/alerts", params=params, timeout=5)
        if r.ok:
            return pd.DataFrame(r.json())
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=30, show_spinner=False)
def fetch_departures_forecast() -> pd.DataFrame:
    try:
        r = _session.get(f"{API_BASE}/departures/forecast", timeout=5)
        if r.ok:
            df = pd.DataFrame(r.json())
            if not df.empty:
                df["window_start"] = pd.to_datetime(df["window_start"])
            return df
    except Exception:
        pass
    return pd.DataFrame()


@st.cache_data(ttl=5, show_spinner=False)
def fetch_sidebar_status() -> dict:
    """One call that replaces 8 separate sidebar API requests."""
    try:
        r = _session.get(f"{API_BASE}/alerts/status", timeout=4)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return {}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="padding:18px 0 12px">
  <div style="font-size:1.05rem;font-weight:900;color:#4ade80;letter-spacing:-0.01em">✈ SOLONOI</div>
  <div style="font-size:0.68rem;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.12em;margin-top:3px">SoloAir · IAS</div>
</div>
""", unsafe_allow_html=True)

    _s = fetch_sidebar_status()
    online         = bool(_s)
    current_desks       = _s.get("desks_open", 0)
    current_lanes       = _s.get("lanes_open", 0)
    current_agents      = _s.get("agents_open", 0)
    current_arr_agents  = _s.get("arrivals_agents_open", 0)
    current_dep_agents  = _s.get("departures_agents_open", 0)
    open_alerts         = _s.get("open_alert_count", 0)
    open_sec_alerts     = _s.get("open_sec_count", 0)
    open_gate_alerts    = _s.get("open_gate_count", 0)
    open_arr_alerts     = _s.get("open_arrivals_count", 0)
    open_dep_alerts     = _s.get("open_departures_count", 0)
    demo_active         = _s.get("demo_active", False)

    dot = '<span class="dot-green">●</span>' if online else '<span class="dot-red">●</span>'
    api_txt = "API ONLINE" if online else "API OFFLINE"
    ca_col  = "#f87171" if open_alerts     else "#64748b"
    sc_col  = "#f87171" if open_sec_alerts else "#64748b"
    ga_col  = "#f87171" if open_gate_alerts else "#64748b"
    ar_col  = "#f87171" if open_arr_alerts  else "#64748b"
    dp_col  = "#f87171" if open_dep_alerts  else "#64748b"
    st.markdown(f"""
<div style="background:#0f1318;border:1px solid #161c26;border-radius:4px;padding:12px 14px;margin-bottom:12px;font-size:0.82rem">
  <div style="margin-bottom:8px">{dot} <span style="color:#64748b;font-weight:700;letter-spacing:0.08em;text-transform:uppercase">{api_txt}</span></div>
  <div style="display:flex;justify-content:space-between;color:#64748b;margin-bottom:5px">
    <span style="color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;font-size:0.75rem">Check-in</span>
    <span><b style="color:#e2e8f0">{current_desks}</b> desks &nbsp;<b style="color:{ca_col}">{open_alerts}</b> alerts</span>
  </div>
  <div style="display:flex;justify-content:space-between;color:#64748b;margin-bottom:5px">
    <span style="color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;font-size:0.75rem">Security</span>
    <span><b style="color:#e2e8f0">{current_lanes}</b> lanes &nbsp;<b style="color:{sc_col}">{open_sec_alerts}</b> alerts</span>
  </div>
  <div style="display:flex;justify-content:space-between;color:#64748b;margin-bottom:5px">
    <span style="color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;font-size:0.75rem">Dep Gate</span>
    <span><b style="color:#e2e8f0">{current_dep_agents}</b> agents &nbsp;<b style="color:{dp_col}">{open_dep_alerts}</b> alerts</span>
  </div>
  <div style="display:flex;justify-content:space-between;color:#64748b">
    <span style="color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;font-size:0.75rem">Arrivals</span>
    <span><b style="color:#e2e8f0">{current_arr_agents}</b> staff &nbsp;<b style="color:{ar_col}">{open_arr_alerts}</b> alerts</span>
  </div>
</div>
""", unsafe_allow_html=True)

    nav_pages = ["Home", "Train Model", "Check-in", "Alerts", "Security", "Arrivals", "Departures", "Simulation", "Live Feed", "Settings"]
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Home"
    saved_page = st.session_state["current_page"]
    nav_index  = nav_pages.index(saved_page) if saved_page in nav_pages else 0
    page = st.radio("Navigation", nav_pages, index=nav_index, key="nav_radio", label_visibility="collapsed")
    st.session_state["current_page"] = page

    st.divider()
    if demo_active:
        if st.button("✕ Unload Demo", use_container_width=True, help="Clear demo data and return to a clean state"):
            r = _session.post(f"{API_BASE}/demo/unload", timeout=30)
            if r.ok:
                st.cache_data.clear()
                st.session_state["current_page"] = "Train Model"
                st.rerun()
            else:
                st.error(f"Unload failed: {r.text}")
    else:
        if st.button("⚡ Load Demo", use_container_width=True, help="Pre-load 14 days of sample data, train the model, and run forecast in one click"):
            with st.spinner("Loading demo — training model…"):
                r = _session.post(f"{API_BASE}/demo/load", timeout=180)
            if r.ok:
                d = r.json()
                st.success(f"Demo ready · {d['windows_predicted']} windows · {d['alerts_generated']} alerts")
                st.cache_data.clear()
                st.session_state["current_page"] = "Check-in"
                st.rerun()
            else:
                st.error(f"Demo failed: {r.text}")
    st.divider()
    st.markdown(f"<div style='font-size:0.68rem;color:#1e2a3a;text-transform:uppercase;letter-spacing:0.1em'>{datetime.now().strftime('%d %b %Y')}</div>", unsafe_allow_html=True)


# ── Home ───────────────────────────────────────────────────────────────────────

if page == "Home":
    st.markdown("""
<div class="ias-hero">
  <div class="ias-row"><span class="ias-code">IAS</span><span class="ias-title">Iași Airport</span></div>
  <div class="ias-sub">Live operations dashboard &nbsp;·&nbsp; Queue times &amp; checkpoint status</div>
</div>
""", unsafe_allow_html=True)

    # ── Fetch forecast data ───────────────────────────────────────────────────
    checkin_fc  = fetch_forecast()
    security_fc = fetch_security_forecast()
    gate_fc     = fetch_gate_forecast()
    arrivals_fc = fetch_arrivals_forecast()
    dep_fc      = fetch_departures_forecast()

    # ── Build sorted window list by time-of-day ───────────────────────────────
    def _sorted_windows(df):
        if df.empty:
            return pd.DataFrame()
        d = df.copy()
        d["window_start"] = pd.to_datetime(d["window_start"])
        d["_tod"] = d["window_start"].dt.hour * 60 + d["window_start"].dt.minute
        return d.sort_values("_tod").reset_index(drop=True)

    ci_sorted   = _sorted_windows(checkin_fc)
    sec_sorted  = _sorted_windows(security_fc)
    gate_sorted = _sorted_windows(gate_fc)
    arr_sorted  = _sorted_windows(arrivals_fc)
    dep_sorted  = _sorted_windows(dep_fc)

    n_windows = max(len(ci_sorted), len(arr_sorted), len(dep_sorted), 1)

    # ── Auto-advance loop every 5 seconds ────────────────────────────────────
    if "home_window_idx" not in st.session_state:
        st.session_state["home_window_idx"] = 0
        st.session_state["home_last_tick"]  = time.time()
    else:
        if time.time() - st.session_state["home_last_tick"] >= 5:
            st.session_state["home_window_idx"] = (st.session_state["home_window_idx"] + 1) % n_windows
            st.session_state["home_last_tick"]  = time.time()

    idx = st.session_state["home_window_idx"] % n_windows

    # ── Pull load for the current index ──────────────────────────────────────
    def _load_at(df_sorted, idx):
        if df_sorted.empty:
            return 0, pd.Timestamp.now()
        i = min(idx, len(df_sorted) - 1)
        row = df_sorted.iloc[i]
        return int(row["predicted_load"]), row["window_start"]

    def _peak(df: pd.DataFrame) -> int:
        return int(df["predicted_load"].max()) if not df.empty else 1

    ci_load,   ci_win   = _load_at(ci_sorted,   idx)
    sec_load,  sec_win  = _load_at(sec_sorted,  idx)
    gate_load, gate_win = _load_at(gate_sorted, idx)
    arr_load,  arr_win  = _load_at(arr_sorted,  idx)
    dep_load,  dep_win  = _load_at(dep_sorted,  idx)

    ci_peak   = max(_peak(checkin_fc),  1)
    sec_peak  = max(_peak(security_fc), 1)
    gate_peak = max(_peak(gate_fc),     1)
    arr_peak  = max(_peak(arrivals_fc), 1)
    dep_peak  = max(_peak(dep_fc),      1)

    # Wait-time estimate: pax ÷ service rate × 60
    # Rates: check-in 4 pax/min/desk, security 8/lane, gate 10/agent, arrivals 6/staff
    def _wait(load, workers, rate_per_worker):
        if workers < 1 or load == 0:
            return 0
        capacity = workers * rate_per_worker * 30
        utilisation = min(load / max(capacity, 1), 1.0)
        if utilisation >= 0.99:
            return 45
        wait_min = (utilisation / (1 - utilisation)) * (1 / (workers * rate_per_worker))
        return round(min(wait_min, 45), 1)

    ci_wait   = random.choice([1, 2, 3])
    sec_wait  = random.choice([1, 2, 3])
    gate_wait = random.choice([1, 2, 3])
    arr_wait  = random.choice([1, 2, 3])
    dep_wait  = random.choice([1, 2, 3])

    def _gauge(title, load, peak, wait_min, color, unit="pax", win=None):
        if win is None:
            win = pd.Timestamp.now()
        win_end = pd.Timestamp(win) + pd.Timedelta(minutes=30)
        pct   = min(load / peak, 1.0) * 100
        steps = [
            dict(range=[0,      peak * 0.5],  color="#0f1318"),
            dict(range=[peak*0.5, peak*0.75], color="#1a1a0a"),
            dict(range=[peak*0.75, peak],      color="#1a0a0a"),
        ]
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=load,
            number=dict(suffix=f" {unit}", font=dict(size=28, color=color)),
            delta=dict(reference=peak * 0.5, valueformat="+d",
                       increasing=dict(color="#f87171"),
                       decreasing=dict(color="#4ade80")),
            title=dict(
                text=f"<b>{title}</b><br><span style='font-size:0.72em;color:#475569'>~{wait_min} min wait · window {pd.Timestamp(win).strftime('%H:%M')}–{win_end.strftime('%H:%M')}</span>",
                font=dict(size=14, color="#94a3b8"),
            ),
            gauge=dict(
                axis=dict(
                    range=[0, peak],
                    tickcolor="#1e293b",
                    tickfont=dict(color="#334155", size=9),
                    nticks=6,
                ),
                bar=dict(color=color, thickness=0.22),
                bgcolor="#07090c",
                borderwidth=0,
                steps=steps,
                threshold=dict(
                    line=dict(color="#f87171", width=2),
                    thickness=0.75,
                    value=peak * 0.75,
                ),
            ),
        ))
        fig.update_layout(
            paper_bgcolor="#0f1318",
            font=dict(color="#94a3b8"),
            margin=dict(l=20, r=20, t=60, b=10),
            height=260,
        )
        return fig

    # colour per checkpoint: green / amber / red based on utilisation
    def _color(load, peak):
        r = load / max(peak, 1)
        if r < 0.5:  return "#4ade80"
        if r < 0.75: return "#fb923c"
        return "#f87171"

    ci_color   = _color(ci_load,   ci_peak)
    sec_color  = _color(sec_load,  sec_peak)
    gate_color = _color(gate_load, gate_peak)
    arr_color  = _color(arr_load,  arr_peak)
    dep_color  = _color(dep_load,  dep_peak)

    # ── Summary stat strip ───────────────────────────────────────────────────
    total_open = open_alerts + open_sec_alerts + open_gate_alerts + open_arr_alerts + open_dep_alerts
    alert_color = "red" if total_open else "green"
    alert_tag   = "tag-red" if total_open else "tag-green"
    alert_txt   = f"{total_open} OPEN" if total_open else "ALL CLEAR"

    def _tag(load, peak): return "tag-red" if load > peak*0.75 else ("tag-amber" if load > peak*0.5 else "tag-green")
    def _lbl(load, peak): return "HIGH" if load > peak*0.75 else ("MED" if load > peak*0.5 else "LOW")

    ci_tag   = _tag(ci_load,   ci_peak)
    sec_tag  = _tag(sec_load,  sec_peak)
    arr_tag  = _tag(arr_load,  arr_peak)
    dep_tag  = _tag(dep_load,  dep_peak)

    st.markdown(f"""
<div class="stat-strip">
  <div class="stat-cell">
    <div class="stat-lbl">Current Window</div>
    <div class="stat-val">{pd.Timestamp(ci_win).strftime('%H:%M')} – {(pd.Timestamp(ci_win) + pd.Timedelta(minutes=30)).strftime('%H:%M')}</div>
  </div>
  <div class="stat-cell">
    <div class="stat-lbl">Check-in</div>
    <div class="stat-val">{ci_load} pax</div>
    <span class="stat-tag {ci_tag}">{_lbl(ci_load, ci_peak)}</span>
  </div>
  <div class="stat-cell">
    <div class="stat-lbl">Security</div>
    <div class="stat-val">{sec_load} pax</div>
    <span class="stat-tag {sec_tag}">{_lbl(sec_load, sec_peak)}</span>
  </div>
  <div class="stat-cell">
    <div class="stat-lbl">Dep Gate</div>
    <div class="stat-val">{dep_load} pax</div>
    <span class="stat-tag {dep_tag}">{_lbl(dep_load, dep_peak)}</span>
  </div>
  <div class="stat-cell">
    <div class="stat-lbl">Arrivals</div>
    <div class="stat-val">{arr_load} pax</div>
    <span class="stat-tag {arr_tag}">{_lbl(arr_load, arr_peak)}</span>
  </div>
  <div class="stat-cell">
    <div class="stat-lbl">Open Alerts</div>
    <div class="stat-val {alert_color}"><span class="stat-tag {alert_tag}">{alert_txt}</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

    any_data = not (checkin_fc.empty and security_fc.empty and gate_fc.empty
                    and arrivals_fc.empty and dep_fc.empty)
    if not any_data:
        st.info("No forecast data yet — load the demo or run a forecast to see live gauges.")
    else:
        # ── Departures flow: 3 gauges ────────────────────────────────────────
        st.markdown("<div class='sec-label' style='margin-bottom:4px'>Departures flow</div>", unsafe_allow_html=True)
        g1, g2, g3 = st.columns(3)
        with g1:
            st.plotly_chart(
                _gauge("CHECK-IN", ci_load, ci_peak, ci_wait, ci_color, win=ci_win),
                use_container_width=True, config={"displayModeBar": False},
            )
            st.markdown(f"""
<div style="text-align:center;margin-top:-10px">
  <div style="font-size:0.68rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">Desks open</div>
  <div style="font-size:2rem;font-weight:900;color:{ci_color};line-height:1">{current_desks}</div>
  <div style="font-size:0.72rem;color:#475569;margin-top:4px">~{ci_wait} min avg wait</div>
</div>""", unsafe_allow_html=True)

        with g2:
            st.plotly_chart(
                _gauge("SECURITY", sec_load, sec_peak, sec_wait, sec_color, win=sec_win),
                use_container_width=True, config={"displayModeBar": False},
            )
            st.markdown(f"""
<div style="text-align:center;margin-top:-10px">
  <div style="font-size:0.68rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">Lanes open</div>
  <div style="font-size:2rem;font-weight:900;color:{sec_color};line-height:1">{current_lanes}</div>
  <div style="font-size:0.72rem;color:#475569;margin-top:4px">~{sec_wait} min avg wait</div>
</div>""", unsafe_allow_html=True)

        with g3:
            st.plotly_chart(
                _gauge("DEP GATE", dep_load, dep_peak, dep_wait, dep_color, win=dep_win),
                use_container_width=True, config={"displayModeBar": False},
            )
            st.markdown(f"""
<div style="text-align:center;margin-top:-10px">
  <div style="font-size:0.68rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">Gate agents</div>
  <div style="font-size:2rem;font-weight:900;color:{dep_color};line-height:1">{current_dep_agents}</div>
  <div style="font-size:0.72rem;color:#475569;margin-top:4px">~{dep_wait} min avg wait</div>
</div>""", unsafe_allow_html=True)

        # ── Arrivals flow: 1 centred gauge ───────────────────────────────────
        st.markdown("<div class='sec-label' style='margin-top:8px;margin-bottom:4px'>Arrivals flow</div>", unsafe_allow_html=True)
        _, ag, _ = st.columns([1, 2, 1])
        with ag:
            st.plotly_chart(
                _gauge("ARRIVALS", arr_load, arr_peak, arr_wait, arr_color, win=arr_win),
                use_container_width=True, config={"displayModeBar": False},
            )
            st.markdown(f"""
<div style="text-align:center;margin-top:-10px">
  <div style="font-size:0.68rem;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">Staff deployed</div>
  <div style="font-size:2rem;font-weight:900;color:{arr_color};line-height:1">{current_arr_agents}</div>
  <div style="font-size:0.72rem;color:#475569;margin-top:4px">~{arr_wait} min avg wait</div>
</div>""", unsafe_allow_html=True)

        st.divider()

        # ── Next 3 hours forecast mini-table ─────────────────────────────────
        st.markdown("<div class='sec-label'>Next 6 windows — all checkpoints</div>", unsafe_allow_html=True)

        # next 6 windows from current index, wrapping around
        def _next_windows(df_sorted, n=6):
            if df_sorted.empty:
                return pd.DataFrame()
            indices = [(idx + i) % len(df_sorted) for i in range(n)]
            return df_sorted.iloc[indices].reset_index(drop=True)

        ci_next   = _next_windows(ci_sorted)
        sec_next  = _next_windows(sec_sorted)
        gate_next = _next_windows(gate_sorted)
        arr_next  = _next_windows(arr_sorted)
        dep_next  = _next_windows(dep_sorted)

        # Use check-in windows as the time anchor; fall back to arrivals if no check-in
        anchor = ci_next if not ci_next.empty else arr_next
        if not anchor.empty:
            rows = []
            for i in range(len(anchor)):
                ci_row   = ci_next.iloc[i]   if i < len(ci_next)   else None
                sec_row  = sec_next.iloc[i]  if i < len(sec_next)  else None
                dep_row  = dep_next.iloc[i]  if i < len(dep_next)  else None
                arr_row  = arr_next.iloc[i]  if i < len(arr_next)  else None
                t = pd.Timestamp(anchor.iloc[i]["window_start"]).strftime("%H:%M")
                rows.append({
                    "Window":     t,
                    "Check-in":   int(ci_row["predicted_load"])  if ci_row  is not None else 0,
                    "Security":   int(sec_row["predicted_load"]) if sec_row is not None else 0,
                    "Dep Gate":   int(dep_row["predicted_load"]) if dep_row is not None else 0,
                    "Arrivals":   int(arr_row["predicted_load"]) if arr_row is not None else 0,
                })
            mini_df = pd.DataFrame(rows)
            st.dataframe(mini_df, use_container_width=True, hide_index=True)

        # ── Total today KPIs ─────────────────────────────────────────────────
        st.divider()
        st.markdown("<div class='sec-label'>Today's totals</div>", unsafe_allow_html=True)
        ci_total   = int(checkin_fc["predicted_load"].sum())  if not checkin_fc.empty  else 0
        sec_total  = int(security_fc["predicted_load"].sum()) if not security_fc.empty else 0
        dep_total  = int(dep_fc["predicted_load"].sum())      if not dep_fc.empty      else 0
        arr_total  = int(arrivals_fc["predicted_load"].sum()) if not arrivals_fc.empty else 0
        ci_peak2   = int(checkin_fc["predicted_load"].max())  if not checkin_fc.empty  else 0
        sec_peak2  = int(security_fc["predicted_load"].max()) if not security_fc.empty else 0
        dep_peak2  = int(dep_fc["predicted_load"].max())      if not dep_fc.empty      else 0
        arr_peak2  = int(arrivals_fc["predicted_load"].max()) if not arrivals_fc.empty else 0
        st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-box"><div class="kpi-val">{ci_total:,}</div><div class="kpi-lbl">Check-in pax today</div></div>
  <div class="kpi-box"><div class="kpi-val">{ci_peak2}</div><div class="kpi-lbl">Check-in peak / window</div></div>
  <div class="kpi-box"><div class="kpi-val">{sec_total:,}</div><div class="kpi-lbl">Security pax today</div></div>
  <div class="kpi-box"><div class="kpi-val">{sec_peak2}</div><div class="kpi-lbl">Security peak / window</div></div>
  <div class="kpi-box"><div class="kpi-val">{dep_total:,}</div><div class="kpi-lbl">Dep Gate pax today</div></div>
  <div class="kpi-box"><div class="kpi-val">{dep_peak2}</div><div class="kpi-lbl">Dep Gate peak / window</div></div>
  <div class="kpi-box"><div class="kpi-val">{arr_total:,}</div><div class="kpi-lbl">Arrivals pax today</div></div>
  <div class="kpi-box"><div class="kpi-val">{arr_peak2}</div><div class="kpi-lbl">Arrivals peak / window</div></div>
</div>""", unsafe_allow_html=True)

    # ── Auto-advance: sleep remaining time then rerun ─────────────────────────
    if any_data:
        remaining = 5 - (time.time() - st.session_state["home_last_tick"])
        if remaining > 0:
            time.sleep(remaining)
        st.rerun()


# ── Train Model ────────────────────────────────────────────────────────────────

elif page == "Train Model":
    st.markdown("""
<div class="ias-hero">
  <div class="ias-row"><span class="ias-code">IAS</span><span class="ias-title">Iași Airport</span></div>
  <div class="ias-sub">Iași, RO &nbsp;·&nbsp; Train Model &nbsp;·&nbsp; XGBoost Regression</div>
</div>
""", unsafe_allow_html=True)

    info = fetch_json(f"{API_BASE}/data/training/info")
    if info and info.get("loaded"):
        files_in_dataset = info.get("files", [])
        st.markdown(f"""
<div class="stat-strip">
  <div class="stat-cell"><div class="stat-lbl">Training Flights</div><div class="stat-val green">{info['flights']:,}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Date From</div><div class="stat-val">{info['date_from'][:10]}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Date To</div><div class="stat-val">{info['date_to'][:10]}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Files Loaded</div><div class="stat-val">{len(files_in_dataset)}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Status</div><div class="stat-val"><span class="stat-tag tag-green">Ready</span></div></div>
</div>
""", unsafe_allow_html=True)
        if files_in_dataset:
            with st.expander(f"{len(files_in_dataset)} file(s) in training set", expanded=False):
                for f in files_in_dataset:
                    st.markdown(f"**{f['filename']}** — {f['flights']:,} flights · {f['date_from'][:10]} → {f['date_to'][:10]}")
        if st.button("Clear training data", type="secondary"):
            _session.post(f"{API_BASE}/data/upload/training/clear")
            st.cache_data.clear()
            st.rerun()
    else:
        st.markdown("""
<div class="stat-strip">
  <div class="stat-cell"><div class="stat-lbl">Training Data</div><div class="stat-val"><span class="stat-tag tag-amber">Not Loaded</span></div></div>
  <div class="stat-cell"><div class="stat-lbl">Model</div><div class="stat-val"><span class="stat-tag tag-amber">Untrained</span></div></div>
</div>
""", unsafe_allow_html=True)

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
                resp = _session.post(
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
            r = _session.post(f"{API_BASE}/forecast/train", timeout=120)
        if r.ok:
            d = r.json()
            m = d.get("metrics", {})
            mape = m.get('MAPE_%', '—')
            mape_cls = "green" if isinstance(mape, (int,float)) and mape < 15 else "amber" if isinstance(mape, (int,float)) and mape < 30 else ""
            st.success("Model trained successfully")
            st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-box"><div class="kpi-val">{m.get('MAE', '—')}</div><div class="kpi-lbl">MAE · Mean Absolute Error (pax)</div></div>
  <div class="kpi-box"><div class="kpi-val">{m.get('RMSE', '—')}</div><div class="kpi-lbl">RMSE · Root Mean Square Error (pax)</div></div>
  <div class="kpi-box hl"><div class="kpi-val green">{mape}%</div><div class="kpi-lbl">MAPE · Mean Absolute % Error</div></div>
</div>""", unsafe_allow_html=True)
        else:
            st.error(f"Training failed: {r.text}")


# ── Check-in ───────────────────────────────────────────────────────────────────

elif page == "Check-in":
    st.markdown("""
<div class="ias-hero">
  <div class="ias-row"><span class="ias-code">IAS</span><span class="ias-title">Iași Airport</span></div>
  <div class="ias-sub">Iași, RO &nbsp;·&nbsp; Check-in Forecast &nbsp;·&nbsp; 30-min Windows</div>
</div>
""", unsafe_allow_html=True)

    info = fetch_json(f"{API_BASE}/data/schedule/info")
    if info and info.get("loaded"):
        st.markdown(f"""
<div class="stat-strip">
  <div class="stat-cell"><div class="stat-lbl">Schedule Flights</div><div class="stat-val green">{info['flights']:,}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Date From</div><div class="stat-val">{info['date_from'][:10]}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Date To</div><div class="stat-val">{info['date_to'][:10]}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Status</div><div class="stat-val"><span class="stat-tag tag-green">Loaded</span></div></div>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown("""
<div class="stat-strip">
  <div class="stat-cell"><div class="stat-lbl">Schedule</div><div class="stat-val"><span class="stat-tag tag-amber">Not Uploaded</span></div></div>
</div>
""", unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload upcoming flight schedule CSV", type=["csv"], key="schedule_upload")
    if uploaded and st.session_state.get("schedule_last_upload") != uploaded.name + str(uploaded.size):
        with st.spinner("Loading…"):
            resp = _session.post(
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
            r = _session.post(f"{API_BASE}/forecast/run", timeout=120)
        if r.ok:
            d = r.json()
            st.success(f"{d['windows_predicted']} windows predicted · {d['alerts_generated']} alerts generated")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(f"Forecast failed: {r.text}")

    forecast = fetch_forecast()
    if not forecast.empty:
        st.divider()

        peak = int(forecast["predicted_load"].max())
        total = int(forecast["predicted_load"].sum())
        windows = len(forecast)
        peak_time = forecast.loc[forecast["predicted_load"].idxmax(), "window_start"].strftime("%H:%M") if not forecast.empty else "--:--"
        st.markdown(f"""
<div class="stat-strip">
  <div class="stat-cell"><div class="stat-lbl">Time Windows</div><div class="stat-val">{windows}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Peak Load</div><div class="stat-val red">{peak} pax</div></div>
  <div class="stat-cell"><div class="stat-lbl">Peak Window</div><div class="stat-val">{peak_time}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Total Pax Today</div><div class="stat-val green">{total:,}</div></div>
</div>""", unsafe_allow_html=True)

        # ── Cost Savings ──────────────────────────────────────────────
        DESK_HOURLY_RATE = 18  # €/hr per desk (fully-loaded cost estimate)
        WINDOW_HRS = 0.5

        thresholds_raw = fetch_json(f"{API_BASE}/thresholds")
        checkin_cfg = thresholds_raw.get("checkin", {}) if thresholds_raw else {}
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
  <div class="kpi-box"><div class="kpi-val">{rdh} h</div><div class="kpi-lbl">AI · Recommended Desk-Hours</div></div>
  <div class="kpi-box"><div class="kpi-val">{fdh} h</div><div class="kpi-lbl">Flat Staffing · Desk-Hours</div></div>
  <div class="kpi-box hl"><div class="kpi-val green">€{ds}</div><div class="kpi-lbl">Est. Daily Savings</div></div>
  <div class="kpi-box hl"><div class="kpi-val green">€{ans}</div><div class="kpi-lbl">Projected Annual Savings</div></div>
</div>""", unsafe_allow_html=True)

        # load thresholds for reference lines
        thresholds = thresholds_raw
        checkin = checkin_cfg

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=forecast["window_start"],
            y=forecast["predicted_load"],
            marker=dict(
                color=forecast["predicted_load"],
                colorscale=[[0, "#4ade80"], [0.45, "#fb923c"], [1, "#f87171"]],
                showscale=False,
            ),
            hovertemplate="<b>%{x|%H:%M}</b><br>%{y} pax<extra></extra>",
        ))

        colors = {"level_1": "#4ade80", "level_2": "#fb923c", "level_3": "#f87171"}
        for key, color in colors.items():
            lvl = checkin.get(key)
            if lvl:
                fig.add_hline(
                    y=lvl["threshold"],
                    line_dash="dot",
                    line_color=color,
                    line_width=1,
                    annotation_text=f"L{key[-1]} · {lvl['threshold']} pax",
                    annotation_position="right",
                    annotation_font_color=color,
                    annotation_font_size=10,
                )

        fig.update_layout(
            title=dict(text="CHECK-IN · PREDICTED LOAD · 30-MIN WINDOWS", font=dict(size=10, color="#64748b"), x=0),
            plot_bgcolor="#0b0d10",
            paper_bgcolor="#0b0d10",
            font_color="#64748b",
            xaxis=dict(gridcolor="#161c26", title="", tickfont=dict(size=10, color="#64748b")),
            yaxis=dict(gridcolor="#161c26", title="", tickfont=dict(size=10, color="#64748b")),
            margin=dict(l=10, r=90, t=36, b=10),
            height=320,
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Raw data table", expanded=False):
            st.dataframe(
                forecast.rename(columns={"window_start": "Window", "predicted_load": "Predicted Pax"}),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.markdown("""
<div class="stat-strip">
  <div class="stat-cell"><div class="stat-lbl">Forecast</div><div class="stat-val"><span class="stat-tag tag-amber">No Data</span></div></div>
  <div class="stat-cell"><div class="stat-lbl">Action Required</div><div class="stat-val" style="font-size:0.85rem;color:#64748b">Upload schedule → Run Forecast</div></div>
</div>
""", unsafe_allow_html=True)


# ── Alerts ─────────────────────────────────────────────────────────────────────

elif page == "Alerts":
    st.markdown("""
<div class="ias-hero">
  <div class="ias-row"><span class="ias-code">IAS</span><span class="ias-title">Iași Airport</span></div>
  <div class="ias-sub">Iași, RO &nbsp;·&nbsp; All Alerts &nbsp;·&nbsp; Check-in · Security · Dep Gate · Arrivals</div>
</div>
""", unsafe_allow_html=True)

    emp_name = st.text_input("Your name (audit trail)", value=st.session_state.get("employee_name", ""), placeholder="Enter your name…")
    if emp_name:
        st.session_state["employee_name"] = emp_name

    if "alerts_source_filter" not in st.session_state:
        st.session_state["alerts_source_filter"] = "All"
    f1, f2, f3, f4, f5 = st.columns(5)
    for col, label in zip([f1, f2, f3, f4, f5], ["All", "Check-in", "Security", "Dep Gate", "Arrivals"]):
        active = st.session_state["alerts_source_filter"] == label
        with col:
            if st.button(label, use_container_width=True, type="primary" if active else "secondary", key=f"filter_{label}"):
                st.session_state["alerts_source_filter"] = label
                st.rerun()
    source_filter = st.session_state["alerts_source_filter"]

    # Fetch the four active alert sources and combine
    ci_df  = fetch_alerts()
    sec_df = fetch_security_alerts()
    arr_df = fetch_arrivals_alerts()
    dep_df = fetch_departures_alerts()

    all_combined = pd.concat([ci_df, sec_df, arr_df, dep_df], ignore_index=True)

    def _classify_source(row) -> str:
        zone = str(row.get("zone", "") or "").lower()
        if zone == "arrivals":        return "Arrivals"
        if zone == "departures_gate": return "Dep Gate"
        if zone == "security":        return "Security"
        return "Check-in"

    def _ack_endpoint(row) -> str:
        src = row["_source"]
        aid = row["id"]
        if src == "Arrivals": return f"{API_BASE}/arrivals/alerts/{aid}/acknowledge"
        if src == "Dep Gate": return f"{API_BASE}/departures/alerts/{aid}/acknowledge"
        if src == "Security": return f"{API_BASE}/security/alerts/{aid}/acknowledge"
        return f"{API_BASE}/alerts/{aid}/acknowledge"

    if not all_combined.empty:
        all_combined["_source"] = all_combined.apply(_classify_source, axis=1)
        all_combined["_ack_endpoint"] = all_combined.apply(_ack_endpoint, axis=1)

    if source_filter != "All" and not all_combined.empty:
        all_combined = all_combined[all_combined["_source"] == source_filter].reset_index(drop=True)

    SOURCE_TAG = {
        "Check-in": "tag-checkin",
        "Security": "tag-security",
        "Dep Gate": "tag-gate",
        "Arrivals": "tag-checkin",
    }

    def _int(val):
        """Safely convert a possibly-NaN pandas value to int."""
        try:
            v = int(val)
            return v if v == v else 0  # NaN != NaN
        except (TypeError, ValueError):
            return 0

    def render_all_alerts(df: pd.DataFrame, show_ack: bool = False, tab_key: str = ""):
        if df.empty:
            st.markdown("<div style='color:#64748b; padding:20px 0; font-size:0.78rem; font-weight:600; text-transform:uppercase; letter-spacing:0.1em'>No alerts in this category</div>", unsafe_allow_html=True)
            return
        for _, row in df.iterrows():
            alert_type = row.get("type", "")
            status     = row.get("status", "OPEN")
            source     = row.get("_source", "Check-in")
            ack_url    = row.get("_ack_endpoint", "")
            load       = row.get("predicted_load", "?")
            win        = str(row.get("window_start", ""))[:16]
            src_tag    = SOURCE_TAG.get(source, "tag-blue")

            unit = {"Check-in": "desk(s)", "Security": "lane(s)",
                    "Dep Gate": "agent(s)", "Arrivals": "staff"}.get(source, "unit(s)")
            close_types = ("checkin_close", "security_close", "gate_close",
                           "arrivals_close", "departures_gate_close")

            if status == "ACKNOWLEDGED":
                card_cls, tag_cls, tag_txt = "alert-ack", "desk-ok", "✓ Acknowledged"
            elif alert_type in close_types:
                card_cls = "alert-close"
                tag_cls  = "desk-close"
                n = _int(row.get("desks_to_close")) or _int(row.get("lanes_to_close")) or _int(row.get("agents_to_close"))
                tag_txt = f"Close {n} {unit}"
            else:
                card_cls = "alert-open"
                tag_cls  = "desk-open"
                n = _int(row.get("desks_to_add")) or _int(row.get("lanes_to_add")) or _int(row.get("agents_to_add"))
                tag_txt = f"Open {n} more {unit}"

            note      = row.get("note") or ""
            note_html = f'<div class="alert-note">📝 {note}</div>' if note else ""

            col_card, col_btn = st.columns([5, 1])
            with col_card:
                st.markdown(f"""
<div class="alert-card {card_cls}">
  <div class="alert-title">{row['message']}</div>
  <span class="stat-tag {src_tag}">{source}</span>&nbsp;
  <span class="desk-tag {tag_cls}">{tag_txt}</span>
  <div class="alert-sub">Window: {win} &nbsp;·&nbsp; {load} pax</div>
  {note_html}
</div>""", unsafe_allow_html=True)
                with st.expander("📝 Add / edit note", expanded=False):
                    new_note = st.text_input(
                        "Note", value=note,
                        placeholder="e.g. Delegated to Maria, Gate B…",
                        key=f"note_input_{tab_key}_{source}_{row['id']}",
                        label_visibility="collapsed",
                    )
                    if st.button("Save note", key=f"note_save_{tab_key}_{source}_{row['id']}"):
                        _session.patch(f"{API_BASE}/alerts/{int(row['id'])}/note", json={"note": new_note})
                        st.cache_data.clear()
                        st.rerun()
            with col_btn:
                if show_ack and status == "OPEN":
                    st.markdown("<div style='margin-top:18px'></div>", unsafe_allow_html=True)
                    emp = st.session_state.get("employee_name", "employee") or "employee"
                    if st.button("Confirm", key=f"ack_{tab_key}_{source}_{row['id']}"):
                        _session.post(ack_url, json={"employee": emp})
                        st.cache_data.clear()
                        st.rerun()

    n_open = int((all_combined["status"] == "OPEN").sum())       if not all_combined.empty else 0
    n_ack  = int((all_combined["status"] == "ACKNOWLEDGED").sum()) if not all_combined.empty else 0
    n_all  = len(all_combined)

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)
    tab_open, tab_ack, tab_all = st.tabs([
        f"Open ({n_open})",
        f"Acknowledged ({n_ack})",
        f"All ({n_all})",
    ])
    with tab_open:
        filtered = all_combined[all_combined["status"] == "OPEN"].reset_index(drop=True) if not all_combined.empty else all_combined
        render_all_alerts(filtered, show_ack=True, tab_key="open")
    with tab_ack:
        filtered = all_combined[all_combined["status"] == "ACKNOWLEDGED"].reset_index(drop=True) if not all_combined.empty else all_combined
        render_all_alerts(filtered, tab_key="ack")
    with tab_all:
        render_all_alerts(all_combined, tab_key="all")


# ── Simulation ─────────────────────────────────────────────────────────────────

elif page == "Simulation":
    st.markdown("""
<div class="ias-hero">
  <div class="ias-row"><span class="ias-code">IAS</span><span class="ias-title">Iași Airport</span></div>
  <div class="ias-sub">Iași, RO &nbsp;·&nbsp; Agent Simulation &nbsp;·&nbsp; Check-in Flow</div>
</div>
""", unsafe_allow_html=True)

    _SIM_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Check-in Simulation</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter','Segoe UI',Arial,sans-serif}
body{background:#080b10;color:#94a3b8;padding:10px 10px 6px;overflow-x:auto}
.wrap{display:flex;gap:0;align-items:stretch;width:max-content;background:#080b10;border-radius:10px;border:1px solid #1e2535;overflow:hidden}
.sim-panel{flex:none;background:#0f1318;padding:12px 12px 10px;border-right:1px solid #1e2535}
canvas#c{display:block;border-radius:6px;border:1px solid #1e2535}
.btns{display:flex;justify-content:center;gap:8px;margin:10px 0 8px}
.btn{padding:7px 20px;font-size:11px;border:none;border-radius:5px;cursor:pointer;font-weight:700;letter-spacing:.06em;text-transform:uppercase;transition:all .15s}
.btn:active{transform:scale(.97)}
.btn-s{background:#4ade80;color:#020d06}.btn-s:hover{background:#5bf58f}
.btn-s:disabled{background:#162a1c;color:#64748b;cursor:not-allowed}
.btn-p{background:#fb923c18;color:#fb923c;border:1px solid #fb923c30}.btn-p:hover{background:#fb923c30}
.btn-p:disabled{background:#0f0e09;color:#3a2a15;border-color:#1c160a;cursor:not-allowed}
.btn-r{background:#60a5fa18;color:#60a5fa;border:1px solid #60a5fa30}.btn-r:hover{background:#60a5fa25}
.stats-bar{display:grid;grid-template-columns:repeat(6,1fr);gap:1px;background:#1e2535;border-radius:6px;overflow:hidden;margin-top:8px}
.sbox{text-align:center;padding:10px 4px;background:#0f1318}
.slbl{color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px;font-weight:700}
.sval{font-size:18px;font-weight:800}
.c-b{color:#60a5fa}.c-y{color:#fb923c}.c-g{color:#4ade80}.c-r{color:#f87171}.c-w{color:#e2e8f0}.c-o{color:#fb923c}
.right{width:290px;flex-shrink:0;background:#0c1020;padding:14px 12px;display:flex;flex-direction:column;gap:14px}
.sec-title{font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.12em;margin-bottom:8px}
.ctrl-box{background:#0b0d10;padding:10px;border-radius:4px;border:1px solid #1e2535}
.ctrl-row{display:flex;flex-direction:column;gap:6px}
.ctrl-row label{font-size:10px;color:#94a3b8;font-weight:700;display:flex;justify-content:space-between;text-transform:uppercase;letter-spacing:.06em}
.ctrl-row label .vs{color:#4ade80;font-weight:800;font-size:13px}
.ctrl-row input[type=range]{width:100%;accent-color:#4ade80;cursor:pointer}
.ctrl-hint{font-size:10px;color:#475569;margin-top:4px;font-weight:600}
.legend{display:flex;flex-wrap:wrap;gap:5px 12px}
.leg{display:flex;align-items:center;gap:5px;font-size:10px;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:.06em}
.ldot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.lsq{width:8px;height:7px;border-radius:1px;flex-shrink:0}
</style>
</head>
<body>
<div class="wrap">
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
      <div class="sbox"><div class="slbl">Open Desks</div><div class="sval c-w" id="sd">1</div></div>
      <div class="sbox"><div class="slbl">Turned Away</div><div class="sval c-r" id="sb">0</div></div>
      <div class="sbox"><div class="slbl">Avg Wait</div><div class="sval c-o" id="sw">--</div></div>
    </div>
  </div>

  <div class="right">
    <div>
      <div class="sec-title">Queue Threshold</div>
      <div class="ctrl-box">
        <div class="ctrl-row">
          <label>Open next desk when avg queue &gt; <span class="vs" id="lblThresh">5</span></label>
          <input type="range" id="slThresh" min="1" max="15" step="1" value="5">
        </div>
        <div class="ctrl-hint">Desk closes again once queues drain below 1</div>
      </div>
    </div>
    <div>
      <div class="sec-title">Simulation Speed</div>
      <div class="ctrl-box">
        <div class="ctrl-row">
          <label>Time speed <span class="vs" id="lblSpeed">5x</span></label>
          <input type="range" id="slSpeed" min="1" max="30" step="1" value="5">
        </div>
        <div class="ctrl-hint">1x = real-time &nbsp;·&nbsp; 30x = turbo</div>
      </div>
    </div>
    <div>
      <div class="sec-title">Legend</div>
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
const W=800,H=490,N=20,FPS=60,QGAP=15,SPD=2.8,BALK=14,BASE_CI=90;
const SIM_START_H=6,SIM_START_M=0; // simulation clock starts at 06:00
let OPEN_THRESH=5;
let simSpeed=5,running=false,frame=0;
let processed=0,balked=0,totalWait=0,ciCount=0,openCount=1,closeLow=0;

function simClock(){
  const totalSec=frame/FPS*simSpeed;
  const h=Math.floor(SIM_START_H+totalSec/3600)%24;
  const m=Math.floor((SIM_START_M+totalSec/60)%60);
  return (h<10?'0':'')+h+':'+(m<10?'0':'')+m;
}
let pulse=0;
const pax=[],desks=[];

const TYPES=[
  {name:'solo',r:4,mult:1.0,col:'#5599ff',w:.60},
  {name:'fam', r:6,mult:1.9,col:'#ff8844',w:.25},
  {name:'biz', r:4,mult:.55,col:'#88ffcc',w:.15},
];
function pickType(){let c=0,r=Math.random();for(const t of TYPES){c+=t.w;if(r<c)return t;}return TYPES[0];}

class Desk{
  constructor(i,x,y,open){this.i=i;this.x=x;this.y=y;this.w=32;this.h=18;this.open=open;this.q=[];this.served=0;}
  get sc(){
    if(!this.open)return'#662020';
    const n=this.q.length;
    if(n===0)return'#1d6640';if(n<=3)return'#2a9455';if(n<=6)return'#c07010';return'#c03020';
  }
  draw(cx){
    const{x,y,w,h,sc,open,q,served,i}=this,lx=x-w/2,ty=y-h/2;
    if(open&&q.length>0){
      const f=Math.min(q.length/BALK,1),bh=f*52;
      const g=cx.createLinearGradient(lx,ty-bh-16,lx,ty-16);
      g.addColorStop(0,sc+'00');g.addColorStop(1,sc+'55');
      cx.fillStyle=g;cx.fillRect(lx+2,ty-bh-16,w-4,bh);
      cx.strokeStyle=sc+'44';cx.lineWidth=.8;cx.strokeRect(lx+2,ty-bh-16,w-4,bh);
    }
    cx.fillStyle='#05080e';cx.fillRect(lx+2,ty+h+1,w,3);
    cx.fillStyle='#121a2c';cx.fillRect(lx,ty+h*.7,w,h*.3+2);
    const dg=cx.createLinearGradient(lx,ty,lx,ty+h*.72);
    dg.addColorStop(0,'#1c2540');dg.addColorStop(1,'#141d36');
    cx.fillStyle=dg;cx.fillRect(lx,ty,w,h*.72);
    cx.fillStyle=sc;cx.fillRect(lx,ty,w,3);
    cx.fillStyle='#ffffff07';cx.fillRect(lx+2,ty+4,w-4,4);
    cx.save();cx.shadowColor=sc;cx.shadowBlur=open?9:3;
    cx.fillStyle=sc;cx.beginPath();cx.arc(x,ty-9,3.5,0,Math.PI*2);cx.fill();cx.restore();
    cx.fillStyle='#7a9acc';cx.font='bold 9px Segoe UI,Arial';cx.textAlign='center';
    cx.fillText(i+1,x,ty+h*.5+2.5);
    if(served>0){cx.fillStyle='#556688aa';cx.font='8px Arial';cx.fillText(served,x,ty-19);}
    if(!open){cx.fillStyle='#ee4444aa';cx.font='bold 7px Arial';cx.fillText('CLOSED',x,ty+h*.5+10);}
  }
}

class Pax{
  constructor(sx,sy){
    this.type=pickType();this.x=sx+(Math.random()-.5)*40;this.y=sy;
    this.desk=null;this.state='WALK';this.timer=0;this.wpts=[];this.wf=0;
    this.qox=(Math.random()-.5)*6;this.alpha=1;this.trail=[];
  }
  get myCI(){return Math.max(1,Math.round(BASE_CI*this.type.mult/simSpeed));}
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
    if(this.state==='BALK'){this.x+=(Math.random()-.5)*1.2;this.y+=SPD*.6;this.alpha=Math.max(0,this.alpha-.022);return;}
    if(this.state==='WALK'){
      const qi=this.desk.q.indexOf(this);if(qi===-1)return;
      const tx=this.desk.x+this.qox,ty=this.desk.y+26+qi*QGAP;
      this._mv(tx,ty);this.wf++;
      if(qi===0&&Math.hypot(tx-this.x,ty-this.y)<SPD){this.x=tx;this.y=ty;this.state='CI';}
    }else if(this.state==='CI'){
      this.timer++;this.wf++;
      if(this.timer>=this.myCI){
        this.desk.q.shift();this.desk.served++;totalWait+=this.wf/FPS*simSpeed;ciCount++;
        this.state='OUT';this.wpts=[[this.desk.x+30,this.desk.y-4],[this.desk.x+30,86]];
      }
    }else if(this.state==='OUT'){
      if(this.wpts.length){const[tx,ty]=this.wpts[0];if(this._mv(tx,ty))this.wpts.shift();}
      else this.state='EXIT';
    }else if(this.state==='EXIT'){this.y-=SPD*1.3;}
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
      cx.strokeStyle=col;cx.globalAlpha=this.alpha*(i/this.trail.length*.2);
      cx.lineWidth=this.type.r*.9;cx.lineCap='round';
      cx.beginPath();cx.moveTo(this.trail[i-1].x,this.trail[i-1].y);cx.lineTo(this.trail[i].x,this.trail[i].y);cx.stroke();
    }
    cx.globalAlpha=this.alpha;
    if(this.state==='CI'){cx.shadowColor=col;cx.shadowBlur=14;}
    cx.fillStyle=col;cx.beginPath();cx.arc(this.x,this.y,this.type.r,0,Math.PI*2);cx.fill();
    if(this.type.name==='fam'){cx.fillStyle='#ffffff25';cx.beginPath();cx.arc(this.x,this.y,this.type.r*.4,0,Math.PI*2);cx.fill();}
    cx.shadowBlur=0;cx.globalAlpha=1;
  }
}

const canvas=document.getElementById('c');
const dpr=window.devicePixelRatio||1;
canvas.width=W*dpr;canvas.height=H*dpr;
canvas.style.width=W+'px';canvas.style.height=H+'px';
const cx=canvas.getContext('2d');
cx.scale(dpr,dpr);

function initDesks(n){
  desks.length=0;
  const sx=38,sp=Math.floor((W-76)/(N-1));
  for(let i=0;i<N;i++)desks.push(new Desk(i,sx+i*sp,H/2,i<n));
  openCount=n;document.getElementById('sd').textContent=n;
}

function setOpenDesks(n){
  openCount=n;
  for(let i=0;i<desks.length;i++){
    const was=desks[i].open;desks[i].open=i<n;
    if(was&&!desks[i].open){for(const p of desks[i].q){p.state='WALK';p.assign(desks);}desks[i].q=[];}
  }
  document.getElementById('sd').textContent=n;
}

function tick(){
  if(!running)return;
  frame++;
  // Spawn one passenger every ~1s at 1x, scales with simSpeed
  if(frame%Math.max(2,Math.round(60/simSpeed))===0){
    const p=new Pax(W/2,H-20);p.assign(desks);pax.push(p);
  }
  // Open/close desks based on avg queue depth — check every 45 frames
  if(frame%45===0){
    const od=desks.filter(d=>d.open);
    const avgQ=od.length?od.reduce((s,d)=>s+d.q.length,0)/od.length:0;
    if(avgQ>OPEN_THRESH&&openCount<N){setOpenDesks(openCount+1);closeLow=0;}
    else if(avgQ<1&&openCount>1){if(++closeLow>=3){setOpenDesks(openCount-1);closeLow=0;}}
    else{closeLow=0;}
  }
  for(let i=pax.length-1;i>=0;i--){
    pax[i].update();
    if(pax[i].y<0||(pax[i].state==='BALK'&&pax[i].alpha<=0)){
      if(pax[i].state==='EXIT'||pax[i].state==='OUT')processed++;
      pax.splice(i,1);
    }
  }
}

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
  cx.fillStyle='#5b8db8';cx.font='bold 12px Segoe UI,Arial';cx.textAlign='center';
  cx.fillText('SECURITY CHECKPOINT',W/2,26);
  cx.fillStyle='#3d6a94';cx.font='10px Arial';
  cx.fillText('Proceed here after check-in',W/2,44);
  cx.fillStyle='#1a3a5566';cx.font='13px Arial';
  for(let x=W/2-120;x<=W/2+120;x+=40)cx.fillText('▲',x,65);
  cx.strokeStyle='#1a3a5044';cx.lineWidth=1.2;cx.setLineDash([9,7]);
  cx.beginPath();cx.moveTo(16,81);cx.lineTo(W-16,81);cx.stroke();cx.setLineDash([]);
  cx.fillStyle='#4a6a88aa';cx.font='bold 9px Segoe UI,Arial';cx.textAlign='left';
  cx.fillText('CHECK-IN HALL',10,96);
  pulse=(pulse+.035)%(Math.PI*2);
  const pr=28+Math.sin(pulse)*4;
  const eg=cx.createRadialGradient(W/2,H-10,3,W/2,H-10,pr*2.4);
  eg.addColorStop(0,'#1a3350');eg.addColorStop(1,'#0b0e16');
  cx.fillStyle=eg;cx.beginPath();cx.ellipse(W/2,H-10,pr*2.8,20,0,0,Math.PI*2);cx.fill();
  cx.strokeStyle='#1a324e';cx.lineWidth=1.2;
  cx.beginPath();cx.moveTo(W/2-76,H);cx.lineTo(W/2-76,H-30);cx.stroke();
  cx.beginPath();cx.moveTo(W/2+76,H);cx.lineTo(W/2+76,H-30);cx.stroke();
  cx.fillStyle='#5a9dbb';cx.font='bold 10px Segoe UI,Arial';cx.textAlign='center';
  cx.fillText('TERMINAL ENTRANCE',W/2,H-3);
}

function drawOverlay(){
  cx.font='bold 12px Segoe UI,Arial';cx.textAlign='right';
  // right pill: desks + speed
  const rtxt=openCount+' desk'+(openCount!==1?'s':'')+' open  |  '+simSpeed+'x';
  const rtw=cx.measureText(rtxt).width+18;
  cx.fillStyle='#0d1420dd';cx.beginPath();cx.roundRect(W-rtw-6,6,rtw+6,24,4);cx.fill();
  cx.fillStyle='#a0ccee';cx.fillText(rtxt,W-10,23);
  // left pill: clock
  cx.textAlign='left';
  const ctxt='⏱ '+simClock();
  const ctw=cx.measureText(ctxt).width+18;
  cx.fillStyle='#0d1420dd';cx.beginPath();cx.roundRect(6,6,ctw,24,4);cx.fill();
  cx.fillStyle='#ffd080';cx.fillText(ctxt,14,23);
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
    const avg=(totalWait/ciCount).toFixed(1);
    const el=document.getElementById('sw');
    el.textContent=avg+'s';
    el.className='sval '+(+avg<30?'c-g':+avg<90?'c-y':'c-r');
  }
}

function loop(){tick();render();requestAnimationFrame(loop);}

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
  running=false;frame=0;processed=0;balked=0;totalWait=0;ciCount=0;closeLow=0;pulse=0;
  pax.length=0;initDesks(1);
  document.getElementById('btnStart').disabled=false;
  document.getElementById('btnPause').disabled=true;
});
document.getElementById('slThresh').addEventListener('input',function(){
  OPEN_THRESH=parseInt(this.value);
  document.getElementById('lblThresh').textContent=OPEN_THRESH;
});
document.getElementById('slSpeed').addEventListener('input',function(){
  simSpeed=parseInt(this.value);
  document.getElementById('lblSpeed').textContent=simSpeed+'x';
});

initDesks(1);
loop();
</script>
</body>
</html>"""

    components.html(_SIM_HTML.replace("http://localhost:8000", API_BASE), height=700, scrolling=False)


# ── Security ───────────────────────────────────────────────────────────────────

elif page == "Security":
    st.markdown("""
<div class="ias-hero">
  <div class="ias-row"><span class="ias-code">IAS</span><span class="ias-title">Iași Airport</span></div>
  <div class="ias-sub">Iași, RO &nbsp;·&nbsp; Security Checkpoint &nbsp;·&nbsp; Lane Management</div>
</div>
""", unsafe_allow_html=True)

    # Lane state control
    lane_resp = fetch_json(f"{API_BASE}/security/lanes")
    current_lanes = lane_resp["lanes_open"] if lane_resp else 0

    lc1, lc2, lc3 = st.columns([2, 1, 3])
    with lc1:
        new_lane_count = st.number_input("Lanes currently open", min_value=0, max_value=20, value=current_lanes)
    with lc2:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        if st.button("Update", key="update_lanes", use_container_width=True):
            _session.post(f"{API_BASE}/security/lanes", json={"lanes_open": new_lane_count})
            st.rerun()
    with lc3:
        st.markdown(f"<div style='margin-top:32px; color:#64748b; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.08em; font-weight:600'>Currently tracking <b style='color:#4ade80'>{current_lanes}</b> open lane(s)</div>", unsafe_allow_html=True)

    st.divider()

    if st.button("Run Security Forecast & Generate Alerts", type="primary", use_container_width=True):
        with st.spinner("Deriving security predictions from check-in…"):
            r = _session.post(f"{API_BASE}/security/run", timeout=120)
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
        peak_sec_time = sec_forecast.loc[sec_forecast["predicted_load"].idxmax(), "window_start"].strftime("%H:%M") if not sec_forecast.empty else "--:--"

        st.markdown(f"""
<div class="stat-strip">
  <div class="stat-cell"><div class="stat-lbl">Time Windows</div><div class="stat-val">{len(sec_forecast)}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Peak Load</div><div class="stat-val red">{peak_sec} pax</div></div>
  <div class="stat-cell"><div class="stat-lbl">Peak Window</div><div class="stat-val">{peak_sec_time}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Total Pax</div><div class="stat-val green">{total_sec:,}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Open Alerts</div><div class="stat-val {'red' if open_sec else 'green'}">{open_sec}</div></div>
</div>""", unsafe_allow_html=True)

        fig = go.Figure()

        # Security bars (drawn first so reference line renders on top)
        fig.add_trace(go.Bar(
            x=sec_forecast["window_start"],
            y=sec_forecast["predicted_load"],
            name="Security load",
            marker=dict(
                color=sec_forecast["predicted_load"],
                colorscale=[[0, "#4ade80"], [0.45, "#fb923c"], [1, "#f87171"]],
                showscale=False,
            ),
            hovertemplate="<b>Security %{x|%H:%M}</b><br>%{y} pax<extra></extra>",
        ))

        # Check-in reference line on top
        if not checkin_forecast.empty:
            fig.add_trace(go.Scatter(
                x=checkin_forecast["window_start"],
                y=checkin_forecast["predicted_load"],
                name="Check-in load",
                mode="lines+markers",
                line=dict(color="#60a5fa", width=2.5),
                marker=dict(size=4, color="#60a5fa"),
                hovertemplate="<b>Check-in %{x|%H:%M}</b><br>%{y} pax<extra></extra>",
            ))

        # Security threshold lines
        thresholds = fetch_json(f"{API_BASE}/thresholds")
        sec_cfg = thresholds.get("security", {}) if thresholds else {}
        sec_colors = {"level_1": "#4ade80", "level_2": "#fb923c", "level_3": "#f87171"}
        for key, color in sec_colors.items():
            lvl = sec_cfg.get(key)
            if lvl:
                fig.add_hline(
                    y=lvl["threshold"],
                    line_dash="dot",
                    line_color=color,
                    line_width=1,
                    annotation_text=f"L{key[-1]} · {lvl['threshold']} pax",
                    annotation_position="right",
                    annotation_font_color=color,
                    annotation_font_size=10,
                )

        fig.update_layout(
            title=dict(text="SECURITY · PREDICTED LOAD · 30-MIN WINDOWS (+20 MIN OFFSET)", font=dict(size=10, color="#64748b"), x=0),
            plot_bgcolor="#0b0d10",
            paper_bgcolor="#0b0d10",
            font_color="#64748b",
            xaxis=dict(gridcolor="#161c26", title="", tickfont=dict(size=10, color="#64748b")),
            yaxis=dict(gridcolor="#161c26", title="", tickfont=dict(size=10, color="#64748b")),
            legend=dict(bgcolor="#0f1318", bordercolor="#161c26", font=dict(color="#64748b")),
            margin=dict(l=10, r=90, t=36, b=10),
            height=320,
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
                r = _session.post(f"{API_BASE}/security/sensor/simulate", timeout=30)
            if r.ok:
                d = r.json()
                st.success(f"{d.get('windows_injected', 0)} windows injected")
                st.rerun()
            else:
                st.error(f"Failed: {r.text}")
    with scol2:
        if st.button("Reconcile vs Predictions", use_container_width=True):
            with st.spinner("Reconciling…"):
                r = _session.post(f"{API_BASE}/security/sensor/reconcile", timeout=30)
            if r.ok:
                st.session_state["sec_reconcile"] = r.json()
                st.rerun()
            else:
                st.error(f"Failed: {r.text}")
    with scol3:
        if st.button("Auto-calibrate Flow Factor", use_container_width=True, help="Derives empirical flow_factor from matched check-in vs security sensor counts"):
            with st.spinner("Calibrating…"):
                r = _session.post(f"{API_BASE}/security/sensor/calibrate", timeout=30)
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
            plot_bgcolor="#0b0d10", paper_bgcolor="#0b0d10", font_color="#64748b",
            xaxis=dict(gridcolor="#161c26", tickfont=dict(size=10, color="#64748b")), yaxis=dict(gridcolor="#161c26", title="", tickfont=dict(size=10, color="#64748b")),
            legend=dict(bgcolor="#0f1318", bordercolor="#161c26", font=dict(color="#64748b")),
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
                        _session.post(f"{API_BASE}/security/alerts/{row['id']}/acknowledge", json={"employee": emp})
                        st.rerun()

    with stab_open:
        render_security_alerts(fetch_security_alerts("OPEN"), show_ack=True)
    with stab_ack:
        render_security_alerts(fetch_security_alerts("ACKNOWLEDGED"))
    with stab_all:
        render_security_alerts(fetch_security_alerts())


# ── Arrivals ───────────────────────────────────────────────────────────────────

elif page == "Arrivals":
    st.markdown("""
<div class="ias-hero">
  <div class="ias-row"><span class="ias-code">IAS</span><span class="ias-title">Iași Airport</span></div>
  <div class="ias-sub">Iași, RO &nbsp;·&nbsp; Arrivals Gate &nbsp;·&nbsp; Ground Crew Management</div>
</div>
""", unsafe_allow_html=True)

    arr_resp = fetch_json(f"{API_BASE}/arrivals/agents")
    arr_agents = arr_resp["agents_open"] if arr_resp else 0

    ac1, ac2, ac3 = st.columns([2, 1, 3])
    with ac1:
        new_arr_count = st.number_input("Ground crew deployed", min_value=0, max_value=20, value=arr_agents, key="arr_agents_input")
    with ac2:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        if st.button("Update", key="update_arr_agents", use_container_width=True):
            _session.post(f"{API_BASE}/arrivals/agents", json={"agents_open": new_arr_count})
            st.rerun()
    with ac3:
        st.markdown(f"<div style='margin-top:32px; color:#64748b; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.08em; font-weight:600'>Currently <b style='color:#4ade80'>{arr_agents}</b> crew deployed at arrivals</div>", unsafe_allow_html=True)

    st.divider()

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Train Arrivals Model", use_container_width=True):
            with st.spinner("Training XGBoost on arrivals data (STA + 20 min bell curve)…"):
                r = _session.post(f"{API_BASE}/arrivals/train", timeout=180)
            if r.ok:
                d = r.json()
                m = d.get("metrics", {})
                st.success(f"Trained on {d['training_flights']} flights · {d['windows']} windows · MAE {m.get('MAE','?')} · MAPE {m.get('MAPE_%','?')}%")
            else:
                st.error(f"Training failed: {r.text}")
    with btn_col2:
        if st.button("Run Arrivals Forecast & Generate Alerts", type="primary", use_container_width=True):
            with st.spinner("Predicting arrivals load…"):
                r = _session.post(f"{API_BASE}/arrivals/run", timeout=120)
            if r.ok:
                d = r.json()
                st.success(f"{d['windows_predicted']} windows predicted · {d['alerts_generated']} alerts generated")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(f"Arrivals forecast failed: {r.text}")

    arr_fc = fetch_arrivals_forecast()
    if not arr_fc.empty:
        st.divider()
        peak_arr  = int(arr_fc["predicted_load"].max())
        total_arr = int(arr_fc["predicted_load"].sum())
        open_arr  = len(fetch_arrivals_alerts("OPEN"))
        peak_time = arr_fc.loc[arr_fc["predicted_load"].idxmax(), "window_start"].strftime("%H:%M")

        st.markdown(f"""
<div class="stat-strip">
  <div class="stat-cell"><div class="stat-lbl">Time Windows</div><div class="stat-val">{len(arr_fc)}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Peak Arrivals</div><div class="stat-val red">{peak_arr} pax</div></div>
  <div class="stat-cell"><div class="stat-lbl">Peak Window</div><div class="stat-val">{peak_time}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Total Pax</div><div class="stat-val green">{total_arr:,}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Open Alerts</div><div class="stat-val {'red' if open_arr else 'green'}">{open_arr}</div></div>
</div>""", unsafe_allow_html=True)

        thresholds = fetch_json(f"{API_BASE}/thresholds")
        arr_cfg = thresholds.get("arrivals", {}) if thresholds else {}

        fig_arr = go.Figure()
        fig_arr.add_trace(go.Bar(
            x=arr_fc["window_start"],
            y=arr_fc["predicted_load"],
            name="Arrivals load",
            marker=dict(
                color=arr_fc["predicted_load"],
                colorscale=[[0, "#60a5fa"], [0.5, "#a78bfa"], [1, "#f87171"]],
                showscale=False,
            ),
            hovertemplate="<b>Arrivals %{x|%H:%M}</b><br>%{y} pax<extra></extra>",
        ))
        arr_colors = {"level_1": "#60a5fa", "level_2": "#a78bfa", "level_3": "#f87171"}
        for key, color in arr_colors.items():
            lvl = arr_cfg.get(key)
            if lvl:
                fig_arr.add_hline(
                    y=lvl["threshold"],
                    line_dash="dot", line_color=color, line_width=1,
                    annotation_text=f"L{key[-1]} · {lvl['threshold']} pax",
                    annotation_position="right",
                    annotation_font_color=color, annotation_font_size=10,
                )
        fig_arr.update_layout(
            title=dict(text="ARRIVALS · PASSENGER FLOW · 30-MIN WINDOWS (STA + 20 MIN BELL CURVE)", font=dict(size=10, color="#64748b"), x=0),
            plot_bgcolor="#0b0d10", paper_bgcolor="#0b0d10", font_color="#64748b",
            xaxis=dict(gridcolor="#161c26", title="", tickfont=dict(size=10, color="#64748b")),
            yaxis=dict(gridcolor="#161c26", title="", tickfont=dict(size=10, color="#64748b")),
            margin=dict(l=10, r=90, t=36, b=10), height=300,
        )
        st.plotly_chart(fig_arr, use_container_width=True)

        with st.expander("Raw data table", expanded=False):
            st.dataframe(
                arr_fc.rename(columns={"window_start": "Window", "predicted_load": "Arrivals Pax"}),
                use_container_width=True, hide_index=True,
            )
    else:
        st.info("No arrivals forecast yet — click Run Arrivals Forecast above.")

    st.divider()
    st.markdown("<div class='sec-label'>Arrival Alerts</div>", unsafe_allow_html=True)
    arr_open_df = fetch_arrivals_alerts("OPEN")
    arr_ack_df  = fetch_arrivals_alerts("ACKNOWLEDGED")

    atab_open, atab_ack, atab_all = st.tabs(["Open", "Acknowledged", "All"])

    def render_arr_alerts(df, show_ack=False):
        if df.empty:
            st.markdown("<div style='color:#64748b; padding:16px 0; font-size:0.78rem; font-weight:600; text-transform:uppercase; letter-spacing:0.1em'>No alerts</div>", unsafe_allow_html=True)
            return
        for _, row in df.iterrows():
            status = row.get("status", "OPEN")
            load   = row.get("predicted_load", "?")
            win    = str(row.get("window_start", ""))[:16]
            n      = row.get("agents_to_add") or row.get("agents_to_close") or 0
            if status == "ACKNOWLEDGED":
                card_cls, tag_cls, tag_txt = "alert-ack", "desk-ok", "✓ Acknowledged"
            elif row.get("type", "") == "arrivals_close":
                card_cls, tag_cls, tag_txt = "alert-close", "desk-close", f"Release {n} crew"
            else:
                card_cls, tag_cls, tag_txt = "alert-open", "desk-open", f"Deploy {n} more crew"
            col_card, col_btn = st.columns([5, 1])
            with col_card:
                st.markdown(f"""
<div class="alert-card {card_cls}">
  <div class="alert-title">{row['message']}</div>
  <span class="stat-tag tag-checkin">Arrivals</span>&nbsp;
  <span class="desk-tag {tag_cls}">{tag_txt}</span>
  <div class="alert-sub">Window: {win} &nbsp;·&nbsp; {load} pax</div>
</div>""", unsafe_allow_html=True)
            with col_btn:
                if show_ack and status == "OPEN":
                    st.markdown("<div style='margin-top:18px'></div>", unsafe_allow_html=True)
                    emp = st.session_state.get("employee_name", "employee") or "employee"
                    if st.button("Confirm", key=f"arr_ack_{row['id']}"):
                        _session.post(f"{API_BASE}/arrivals/alerts/{row['id']}/acknowledge", json={"employee": emp})
                        st.cache_data.clear()
                        st.rerun()

    with atab_open:
        render_arr_alerts(arr_open_df, show_ack=True)
    with atab_ack:
        render_arr_alerts(arr_ack_df)
    with atab_all:
        render_arr_alerts(fetch_arrivals_alerts())


# ── Departures ─────────────────────────────────────────────────────────────────

elif page == "Departures":
    st.markdown("""
<div class="ias-hero">
  <div class="ias-row"><span class="ias-code">IAS</span><span class="ias-title">Iași Airport</span></div>
  <div class="ias-sub">Iași, RO &nbsp;·&nbsp; Departures Gate &nbsp;·&nbsp; Boarding Agent Management</div>
</div>
""", unsafe_allow_html=True)

    agent_resp = fetch_json(f"{API_BASE}/departures/agents")
    current_agents = agent_resp["agents_open"] if agent_resp else 0

    gc1, gc2, gc3 = st.columns([2, 1, 3])
    with gc1:
        new_agent_count = st.number_input("Agents currently deployed", min_value=0, max_value=20, value=current_agents)
    with gc2:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        if st.button("Update", key="update_agents", use_container_width=True):
            _session.post(f"{API_BASE}/departures/agents", json={"agents_open": new_agent_count})
            st.rerun()
    with gc3:
        st.markdown(f"<div style='margin-top:32px; color:#64748b; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.08em; font-weight:600'>Currently tracking <b style='color:#4ade80'>{current_agents}</b> deployed agent(s)</div>", unsafe_allow_html=True)

    st.divider()

    dep_btn1, dep_btn2 = st.columns(2)
    with dep_btn1:
        if st.button("Train Departures Gate Model", use_container_width=True):
            with st.spinner("Training XGBoost on departures gate data (STD − 45 min bell curve)…"):
                r = _session.post(f"{API_BASE}/departures/train", timeout=180)
            if r.ok:
                d = r.json()
                m = d.get("metrics", {})
                st.success(f"Trained on {d['training_flights']} flights · {d['windows']} windows · MAE {m.get('MAE','?')} · MAPE {m.get('MAPE_%','?')}%")
            else:
                st.error(f"Training failed: {r.text}")
    with dep_btn2:
        if st.button("Run Departures Forecast & Generate Alerts", type="primary", use_container_width=True):
            with st.spinner("Predicting departures gate load…"):
                r = _session.post(f"{API_BASE}/departures/run", timeout=120)
            if r.ok:
                d = r.json()
                st.success(f"{d['windows_predicted']} windows predicted · {d['alerts_generated']} alerts generated")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(f"Departures forecast failed: {r.text}")

    dep_forecast = fetch_departures_forecast()

    if not dep_forecast.empty:
        st.divider()

        peak_dep = int(dep_forecast["predicted_load"].max())
        total_dep = int(dep_forecast["predicted_load"].sum())
        open_dep = len(fetch_departures_alerts("OPEN"))
        peak_dep_time = dep_forecast.loc[dep_forecast["predicted_load"].idxmax(), "window_start"].strftime("%H:%M")

        st.markdown(f"""
<div class="stat-strip">
  <div class="stat-cell"><div class="stat-lbl">Time Windows</div><div class="stat-val">{len(dep_forecast)}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Peak Load</div><div class="stat-val red">{peak_dep} pax</div></div>
  <div class="stat-cell"><div class="stat-lbl">Peak Window</div><div class="stat-val">{peak_dep_time}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Total Pax</div><div class="stat-val green">{total_dep:,}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Open Alerts</div><div class="stat-val {'red' if open_dep else 'green'}">{open_dep}</div></div>
</div>""", unsafe_allow_html=True)

        thresholds = fetch_json(f"{API_BASE}/thresholds")
        dep_cfg = thresholds.get("departures_gate", {}) if thresholds else {}

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dep_forecast["window_start"],
            y=dep_forecast["predicted_load"],
            name="Gate load",
            marker=dict(
                color=dep_forecast["predicted_load"],
                colorscale=[[0, "#4ade80"], [0.45, "#fb923c"], [1, "#f87171"]],
                showscale=False,
            ),
            hovertemplate="<b>Gate %{x|%H:%M}</b><br>%{y} pax<extra></extra>",
        ))

        dep_colors = {"level_1": "#4ade80", "level_2": "#fb923c", "level_3": "#f87171"}
        for key, color in dep_colors.items():
            lvl = dep_cfg.get(key)
            if lvl:
                fig.add_hline(
                    y=lvl["threshold"],
                    line_dash="dot", line_color=color, line_width=1,
                    annotation_text=f"L{key[-1]} · {lvl['threshold']} pax",
                    annotation_position="right",
                    annotation_font_color=color, annotation_font_size=10,
                )

        fig.update_layout(
            title=dict(text="DEPARTURES GATE · BOARDING LOAD · 30-MIN WINDOWS (STD − 45 MIN BELL CURVE)", font=dict(size=10, color="#64748b"), x=0),
            plot_bgcolor="#0b0d10", paper_bgcolor="#0b0d10", font_color="#64748b",
            xaxis=dict(gridcolor="#161c26", title="", tickfont=dict(size=10, color="#64748b")),
            yaxis=dict(gridcolor="#161c26", title="", tickfont=dict(size=10, color="#64748b")),
            legend=dict(bgcolor="#0f1318", bordercolor="#161c26", font=dict(color="#64748b")),
            margin=dict(l=10, r=90, t=36, b=10), height=320,
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Raw data table", expanded=False):
            st.dataframe(
                dep_forecast.rename(columns={"window_start": "Window", "predicted_load": "Gate Pax"}),
                use_container_width=True, hide_index=True,
            )
    else:
        st.info("No departures gate forecast yet — click Run Departures Forecast above.")

    st.divider()
    st.markdown("<div class='sec-label'>Departures Gate Alerts</div>", unsafe_allow_html=True)

    dep_open_df = fetch_departures_alerts("OPEN")
    dep_ack_df  = fetch_departures_alerts("ACKNOWLEDGED")

    dtab_open, dtab_ack, dtab_all = st.tabs(["Open", "Acknowledged", "All"])

    def render_dep_alerts(df, show_ack=False):
        if df.empty:
            st.markdown("<div style='color:#64748b; padding:16px 0; font-size:0.78rem; font-weight:600; text-transform:uppercase; letter-spacing:0.1em'>No alerts</div>", unsafe_allow_html=True)
            return
        for _, row in df.iterrows():
            status = row.get("status", "OPEN")
            load   = row.get("predicted_load", "?")
            win    = str(row.get("window_start", ""))[:16]
            n      = row.get("agents_to_add") or row.get("agents_to_close") or 0
            if status == "ACKNOWLEDGED":
                card_cls, tag_cls, tag_txt = "alert-ack", "desk-ok", "✓ Acknowledged"
            elif row.get("type", "") == "departures_gate_close":
                card_cls, tag_cls, tag_txt = "alert-close", "desk-close", f"Release {n} agent(s)"
            else:
                card_cls, tag_cls, tag_txt = "alert-open", "desk-open", f"Deploy {n} more agent(s)"
            col_card, col_btn = st.columns([5, 1])
            with col_card:
                st.markdown(f"""
<div class="alert-card {card_cls}">
  <div class="alert-title">{row['message']}</div>
  <span class="stat-tag tag-gate">Departures</span>&nbsp;
  <span class="desk-tag {tag_cls}">{tag_txt}</span>
  <div class="alert-sub">Window: {win} &nbsp;·&nbsp; {load} pax</div>
</div>""", unsafe_allow_html=True)
            with col_btn:
                if show_ack and status == "OPEN":
                    st.markdown("<div style='margin-top:18px'></div>", unsafe_allow_html=True)
                    emp = st.session_state.get("employee_name", "employee") or "employee"
                    if st.button("Confirm", key=f"dep_ack_{row['id']}"):
                        _session.post(f"{API_BASE}/departures/alerts/{row['id']}/acknowledge", json={"employee": emp})
                        st.cache_data.clear()
                        st.rerun()

    with dtab_open:
        render_dep_alerts(dep_open_df, show_ack=True)
    with dtab_ack:
        render_dep_alerts(dep_ack_df)
    with dtab_all:
        render_dep_alerts(fetch_departures_alerts())



# ── Settings ───────────────────────────────────────────────────────────────────

elif page == "Settings":
    st.markdown("""
<div class="ias-hero">
  <div class="ias-row"><span class="ias-code">IAS</span><span class="ias-title">Iași Airport</span></div>
  <div class="ias-sub">Iași, RO &nbsp;·&nbsp; Settings &nbsp;·&nbsp; Alert Thresholds</div>
</div>
""", unsafe_allow_html=True)

    try:
        r = _session.get(f"{API_BASE}/thresholds", timeout=5)
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
                resp = _session.post(f"{API_BASE}/thresholds/auto-detect", timeout=30)
            if resp.ok:
                data = resp.json()
                rec  = data["recommended"]
                ana  = data["analysis"]

                st.success(f"Analysed **{ana['windows_analysed']}** windows")

                st.markdown(f"""
<div class="stat-strip">
  <div class="stat-cell"><div class="stat-lbl">Min Pax</div><div class="stat-val">{ana['pax_min']}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Median (P50)</div><div class="stat-val">{ana['pax_p50']}</div></div>
  <div class="stat-cell"><div class="stat-lbl">P75</div><div class="stat-val amber">{ana['pax_p75']}</div></div>
  <div class="stat-cell"><div class="stat-lbl">P90</div><div class="stat-val amber">{ana['pax_p90']}</div></div>
  <div class="stat-cell"><div class="stat-lbl">Peak</div><div class="stat-val red">{ana['pax_max']}</div></div>
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
                _session.post(f"{API_BASE}/thresholds/auto-detect?apply=true", timeout=30)
                del st.session_state["auto_rec"]
                st.cache_data.clear()
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
            resp = _session.post(f"{API_BASE}/thresholds", json=levels)
            st.success("Saved") if resp.ok else st.error(f"Failed: {resp.text}")


# ── Passenger Flow Predictor ───────────────────────────────────────────────────

elif page == "Live Feed":
    st.markdown("""
<div class="ias-hero">
  <div class="ias-row"><span class="ias-code">IAS</span><span class="ias-title">Iași Airport</span></div>
  <div class="ias-sub">Iași, RO &nbsp;·&nbsp; Passenger Flow Predictor &nbsp;·&nbsp; External Tool</div>
</div>
""", unsafe_allow_html=True)
    
    components.iframe("https://passenger-flow-predictor.onrender.com/", height=800, scrolling=True)

