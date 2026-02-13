"""
Golf Edge Finder — Streamlit Dashboard v6
True black · No gradients · Clean flat design · Created by Zack Hennigan
"""

import streamlit as st
import streamlit.components.v1 as components
import requests
import re
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="EdgeFinder Golf", page_icon="⛳", layout="wide", initial_sidebar_state="collapsed")

DG_API_KEY = st.secrets.get("DG_API_KEY", "")
KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"
DG_BASE = "https://feeds.datagolf.com"

KALSHI_SERIES = {"win": "KXPGATOUR", "top_5": "KXPGATOP5", "top_10": "KXPGATOP10", "top_20": "KXPGATOP20"}
KNOWN_EVENTS = {
    "ATPBP": "Pebble Beach", "MAST": "Masters", "PGAC": "PGA Championship",
    "USOP": "US Open", "OPEN": "The Open", "PLAY": "Players", "GENE": "Genesis",
    "PHOE": "WM Phoenix", "FARM": "Farmers", "MEMO": "Memorial", "TRAV": "Travelers",
    "SENT": "Sentry", "SONY": "Sony Open", "WELL": "Wells Fargo", "RBC": "RBC Heritage",
}
MARKET_LABELS = {"win": "Win", "top_5": "Top 5", "top_10": "Top 10", "top_20": "Top 20"}
DG_FIELDS = {"win": "win", "top_5": "top_5", "top_10": "top_10", "top_20": "top_20"}

EST = timezone(timedelta(hours=-5))
def now_est():
    return datetime.now(EST)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@300;400;500;600&display=swap');

.stApp { background: #090909; }
header[data-testid="stHeader"] { background: #090909; }
.block-container { padding-top: 1.5rem; max-width: 1140px; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

.edge-header { display: flex; align-items: center; gap: 14px; margin-bottom: 4px; }
.edge-logo {
    width: 38px; height: 38px; border-radius: 10px;
    background: #0a0a0a; border: 1px solid #1a1a1a;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
}
.edge-title { font-family: 'DM Sans', sans-serif; font-size: 22px; font-weight: 700; color: #f0f0f0; letter-spacing: -0.3px; }
.edge-title span { color: #4ade80; }
.edge-badge {
    font-family: 'IBM Plex Mono', monospace; font-size: 9px; font-weight: 600;
    letter-spacing: 0.14em; background: #0a0a0a; border: 1px solid #22c55e33;
    color: #4ade80; padding: 3px 10px; border-radius: 5px;
}
.edge-subtitle { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #404040; margin-top: 2px; }

.pulse-container { display: inline-flex; align-items: center; gap: 8px; }
.pulse-dot { width: 7px; height: 7px; background: #4ade80; border-radius: 50%; position: relative; }
.pulse-dot::before { content: ''; position: absolute; inset: -3px; border-radius: 50%; background: #4ade80; opacity: 0.3; animation: pulse 2.5s ease-in-out infinite; }
.pulse-dot-live { width: 7px; height: 7px; background: #f87171; border-radius: 50%; position: relative; }
.pulse-dot-live::before { content: ''; position: absolute; inset: -3px; border-radius: 50%; background: #f87171; opacity: 0.3; animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%,100% { transform:scale(1); opacity:.3 } 50% { transform:scale(2.5); opacity:0 } }

div.stButton > button {
    background: #16a34a !important;
    color: #f0f0f0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important; font-size: 13px !important;
    border: 1px solid #22c55e55 !important;
    padding: 0.5rem 1.8rem !important; border-radius: 8px !important;
}
div[data-baseweb="select"] > div { background: #161616 !important; border-color: #2a2a2a !important; font-family: 'IBM Plex Mono', monospace !important; color: #d0d0d0 !important; }
div[data-baseweb="select"] > div:hover { border-color: #4ade8044 !important; }
div[data-baseweb="select"] span { color: #d0d0d0 !important; }
div[data-baseweb="select"] svg { fill: #707070 !important; }
label { font-family: 'IBM Plex Mono', monospace !important; font-size: 11px !important; color: #606060 !important; letter-spacing: 0.08em !important; text-transform: uppercase !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================

def get_event_code(market):
    et = market.get("event_ticker", "")
    parts = et.split("-")
    return parts[1].upper() if len(parts) >= 2 else ""

def get_tournament_label(market):
    et = market.get("event_ticker", "")
    parts = et.split("-")
    if len(parts) >= 2:
        code = re.sub(r'\d+$', '', parts[1]).upper()
        for key, name in KNOWN_EVENTS.items():
            if key in code: return name
    return "Unknown"

def identify_current_event_code(markets_by_type, dg_event_name):
    event_code_counts, event_code_to_label = {}, {}
    for m_type, markets in markets_by_type.items():
        for m in markets:
            code = get_event_code(m)
            if code:
                event_code_counts[code] = event_code_counts.get(code, 0) + 1
                if code not in event_code_to_label: event_code_to_label[code] = get_tournament_label(m)
    if not event_code_counts: return None
    dg_lower = dg_event_name.lower()
    for code, label in event_code_to_label.items():
        if any(word in dg_lower for word in label.lower().split() if len(word) > 3): return code
    major_codes = {c for c, l in event_code_to_label.items() if l in ["Masters", "PGA Championship", "US Open", "The Open"]}
    non_major = {c: n for c, n in event_code_counts.items() if c not in major_codes}
    return max(non_major, key=non_major.get) if non_major else max(event_code_counts, key=event_code_counts.get)

def normalize_name(name):
    if not name: return ""
    name = name.strip()
    if "," in name:
        parts = name.split(",", 1); name = f"{parts[1].strip()} {parts[0].strip()}"
    return re.sub(r"\s+(jr|sr|ii|iii|iv)$", "", re.sub(r"\s+", " ", re.sub(r"[.\-']", "", name.lower())))

def format_player_name(name):
    if not name: return ""
    if "," in name:
        parts = name.split(",", 1); return f"{parts[1].strip()} {parts[0].strip()}"
    return name

def get_kalshi_player_name(market):
    name = market.get("yes_sub_title", "")
    if name and len(name.strip().split()) >= 2:
        return re.sub(r"\s+(finish|wins?|top|make|miss).*$", "", name, flags=re.IGNORECASE).strip()
    return None

# ============================================================
# API
# ============================================================

@st.cache_data(ttl=300)
def fetch_dg_live():
    params = {"tour": "pga", "dead_heat": "no", "odds_format": "percent", "file_format": "json", "key": DG_API_KEY}
    try:
        r = requests.get(f"{DG_BASE}/preds/in-play", params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                event_name = data.get("event_name", data.get("info", {}).get("event_name", "Live Tournament"))
                for key in ["data", "players", "baseline_history_fit", "baseline"]:
                    if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                        return {"event_name": event_name, "players": data[key], "source": "LIVE"}
            elif isinstance(data, list) and len(data) > 0:
                return {"event_name": "Live Tournament", "players": data, "source": "LIVE"}
    except: pass
    return None

@st.cache_data(ttl=300)
def fetch_dg_pretournament():
    params = {"tour": "pga", "odds_format": "percent", "file_format": "json", "key": DG_API_KEY}
    r = requests.get(f"{DG_BASE}/preds/pre-tournament", params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    return {"event_name": data.get("event_name", "Unknown Event"), "players": data.get("baseline_history_fit", []) or data.get("baseline", []), "source": "PRE-TOURNAMENT"}

@st.cache_data(ttl=120)
def fetch_kalshi_markets(series_ticker):
    all_markets, cursor = [], None
    for _ in range(20):
        params = {"series_ticker": series_ticker, "status": "open", "limit": 200}
        if cursor: params["cursor"] = cursor
        r = requests.get(f"{KALSHI_BASE}/markets", params=params, timeout=15)
        if r.status_code != 200: break
        data = r.json(); markets = data.get("markets", [])
        if not markets: break
        all_markets.extend(markets); cursor = data.get("cursor")
        if not cursor: break
    return all_markets

def calculate_all_edges(dg_data, kalshi_by_type):
    players = dg_data.get("players", [])
    dg_lookup, dg_fuzzy = {}, {}
    for p in players:
        norm = normalize_name(p.get("player_name", ""))
        if norm:
            dg_lookup[norm] = p
            parts = norm.split()
            if len(parts) >= 2: dg_fuzzy[f"{parts[0][0]}_{parts[-1]}"] = p
    current_event_code = identify_current_event_code(kalshi_by_type, dg_data.get("event_name", ""))
    edges, matched, skipped = [], 0, 0
    for m_type, markets in kalshi_by_type.items():
        for m in markets:
            if current_event_code:
                if get_event_code(m) and get_event_code(m) != current_event_code: skipped += 1; continue
            k_name = get_kalshi_player_name(m)
            if not k_name: continue
            k_norm = normalize_name(k_name)
            yes_ask, no_ask = m.get("yes_ask"), m.get("no_ask")
            dg = dg_lookup.get(k_norm)
            if not dg:
                parts = k_norm.split()
                if len(parts) >= 2: dg = dg_fuzzy.get(f"{parts[0][0]}_{parts[-1]}")
            if not dg: continue
            matched += 1
            dg_prob = dg.get(DG_FIELDS.get(m_type))
            if dg_prob is None: continue
            dg_yes = dg_prob * 100 if dg_prob <= 1 else float(dg_prob); dg_no = 100 - dg_yes
            tournament = get_tournament_label(m)
            display_name = format_player_name(dg.get("player_name", k_name))
            if yes_ask and yes_ask > 0:
                edges.append({"player": display_name, "market": MARKET_LABELS.get(m_type), "side": "YES", "event": tournament,
                    "dg_prob": dg_yes, "dg_yes": dg_yes, "dg_no": dg_no, "cost": yes_ask,
                    "edge": dg_yes - yes_ask, "profit": 100 - yes_ask, "rr": (100 - yes_ask) / yes_ask})
            if no_ask and 0 < no_ask < 100:
                edges.append({"player": display_name, "market": MARKET_LABELS.get(m_type), "side": "NO", "event": tournament,
                    "dg_prob": dg_no, "dg_yes": dg_yes, "dg_no": dg_no, "cost": no_ask,
                    "edge": dg_no - no_ask, "profit": 100 - no_ask, "rr": (100 - no_ask) / no_ask})
    return edges, matched, len(players), skipped


def build_results_html(filtered, event_name, field_size, matched, min_edge, yes_count, no_count, avg_edge, source, skipped_other):
    rows = ""
    for e in filtered:
        evt_cls = "badge-masters" if e["event"] == "Masters" else "badge-current" if e["event"] == "Pebble Beach" else "badge-other"
        evt_html = f'<span class="badge {evt_cls}">{e["event"]}</span>'

        if e["side"] == "YES":
            side_html = '<span class="badge badge-yes">YES</span>'
            model_html = f'<span class="text-bright">{e["dg_prob"]:.1f}%</span>'
        else:
            side_html = '<span class="badge badge-no">NO</span>'
            model_html = f'<span class="text-dim">{e["dg_yes"]:.1f}% &rarr;</span> <span class="text-bright">{e["dg_no"]:.1f}%</span>'

        edge_cls = "edge-hot" if e["edge"] >= 7 else "edge-warm" if e["edge"] >= 5 else "edge-mild"
        rr_cls = "rr-hot" if e["rr"] >= 2 else "rr-warm" if e["rr"] >= 1 else "rr-cool"

        rows += f"""<tr>
<td>{evt_html}</td>
<td class="player-cell">{e["player"]}</td>
<td class="text-secondary">{e["market"]}</td>
<td>{side_html}</td>
<td>{model_html}</td>
<td><span class="{edge_cls}">+{e["edge"]:.1f}%</span></td>
<td class="text-bright" style="font-weight:500;">{e["cost"]}&cent;</td>
<td><span class="{rr_cls}">{e["rr"]:.1f}x</span></td>
</tr>"""

    table_body = rows if filtered else f'<tr><td colspan="8" class="empty-state">No edges above {min_edge}% — try lowering the threshold</td></tr>'

    source_badge = '<span class="source-badge source-live"><span class="live-dot"></span>LIVE MODEL</span>' if source == "LIVE" else '<span class="source-badge source-pre">PRE-TOURNAMENT</span>'
    skipped_note = f" &middot; {skipped_other} future markets filtered" if skipped_other > 0 else ""

    return f"""<!DOCTYPE html><html><head><style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@300;400;500;600&display=swap');
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:#090909; color:#b0b0b0; font-family:'IBM Plex Mono',monospace; font-size:13px; -webkit-font-smoothing:antialiased; }}

.event-banner {{
    background: #0a0a0a;
    border: 1px solid #1a1a1a;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
}}
.event-label {{ font-size:9px; color:#404040; letter-spacing:0.14em; font-weight:600; text-transform:uppercase; }}
.event-name {{ font-family:'DM Sans',sans-serif; font-size:22px; font-weight:700; color:#e8e8e8; margin-top:6px; letter-spacing:-0.3px; }}
.event-stat {{ text-align:center; }}
.event-stat-value {{ font-size:20px; font-weight:600; color:#e8e8e8; font-family:'DM Sans',sans-serif; }}

.source-badge {{ display:inline-flex; align-items:center; gap:6px; padding:4px 12px; border-radius:6px; font-size:10px; font-weight:600; letter-spacing:0.08em; }}
.source-live {{ background:#f8717112; color:#f87171; border:1px solid #f8717130; }}
.source-pre {{ background:#4ade800d; color:#4ade80; border:1px solid #4ade8022; }}
.live-dot {{ width:6px; height:6px; background:#f87171; border-radius:50%; animation:livePulse 1.5s ease-in-out infinite; }}
@keyframes livePulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.4}} }}

.stat-row {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:16px; }}
.stat-card {{
    background: #0a0a0a;
    border: 1px solid #1a1a1a;
    border-radius: 10px;
    padding: 16px 18px;
}}
.stat-label {{ font-size:9px; color:#404040; letter-spacing:0.12em; font-weight:600; margin-bottom:8px; text-transform:uppercase; }}
.stat-value {{ font-family:'DM Sans',sans-serif; font-size:28px; font-weight:700; }}
.stat-green {{ color:#4ade80; }}
.stat-blue {{ color:#60a5fa; }}
.stat-amber {{ color:#fbbf24; }}
.stat-purple {{ color:#a78bfa; }}

.table-wrap {{
    background: #0a0a0a;
    border: 1px solid #1a1a1a;
    border-radius: 12px;
    overflow: hidden;
}}
table {{ width:100%; border-collapse:collapse; }}
thead th {{
    background: #050505;
    color: #404040;
    font-size: 9px;
    letter-spacing: 0.12em;
    font-weight: 600;
    padding: 14px 16px;
    text-align: left;
    border-bottom: 1px solid #1a1a1a;
    white-space: nowrap;
    text-transform: uppercase;
}}
tbody td {{
    padding: 12px 16px;
    border-bottom: 1px solid #0f0f0f;
    white-space: nowrap;
}}
tbody tr:nth-child(even) {{ background: #050505; }}
tbody tr:hover {{ background: #111111; }}

.player-cell {{ font-family:'DM Sans',sans-serif; font-weight:600; color:#e0e0e0; font-size:13px; }}
.text-bright {{ color:#d0d0d0; }}
.text-dim {{ color:#505050; }}
.text-secondary {{ color:#707070; }}
.empty-state {{ padding:48px !important; text-align:center; color:#404040; font-style:italic; }}

.badge {{ display:inline-block; padding:3px 10px; border-radius:5px; font-size:10px; font-weight:600; letter-spacing:0.03em; }}
.badge-yes {{ background:#60a5fa10; color:#60a5fa; border:1px solid #60a5fa25; }}
.badge-no {{ background:#fbbf2410; color:#fbbf24; border:1px solid #fbbf2425; }}
.badge-current {{ background:#4ade8008; color:#4ade80; border:1px solid #4ade801a; }}
.badge-masters {{ background:#a78bfa0d; color:#a78bfa; border:1px solid #a78bfa25; }}
.badge-other {{ background:#70707010; color:#707070; border:1px solid #70707025; }}

.edge-hot {{ color:#4ade80; font-weight:700; }}
.edge-warm {{ color:#86efac; font-weight:700; }}
.edge-mild {{ color:#a7f3d0; font-weight:600; }}
.rr-hot {{ color:#4ade80; font-weight:700; }}
.rr-warm {{ color:#86efac; font-weight:600; }}
.rr-cool {{ color:#606060; font-weight:500; }}

.footer {{
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid #1a1a1a;
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    font-size: 11px;
    color: #303030;
}}
.footer-credit {{
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    color: #353535;
    text-align: center;
    margin-top: 24px;
    padding: 16px 0;
    border-top: 1px solid #1a1a1a;
    letter-spacing: 0.02em;
}}
</style></head><body>

<div class="event-banner">
  <div>
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:2px;">
        <span class="event-label">Current Event</span>
        {source_badge}
    </div>
    <div class="event-name">{event_name}</div>
  </div>
  <div style="display:flex;gap:28px;">
    <div class="event-stat"><div class="event-label">Field</div><div class="event-stat-value">{field_size}</div></div>
    <div class="event-stat"><div class="event-label">Matched</div><div class="event-stat-value">{matched}</div></div>
  </div>
</div>

<div class="stat-row">
  <div class="stat-card"><div class="stat-label">Edges Found</div><div class="stat-value stat-green">{len(filtered)}</div></div>
  <div class="stat-card"><div class="stat-label">Buy Yes</div><div class="stat-value stat-blue">{yes_count}</div></div>
  <div class="stat-card"><div class="stat-label">Buy No</div><div class="stat-value stat-amber">{no_count}</div></div>
  <div class="stat-card"><div class="stat-label">Avg Edge</div><div class="stat-value stat-purple">{avg_edge:.1f}%</div></div>
</div>

<div class="table-wrap">
  <div style="overflow-x:auto;">
    <table>
      <thead><tr>
        <th>Event</th><th>Player</th><th>Market</th><th>Side</th><th>DG Model</th><th>Edge</th><th>Cost</th><th>R/R</th>
      </tr></thead>
      <tbody>{table_body}</tbody>
    </table>
  </div>
</div>

<div class="footer">
    <span>Edge = DG probability &minus; Kalshi ask &middot; Live orderbook prices</span>
    <span>{matched} matched &middot; {field_size} players{skipped_note}</span>
</div>

<div class="footer-credit">
    Created by Zack Hennigan
</div>

</body></html>"""


# ============================================================
# MAIN
# ============================================================

st.markdown("""
<div style="margin-bottom:20px;">
    <div class="edge-header">
        <div class="edge-logo">⛳</div>
        <div>
            <div class="edge-title">EDGE<span>FINDER</span> <span class="edge-badge">GOLF</span></div>
            <div class="edge-subtitle">Data Golf Model × Kalshi Markets</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if not DG_API_KEY:
    st.error("⚠️ Add DG_API_KEY to Streamlit secrets.")
    st.stop()

col_btn, col_status = st.columns([1, 3])
with col_btn:
    scan = st.button("⛳ Scan Markets", use_container_width=True)

c1, c2, c3, c4 = st.columns(4)
with c1: min_edge = st.selectbox("Min Edge %", [3, 5, 7, 10], index=1)
with c2: side_filter = st.selectbox("Side", ["All", "YES", "NO"])
with c3: market_filter = st.selectbox("Market", ["All", "Win", "Top 5", "Top 10", "Top 20"])
with c4: sort_by = st.selectbox("Sort By", ["Edge", "R/R", "Profit"])

if scan or "edges" in st.session_state:
    if scan:
        with st.spinner("Checking for live tournament data..."):
            dg_data = fetch_dg_live()
        if dg_data:
            st.toast("🔴 Live model active!", icon="🔴")
        else:
            with st.spinner("Using pre-tournament model..."):
                try:
                    dg_data = fetch_dg_pretournament()
                except Exception as e:
                    st.error(f"Data Golf error: {e}")
                    st.stop()

        kalshi_by_type = {}
        for m_type, ticker in KALSHI_SERIES.items():
            with st.spinner(f"Scanning Kalshi {m_type.replace('_', ' ')} markets..."):
                markets = fetch_kalshi_markets(ticker)
                if markets: kalshi_by_type[m_type] = markets

        edges, matched, field_size, skipped_other = calculate_all_edges(dg_data, kalshi_by_type)
        st.session_state.update({
            "edges": edges, "matched": matched, "field_size": field_size,
            "skipped_other": skipped_other,
            "event_name": dg_data.get("event_name", "Unknown"),
            "source": dg_data.get("source", "PRE-TOURNAMENT"),
            "last_updated": now_est(),
        })

    edges = st.session_state["edges"]
    matched = st.session_state["matched"]
    field_size = st.session_state["field_size"]
    skipped_other = st.session_state.get("skipped_other", 0)
    event_name = st.session_state["event_name"]
    source = st.session_state["source"]
    last_updated = st.session_state["last_updated"]

    with col_status:
        dot_class = "pulse-dot-live" if source == "LIVE" else "pulse-dot"
        label = "LIVE" if source == "LIVE" else "Pre-Tournament"
        time_str = last_updated.strftime("%I:%M %p") + " EST"
        st.markdown(f"""
        <div class="pulse-container" style="margin-top:8px;">
            <div class="{dot_class}"></div>
            <span style="font-family:'IBM Plex Mono',monospace;font-size:11px;color:#404040;">
                {label} &middot; {time_str}
            </span>
        </div>
        """, unsafe_allow_html=True)

    filtered = [e for e in edges if e["edge"] >= min_edge]
    if side_filter != "All": filtered = [e for e in filtered if e["side"] == side_filter]
    if market_filter != "All": filtered = [e for e in filtered if e["market"] == market_filter]
    filtered.sort(key=lambda x: x[{"Edge": "edge", "R/R": "rr", "Profit": "profit"}[sort_by]], reverse=True)

    yes_count = sum(1 for e in filtered if e["side"] == "YES")
    no_count = sum(1 for e in filtered if e["side"] == "NO")
    avg_edge = sum(e["edge"] for e in filtered) / len(filtered) if filtered else 0

    html = build_results_html(filtered, event_name, field_size, matched, min_edge, yes_count, no_count, avg_edge, source, skipped_other)
    components.html(html, height=380 + max(len(filtered), 1) * 46, scrolling=False)
