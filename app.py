"""
Golf Edge Finder — Streamlit Dashboard
Data Golf Model vs. Kalshi Market Prices
"""

import streamlit as st
import requests
import re
import pandas as pd
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="EdgeFinder Golf",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DG_API_KEY = st.secrets.get("DG_API_KEY", "")
KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"
DG_BASE = "https://feeds.datagolf.com"

KALSHI_SERIES = {
    "win": "KXPGATOUR",
    "top_5": "KXPGATOP5",
    "top_10": "KXPGATOP10",
    "top_20": "KXPGATOP20",
}

KNOWN_EVENTS = {
    "ATPBP": "Pebble Beach", "MAST": "Masters", "PGAC": "PGA Championship",
    "USOP": "US Open", "OPEN": "The Open", "PLAY": "Players", "GENE": "Genesis",
    "PHOE": "WM Phoenix", "FARM": "Farmers", "MEMO": "Memorial", "TRAV": "Travelers",
    "SENT": "Sentry", "SONY": "Sony Open", "WELL": "Wells Fargo", "RBC": "RBC Heritage",
}

MARKET_LABELS = {"win": "Win", "top_5": "Top 5", "top_10": "Top 10", "top_20": "Top 20"}
DG_FIELDS = {"win": "win", "top_5": "top_5", "top_10": "top_10", "top_20": "top_20"}


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* Dark theme overrides */
.stApp { background-color: #0a0f1a; }
header[data-testid="stHeader"] { background-color: #0a0f1a; }
.block-container { padding-top: 2rem; max-width: 1100px; }

/* Title styling */
.edge-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 28px;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.5px;
    margin-bottom: 0;
}
.edge-title span { color: #22c55e; }
.edge-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #475569;
    margin-top: 2px;
}

/* Stat cards */
.stat-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 16px;
    position: relative;
    overflow: hidden;
}
.stat-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #475569;
    letter-spacing: 0.1em;
    margin-bottom: 6px;
}
.stat-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 28px;
    font-weight: 700;
}

/* Event banner */
.event-banner {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 16px;
}
.event-name {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: #f8fafc;
}
.event-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #475569;
    letter-spacing: 0.12em;
}

/* Table styling */
.edge-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
}
.edge-table thead th {
    background: #0a0f1a;
    color: #475569;
    font-size: 10px;
    letter-spacing: 0.1em;
    font-weight: 600;
    padding: 12px 14px;
    text-align: left;
    border-bottom: 1px solid #1e293b;
    white-space: nowrap;
}
.edge-table tbody td {
    padding: 10px 14px;
    border-bottom: 1px solid #1e293b08;
    color: #e2e8f0;
    white-space: nowrap;
}
.edge-table tbody tr:nth-child(even) { background: #0a0f1a22; }
.edge-table tbody tr:hover { background: #1e293b33; }

/* Badges */
.badge-yes {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    background: #3b82f614;
    color: #60a5fa;
    border: 1px solid #3b82f630;
}
.badge-no {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    background: #f59e0b14;
    color: #fbbf24;
    border: 1px solid #f59e0b30;
}
.badge-event {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
}
.badge-pebble { background: #22c55e0a; color: #4ade80; border: 1px solid #22c55e1a; }
.badge-masters { background: #7c3aed14; color: #a78bfa; border: 1px solid #7c3aed30; }
.badge-other { background: #64748b14; color: #94a3b8; border: 1px solid #64748b30; }

.edge-green-hot { color: #22c55e; font-weight: 700; }
.edge-green-warm { color: #4ade80; font-weight: 700; }
.edge-green-mild { color: #86efac; font-weight: 700; }
.rr-hot { color: #22c55e; font-weight: 700; }
.rr-warm { color: #4ade80; font-weight: 700; }
.rr-cool { color: #94a3b8; font-weight: 700; }
.cost-red { color: #ef4444; }
.profit-green { color: #22c55e; }
.arrow { color: #334155; }
.model-dim { color: #64748b; }
.model-bright { color: #e2e8f0; }
.player-name {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    color: #f1f5f9;
}

/* Pulse dot */
.pulse-container { display: inline-flex; align-items: center; gap: 8px; }
.pulse-dot {
    width: 8px; height: 8px;
    background: #22c55e;
    border-radius: 50%;
    position: relative;
}
.pulse-dot::before {
    content: '';
    position: absolute;
    inset: -3px;
    border-radius: 50%;
    background: #22c55e;
    opacity: 0.4;
    animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse { 0%,100% { transform:scale(1); opacity:.4 } 50% { transform:scale(2); opacity:0 } }

/* Footer */
.footer-text {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #334155;
    margin-top: 16px;
}

/* Button overrides */
div.stButton > button {
    background: linear-gradient(135deg, #22c55e, #16a34a) !important;
    color: #0a0f1a !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    border: none !important;
    padding: 0.5rem 2rem !important;
    border-radius: 6px !important;
}

/* Selectbox and multiselect */
div[data-baseweb="select"] {
    font-family: 'JetBrains Mono', monospace !important;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_tournament_label(market):
    et = market.get("event_ticker", "")
    parts = et.split("-")
    if len(parts) >= 2:
        code = re.sub(r'\d+$', '', parts[1]).upper()
        for key, name in KNOWN_EVENTS.items():
            if key in code:
                return name
    return "Unknown"


def get_event_badge_class(tournament):
    if tournament == "Masters":
        return "badge-event badge-masters"
    elif tournament == "Pebble Beach":
        return "badge-event badge-pebble"
    return "badge-event badge-other"


def normalize_name(name):
    if not name:
        return ""
    name = name.strip()
    if "," in name:
        parts = name.split(",", 1)
        name = f"{parts[1].strip()} {parts[0].strip()}"
    name = name.lower()
    name = re.sub(r"[.\-']", "", name)
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"\s+(jr|sr|ii|iii|iv)$", "", name)
    return name


def format_player_name(name):
    if not name:
        return ""
    if "," in name:
        parts = name.split(",", 1)
        return f"{parts[1].strip()} {parts[0].strip()}"
    return name


def get_kalshi_player_name(market):
    name = market.get("yes_sub_title", "")
    if name and len(name.strip().split()) >= 2:
        name = re.sub(r"\s+(finish|wins?|top|make|miss).*$", "", name, flags=re.IGNORECASE)
        return name.strip()
    return None


# ============================================================
# API FUNCTIONS
# ============================================================

@st.cache_data(ttl=300)
def fetch_dg_predictions():
    params = {
        "tour": "pga", "odds_format": "percent",
        "file_format": "json", "key": DG_API_KEY,
    }
    r = requests.get(f"{DG_BASE}/preds/pre-tournament", params=params, timeout=15)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=120)
def fetch_kalshi_markets(series_ticker):
    all_markets = []
    cursor = None
    for _ in range(20):
        params = {"series_ticker": series_ticker, "status": "open", "limit": 200}
        if cursor:
            params["cursor"] = cursor
        r = requests.get(f"{KALSHI_BASE}/markets", params=params, timeout=15)
        if r.status_code != 200:
            break
        data = r.json()
        markets = data.get("markets", [])
        if not markets:
            break
        all_markets.extend(markets)
        cursor = data.get("cursor")
        if not cursor:
            break
    return all_markets


def calculate_all_edges(dg_data, kalshi_by_type):
    players = dg_data.get("baseline_history_fit", []) or dg_data.get("baseline", [])

    dg_lookup = {}
    dg_fuzzy = {}
    for p in players:
        norm = normalize_name(p.get("player_name", ""))
        if norm:
            dg_lookup[norm] = p
            parts = norm.split()
            if len(parts) >= 2:
                dg_fuzzy[f"{parts[0][0]}_{parts[-1]}"] = p

    edges = []
    matched = 0

    for m_type, markets in kalshi_by_type.items():
        for m in markets:
            k_name = get_kalshi_player_name(m)
            if not k_name:
                continue

            k_norm = normalize_name(k_name)
            yes_ask = m.get("yes_ask")
            no_ask = m.get("no_ask")

            dg = dg_lookup.get(k_norm)
            if not dg:
                parts = k_norm.split()
                if len(parts) >= 2:
                    dg = dg_fuzzy.get(f"{parts[0][0]}_{parts[-1]}")
            if not dg:
                continue

            matched += 1
            dg_prob = dg.get(DG_FIELDS.get(m_type))
            if dg_prob is None:
                continue

            dg_yes = dg_prob * 100 if dg_prob <= 1 else float(dg_prob)
            dg_no = 100 - dg_yes
            tournament = get_tournament_label(m)
            display_name = dg.get("player_name", k_name)

            if yes_ask and yes_ask > 0:
                edge = dg_yes - yes_ask
                edges.append({
                    "Player": format_player_name(display_name),
                    "Market": MARKET_LABELS.get(m_type, m_type),
                    "Side": "YES",
                    "Event": tournament,
                    "DG Prob": dg_yes,
                    "DG YES%": dg_yes,
                    "DG NO%": dg_no,
                    "Cost": yes_ask,
                    "Edge": edge,
                    "Profit": 100 - yes_ask,
                    "R/R": (100 - yes_ask) / yes_ask if yes_ask > 0 else 0,
                    "Ticker": m.get("ticker", ""),
                    "Volume": m.get("volume", 0),
                })

            if no_ask and 0 < no_ask < 100:
                edge = dg_no - no_ask
                edges.append({
                    "Player": format_player_name(display_name),
                    "Market": MARKET_LABELS.get(m_type, m_type),
                    "Side": "NO",
                    "Event": tournament,
                    "DG Prob": dg_no,
                    "DG YES%": dg_yes,
                    "DG NO%": dg_no,
                    "Cost": no_ask,
                    "Edge": edge,
                    "Profit": 100 - no_ask,
                    "R/R": (100 - no_ask) / no_ask if no_ask > 0 else 0,
                    "Ticker": m.get("ticker", ""),
                    "Volume": m.get("volume", 0),
                })

    return edges, matched, len(players)


# ============================================================
# MAIN APP
# ============================================================

# Header
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
    <div>
        <div class="edge-title">EDGE<span>FINDER</span> <span style="font-size:12px; background:#22c55e15; border:1px solid #22c55e30; color:#22c55e; padding:2px 8px; border-radius:4px; letter-spacing:0.12em; vertical-align:middle;">GOLF</span></div>
        <div class="edge-subtitle">Data Golf Model × Kalshi Markets</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Check API key
if not DG_API_KEY:
    st.error("⚠️ Data Golf API key not configured. Add DG_API_KEY to your Streamlit secrets.")
    st.stop()

# Scan button
col_btn, col_status = st.columns([1, 3])
with col_btn:
    scan = st.button("⛳ Scan Markets", use_container_width=True)

# Run scan
if scan or "edges" in st.session_state:
    if scan:
        with st.spinner("Pulling Data Golf predictions..."):
            try:
                dg_data = fetch_dg_predictions()
            except Exception as e:
                st.error(f"Data Golf error: {e}")
                st.stop()

        kalshi_by_type = {}
        for m_type, ticker in KALSHI_SERIES.items():
            with st.spinner(f"Scanning Kalshi {m_type.replace('_', ' ')} markets..."):
                markets = fetch_kalshi_markets(ticker)
                if markets:
                    kalshi_by_type[m_type] = markets

        edges, matched, field_size = calculate_all_edges(dg_data, kalshi_by_type)
        event_name = dg_data.get("event_name", "Unknown Event")

        st.session_state["edges"] = edges
        st.session_state["matched"] = matched
        st.session_state["field_size"] = field_size
        st.session_state["event_name"] = event_name
        st.session_state["last_updated"] = datetime.now()

    edges = st.session_state["edges"]
    matched = st.session_state["matched"]
    field_size = st.session_state["field_size"]
    event_name = st.session_state["event_name"]
    last_updated = st.session_state["last_updated"]

    with col_status:
        st.markdown(f"""
        <div class="pulse-container" style="margin-top:8px;">
            <div class="pulse-dot"></div>
            <span style="font-family:'JetBrains Mono',monospace; font-size:12px; color:#64748b;">
                Updated {last_updated.strftime("%-I:%M %p")}
            </span>
        </div>
        """, unsafe_allow_html=True)

    # Event banner
    st.markdown(f"""
    <div class="event-banner">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <div class="event-label">CURRENT EVENT</div>
                <div class="event-name">{event_name}</div>
            </div>
            <div style="display:flex; gap:24px;">
                <div style="text-align:center;">
                    <div class="event-label">FIELD</div>
                    <div style="font-size:18px; font-weight:600; color:#f8fafc; font-family:'JetBrains Mono',monospace;">{field_size}</div>
                </div>
                <div style="text-align:center;">
                    <div class="event-label">MATCHED</div>
                    <div style="font-size:18px; font-weight:600; color:#f8fafc; font-family:'JetBrains Mono',monospace;">{matched}</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Controls
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        min_edge = st.selectbox("Min Edge %", [3, 5, 7, 10], index=1)
    with c2:
        side_filter = st.selectbox("Side", ["All", "YES", "NO"])
    with c3:
        market_filter = st.selectbox("Market", ["All", "Win", "Top 5", "Top 10", "Top 20"])
    with c4:
        sort_by = st.selectbox("Sort By", ["Edge", "R/R", "Profit"])

    # Filter
    filtered = [e for e in edges if e["Edge"] >= min_edge]
    if side_filter != "All":
        filtered = [e for e in filtered if e["Side"] == side_filter]
    if market_filter != "All":
        filtered = [e for e in filtered if e["Market"] == market_filter]

    sort_key = {"Edge": "Edge", "R/R": "R/R", "Profit": "Profit"}[sort_by]
    filtered.sort(key=lambda x: x[sort_key], reverse=True)

    yes_count = sum(1 for e in filtered if e["Side"] == "YES")
    no_count = sum(1 for e in filtered if e["Side"] == "NO")
    avg_edge = sum(e["Edge"] for e in filtered) / len(filtered) if filtered else 0

    # Stat cards
    st.markdown(f"""
    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:16px 0;">
        <div class="stat-card">
            <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#22c55e40,transparent);"></div>
            <div class="stat-label">EDGES FOUND</div>
            <div class="stat-value" style="color:#22c55e;">{len(filtered)}</div>
        </div>
        <div class="stat-card">
            <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#3b82f640,transparent);"></div>
            <div class="stat-label">BUY YES</div>
            <div class="stat-value" style="color:#3b82f6;">{yes_count}</div>
        </div>
        <div class="stat-card">
            <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#f59e0b40,transparent);"></div>
            <div class="stat-label">BUY NO</div>
            <div class="stat-value" style="color:#f59e0b;">{no_count}</div>
        </div>
        <div class="stat-card">
            <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#a78bfa40,transparent);"></div>
            <div class="stat-label">AVG EDGE</div>
            <div class="stat-value" style="color:#a78bfa;">{avg_edge:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Build table HTML
    if not filtered:
        st.markdown(f"""
        <div style="background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:40px; text-align:center; color:#475569; font-family:'JetBrains Mono',monospace;">
            No edges above {min_edge}%. Try lowering the threshold.
        </div>
        """, unsafe_allow_html=True)
    else:
        rows_html = ""
        for i, e in enumerate(filtered):
            side_badge = f'<span class="badge-yes">{e["Side"]}</span>' if e["Side"] == "YES" else f'<span class="badge-no">{e["Side"]}</span>'
            event_cls = get_event_badge_class(e["Event"])
            event_badge = f'<span class="{event_cls}">{e["Event"]}</span>'

            if e["Side"] == "NO":
                model_html = f'<span class="model-dim">{e["DG YES%"]:.1f}% YES →</span> <span class="model-bright">{e["DG NO%"]:.1f}% NO</span>'
            else:
                model_html = f'<span class="model-bright">{e["DG Prob"]:.1f}%</span>'

            edge_cls = "edge-green-hot" if e["Edge"] >= 7 else "edge-green-warm" if e["Edge"] >= 5 else "edge-green-mild"
            rr_cls = "rr-hot" if e["R/R"] >= 2 else "rr-warm" if e["R/R"] >= 1 else "rr-cool"

            rows_html += f"""
            <tr>
                <td>{side_badge}</td>
                <td class="player-name">{e["Player"]}</td>
                <td style="color:#94a3b8;">{e["Market"]}</td>
                <td>{event_badge}</td>
                <td>{model_html}</td>
                <td style="color:#e2e8f0; font-weight:500;">{e["Cost"]}¢</td>
                <td><span class="{edge_cls}">+{e["Edge"]:.1f}%</span></td>
                <td><span class="cost-red">{e["Cost"]}¢</span> <span class="arrow">→</span> <span class="profit-green">{e["Profit"]}¢</span></td>
                <td><span class="{rr_cls}">{e["R/R"]:.1f}x</span></td>
            </tr>
            """

        st.markdown(f"""
        <div style="background:#0f172a; border:1px solid #1e293b; border-radius:8px; overflow:hidden;">
            <div style="overflow-x:auto;">
                <table class="edge-table">
                    <thead>
                        <tr>
                            <th>SIDE</th><th>PLAYER</th><th>MARKET</th><th>EVENT</th>
                            <th>DG MODEL</th><th>COST</th><th>EDGE</th>
                            <th>RISK → REWARD</th><th>R/R</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown(f"""
    <div class="footer-text" style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;">
        <span>Edge = DG probability − Kalshi ask price · Actual orderbook prices</span>
        <span>{matched} markets matched · {field_size} players</span>
    </div>
    """, unsafe_allow_html=True)
