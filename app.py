"""
================================================================
Collective Mining Ltd. — Executive Intelligence Dashboard
app.py  ·  Entry point: `streamlit run app.py`

Layout:
  [0] Header bar — logo, title, market status, timestamp
  [1] CNL Hero Scorecard — 6 KPI cards with sparklines
  [2] Competitor Comparison Table — color-coded grid
  [3] Normalized Performance Chart — rebased to 100
  [4] CNL Candlestick + Volume + MAs
  [5] Technical Panel — RSI | Bollinger Bands
  [6] Relative Volume Comparison
  [7] Returns by Period — bar chart
  [8] Active Alerts Panel — log of triggered signals
  [9] Sidebar — controls (period, refresh, export)
================================================================
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import config as cfg
from src.data_fetcher import (
    fetch_all_histories,
    fetch_all_quotes,
    is_market_open,
    market_status_label,
    normalize_to_base100,
)
from src.metrics import build_all_metrics, detect_alerts, add_moving_averages
from src.charts import (
    chart_normalized_performance,
    chart_candlestick,
    chart_rsi,
    chart_bollinger_bands,
    chart_relative_volume,
    chart_returns_comparison,
    chart_sparkline,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EST = ZoneInfo("America/New_York")

# ── PAGE SETUP ────────────────────────────────────────────────

st.set_page_config(**cfg.PAGE_CONFIG)

# ── GLOBAL CSS ───────────────────────────────────────────────

st.markdown("""
<style>
  /* Import Inter font */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

  /* Root dark theme */
  html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #0D1117 !important;
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
  }
  [data-testid="stSidebar"] { background-color: #161B22 !important; }

  /* Remove default Streamlit padding */
  .main .block-container { padding-top: 0.5rem !important; }

  /* Hide Streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }

  /* ── KPI Card ────────────────────────────────────────── */
  .kpi-card {
    background: linear-gradient(145deg, #161B22, #1C2128);
    border: 1px solid #21262D;
    border-radius: 12px;
    padding: 18px 20px;
    text-align: center;
    transition: border-color 0.2s;
    position: relative;
    overflow: hidden;
  }
  .kpi-card:hover { border-color: #FFD700; }
  .kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #FFD700, transparent);
  }
  .kpi-label {
    color: #8B949E;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .kpi-value {
    color: #E6EDF3;
    font-family: 'JetBrains Mono', monospace;
    font-size: 22px;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 4px;
  }
  .kpi-sub {
    color: #8B949E;
    font-size: 11px;
  }
  .kpi-positive { color: #00C853 !important; }
  .kpi-negative { color: #FF1744 !important; }
  .kpi-neutral  { color: #FFD700 !important; }

  /* ── Section header ─────────────────────────────────── */
  .section-header {
    color: #E6EDF3;
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 24px 0 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #21262D;
  }

  /* ── Peer table ──────────────────────────────────────── */
  .peer-table { width: 100%; border-collapse: collapse; }
  .peer-table th {
    background: #21262D;
    color: #8B949E;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 10px 14px;
    text-align: right;
    white-space: nowrap;
  }
  .peer-table th:first-child { text-align: left; }
  .peer-table td {
    padding: 10px 14px;
    border-bottom: 1px solid #21262D;
    color: #C9D1D9;
    font-size: 13px;
    text-align: right;
    white-space: nowrap;
  }
  .peer-table td:first-child { text-align: left; }
  .peer-table tr:hover td { background: #1C2128; }
  .peer-table .target-row td { background: #1C2128; font-weight: 600; }
  .ticker-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.5px;
  }
  .positive { color: #00C853; font-weight: 600; }
  .negative { color: #FF1744; font-weight: 600; }

  /* ── Alert badge ─────────────────────────────────────── */
  .alert-row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
    background: #161B22;
    border: 1px solid #21262D;
    border-radius: 8px;
    margin-bottom: 8px;
  }
  .alert-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
    margin-top: 4px;
  }
  .alert-critical .alert-dot { background: #FF1744; }
  .alert-warning  .alert-dot { background: #FFD600; }
  .alert-info     .alert-dot { background: #00B4D8; }
  .alert-ticker { color: #FFD700; font-weight: 700; font-size: 13px; font-family: 'JetBrains Mono', monospace; }
  .alert-msg    { color: #C9D1D9; font-size: 13px; }

  /* ── Dashboard title bar ─────────────────────────────── */
  .dash-header {
    background: linear-gradient(135deg, #161B22 0%, #0D1117 100%);
    border-bottom: 2px solid #FFD700;
    padding: 18px 24px;
    margin: -0.5rem -1rem 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
  }
  .dash-title {
    color: #FFD700;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin: 0;
  }
  .dash-subtitle { color: #8B949E; font-size: 12px; margin-top: 2px; }
  .status-badge {
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
  }
  .status-open   { background: rgba(0,200,83,0.15); color: #00C853; border: 1px solid rgba(0,200,83,0.3); }
  .status-closed { background: rgba(255,23,68,0.12); color: #FF1744; border: 1px solid rgba(255,23,68,0.25); }
</style>
""", unsafe_allow_html=True)


# ── DATA LOADING (CACHED) ─────────────────────────────────────

@st.cache_data(ttl=cfg.CACHE_TTL_SECONDS, show_spinner=False)
def load_data(period: str = cfg.PERIOD_1Y):
    """Load and process all market data. Cached for CACHE_TTL_SECONDS."""
    tickers   = cfg.ALL_TICKERS + [cfg.BENCHMARK_TICKER]
    histories = fetch_all_histories(tickers, period=period)
    quotes    = fetch_all_quotes()
    metrics   = build_all_metrics(histories, quotes)
    alerts    = detect_alerts(metrics)
    normalized = normalize_to_base100(histories)
    return histories, quotes, metrics, alerts, normalized


# ── HEADER ────────────────────────────────────────────────────

def render_header():
    market_open = is_market_open()
    status_class = "status-open" if market_open else "status-closed"
    status_label = "🟢 TSX OPEN" if market_open else "🔴 TSX CLOSED"
    now_est = datetime.now(EST).strftime("%b %d, %Y  ·  %I:%M %p EST")

    st.markdown(f"""
    <div class="dash-header">
      <div>
        <p class="dash-title">⛏️ {cfg.DASHBOARD_TITLE}</p>
        <p class="dash-subtitle">{cfg.DASHBOARD_SUBTITLE}</p>
      </div>
      <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
        <span style="color:#8B949E;font-size:12px;font-family:'JetBrains Mono',monospace;">{now_est}</span>
        <span class="status-badge {status_class}">{status_label}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── CNL HERO KPI CARDS ────────────────────────────────────────

def render_cnl_scorecard(metrics: dict, histories: dict, quotes: dict):
    tk     = cfg.TARGET.ticker_primary
    m      = metrics.get(tk, {})
    df     = histories.get(tk)

    price   = m.get("price", 0)
    chg_pct = m.get("change_1d_pct", 0) or 0
    ret_ytd = (m.get("returns") or {}).get("ytd")
    ret_1m  = (m.get("returns") or {}).get("1m")
    rsi     = m.get("rsi")
    beta    = m.get("beta")
    vol     = m.get("volume", {})
    sr      = m.get("support_resistance", {})
    curr    = m.get("currency", "CAD")

    def pct_class(v):
        if v is None:   return "kpi-neutral"
        return "kpi-positive" if v >= 0 else "kpi-negative"

    def pct_str(v, decimals=2):
        if v is None: return "—"
        arrow = "▲" if v >= 0 else "▼"
        return f"{arrow} {abs(v):.{decimals}f}%"

    st.markdown('<p class="section-header">⭐ Collective Mining Ltd. — CNL (TSX)</p>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    kpis = [
        (c1, "PRICE", f"${price:.3f}", curr,          "kpi-neutral"),
        (c2, "1D CHANGE", pct_str(chg_pct),  "vs. yesterday", pct_class(chg_pct)),
        (c3, "1M RETURN", pct_str(ret_1m),   "30 days",       pct_class(ret_1m)),
        (c4, "YTD RETURN", pct_str(ret_ytd), "Year-to-Date",  pct_class(ret_ytd)),
        (c5, "RSI (14d)", f"{rsi:.0f}" if rsi else "—",
              "Overbought >70 | Oversold <30", "kpi-neutral"),
        (c6, "BETA (60d)", f"{beta:.2f}" if beta else "—",
              f"vs {cfg.BENCHMARK_DISPLAY}", "kpi-neutral"),
    ]

    for col, label, value, sub, cls in kpis:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-label">{label}</div>
              <div class="kpi-value {cls}">{value}</div>
              <div class="kpi-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    # Second row: Volume + S/R + Sparkline
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        rel_vol = vol.get("rel_vol_20d", 0)
        rv_cls  = "kpi-negative" if vol.get("is_spike") else "kpi-positive"
        st.markdown(f"""
        <div class="kpi-card" style="margin-top:12px;">
          <div class="kpi-label">RELATIVE VOLUME</div>
          <div class="kpi-value {rv_cls}">{rel_vol:.1f}×</div>
          <div class="kpi-sub">vs. 20-day avg ({_fmt_vol(vol.get('vol_today',0))} today)</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        w52h = sr.get("w52_high")
        w52l = sr.get("w52_low")
        st.markdown(f"""
        <div class="kpi-card" style="margin-top:12px;">
          <div class="kpi-label">52-WEEK RANGE</div>
          <div class="kpi-value kpi-neutral" style="font-size:16px;">${w52l:.3f} — ${w52h:.3f}</div>
          <div class="kpi-sub">
            {sr.get('dist_52wh_pct', 0):+.1f}% from high  ·
            {sr.get('dist_52wl_pct', 0):+.1f}% from low
          </div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        if df is not None and not df.empty:
            fig = chart_sparkline(df, cfg.TARGET, days=90)
            st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})


def _fmt_vol(vol: int) -> str:
    if vol >= 1_000_000: return f"{vol/1_000_000:.1f}M"
    if vol >= 1_000:     return f"{vol/1_000:.0f}K"
    return str(vol)


# ── PEER COMPARISON TABLE ────────────────────────────────────

def render_peer_table(metrics: dict, period: str = "1d"):
    period_map = {"1d": "1 Day", "1w": "1 Wk", "1m": "1 Mo", "3m": "3 Mo", "ytd": "YTD", "1y": "1 Year"}

    st.markdown('<p class="section-header">📊 Peer Comparison — Junior Mining</p>', unsafe_allow_html=True)

    rows_html = ""
    for company in cfg.COMPANIES:
        tk  = company.ticker_primary
        m   = metrics.get(tk, {})
        p   = m.get("price")
        chg = m.get("change_1d_pct")
        ret = (m.get("returns") or {}).get(period)
        rsi = m.get("rsi")
        b   = m.get("beta")
        vol = m.get("volume", {}).get("rel_vol_20d")
        sr  = m.get("support_resistance", {})
        w52h= sr.get("w52_high")

        is_target = company.is_target
        row_class = "target-row" if is_target else ""
        star      = "⭐ " if is_target else "&nbsp;&nbsp;&nbsp;"

        def _pct(v):
            if v is None: return '<span style="color:#484F58;">—</span>'
            cls = "positive" if v >= 0 else "negative"
            arr = "▲" if v >= 0 else "▼"
            return f'<span class="{cls}">{arr} {abs(v):.2f}%</span>'

        def _val(v, fmt=".3f"):
            return f"${v:{fmt}}" if v is not None else '<span style="color:#484F58;">—</span>'

        def _num(v, fmt=".2f"):
            return f"{v:{fmt}}" if v is not None else '<span style="color:#484F58;">—</span>'

        badge_style = f"background:rgba({_hex_to_rgb_str(company.color)},0.12);color:{company.color};"

        rows_html += f"""
        <tr class="{row_class}">
          <td>
            {star}<span class="ticker-badge" style="{badge_style}">{company.ticker_display}</span>
            &nbsp;<span style="color:#8B949E;font-size:12px;">{company.short_name}</span>
          </td>
          <td style="font-family:'JetBrains Mono',monospace;">{_val(p)}</td>
          <td>{_pct(chg)}</td>
          <td>{_pct(ret)}</td>
          <td style="color:#FFD700;font-family:'JetBrains Mono',monospace;">{_num(rsi, ".0f")}</td>
          <td style="color:#C9D1D9;font-family:'JetBrains Mono',monospace;">{_num(b)}</td>
          <td style="{'color:#FF1744;' if (vol or 0) >= cfg.VOLUME_ALERT_MULTIPLIER else ''};
                     font-family:'JetBrains Mono',monospace;">{_num(vol, ".1f")}×</td>
          <td style="font-family:'JetBrains Mono',monospace;">{_val(w52h)}</td>
        </tr>"""

    period_label = period_map.get(period, period.upper())
    st.markdown(f"""
    <div style="overflow-x:auto;border:1px solid #21262D;border-radius:10px;overflow:hidden;">
      <table class="peer-table">
        <thead>
          <tr>
            <th>Company</th>
            <th>Price (CAD)</th>
            <th>1D Chg</th>
            <th>{period_label} Rtn</th>
            <th>RSI</th>
            <th>Beta</th>
            <th>Rel.Vol</th>
            <th>52W High</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    <p style="color:#484F58;font-size:11px;margin-top:8px;">
      Data: Yahoo Finance · 15-min delay · Beta vs {cfg.BENCHMARK_DISPLAY}
    </p>
    """, unsafe_allow_html=True)


def _hex_to_rgb_str(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


# ── ALERTS PANEL ─────────────────────────────────────────────

def render_alerts_panel(alerts: list):
    n = len(alerts)
    has_critical = any(a["severity"] == "critical" for a in alerts)

    title_color = "#FF1744" if has_critical else ("#FFD600" if n > 0 else "#00C853")
    title_icon  = "🔴" if has_critical else ("🟡" if n > 0 else "✅")
    title_text  = f"{title_icon} {n} Active Alert(s)" if n > 0 else "✅ No Alerts — All Clear"

    st.markdown(f'<p class="section-header" style="color:{title_color};">{title_text}</p>',
                unsafe_allow_html=True)

    if not alerts:
        st.markdown("""
        <div style="background:#161B22;border:1px solid #21262D;border-radius:8px;padding:16px;
                    text-align:center;color:#00C853;font-size:13px;">
          All thresholds within normal range. No signals triggered.
        </div>""", unsafe_allow_html=True)
        return

    for a in alerts:
        sev_colors = {"critical": "#FF1744", "warning": "#FFD600", "info": "#00B4D8"}
        dot_color  = sev_colors.get(a["severity"], "#8B949E")
        border     = f"border-left:3px solid {dot_color};"
        st.markdown(f"""
        <div class="alert-row" style="{border}">
          <div class="alert-dot" style="background:{dot_color};"></div>
          <div>
            <span class="alert-ticker">{a['display']}</span>
            <span style="color:#484F58;margin:0 8px;">·</span>
            <span style="color:#8B949E;font-size:11px;text-transform:uppercase;
                         letter-spacing:0.5px;">{a['type'].replace('_',' ')}</span>
            <div class="alert-msg">{a['message']}</div>
          </div>
        </div>""", unsafe_allow_html=True)


# ── SIDEBAR ───────────────────────────────────────────────────

def render_sidebar() -> dict:
    with st.sidebar:
        st.markdown("## ⚙️ Dashboard Controls")
        st.markdown("---")

        period = st.selectbox(
            "Historical Period",
            options=["ytd", "1mo", "3mo", "6mo", "1y"],
            format_func=lambda x: {
                "ytd": "Year-to-Date",
                "1mo": "1 Month",
                "3mo": "3 Months",
                "6mo": "6 Months",
                "1y":  "1 Year",
            }[x],
            index=4,
            key="period_select",
        )

        ret_period = st.selectbox(
            "Return Period (Table)",
            options=["1d", "1w", "1m", "3m", "ytd", "1y"],
            format_func=lambda x: {
                "1d": "1 Day", "1w": "1 Week", "1m": "1 Month",
                "3m": "3 Months", "ytd": "YTD", "1y": "1 Year",
            }[x],
            index=4,
            key="ret_period",
        )

        chart_ticker = st.selectbox(
            "Deep-Dive Chart",
            options=[c.ticker_primary for c in cfg.COMPANIES],
            format_func=lambda x: cfg.TICKER_MAP[x].name if x in cfg.TICKER_MAP else x,
            key="chart_ticker",
        )

        st.markdown("---")
        st.markdown("**Alert Channels**")
        show_teams = bool(cfg.TEAMS_WEBHOOK_URL)
        show_email = bool(cfg.RESEND_API_KEY)
        st.markdown(f"{'🟢' if show_teams else '🔴'} Microsoft Teams")
        st.markdown(f"{'🟢' if show_email else '🔴'} Email (Resend)")

        st.markdown("---")
        if st.button("🔄 Force Refresh Data", width='stretch'):
            st.cache_data.clear()
            st.rerun()

        send_now = st.button("📧 Send Alert Now", width='stretch', type="primary")

        st.markdown("---")
        st.markdown(f"""
        <div style="color:#484F58;font-size:11px;line-height:1.6;">
          <b style="color:#8B949E;">Data Source</b><br>
          Yahoo Finance (15-min delay)<br><br>
          <b style="color:#8B949E;">Refresh Interval</b><br>
          {cfg.CACHE_TTL_SECONDS // 60} minutes<br><br>
          <b style="color:#8B949E;">Benchmark</b><br>
          {cfg.BENCHMARK_DISPLAY}
        </div>
        """, unsafe_allow_html=True)

    return {"period": period, "ret_period": ret_period, "chart_ticker": chart_ticker, "send_now": send_now}


# ── MAIN APP ──────────────────────────────────────────────────

def main():
    controls = render_sidebar()
    period      = controls["period"]
    ret_period  = controls["ret_period"]
    chart_ticker = controls["chart_ticker"]

    # Load data
    with st.spinner("Fetching market data…"):
        histories, quotes, metrics, alerts, normalized = load_data(period)

    # Handle manual alert send
    if controls.get("send_now"):
        from src.alerts import dispatch_alerts
        results = dispatch_alerts(alerts, metrics, force=True)
        ok = all(results.values())
        if ok:
            st.toast("✅ Alerts dispatched successfully!", icon="📧")
        else:
            st.toast("⚠️ Some channels failed. Check logs.", icon="⚠️")

    render_header()
    render_cnl_scorecard(metrics, histories, quotes)

    st.markdown("---")
    render_peer_table(metrics, period=ret_period)

    # ── Charts section ────────────────────────────────────────
    st.markdown("---")
    st.markdown('<p class="section-header">📈 Price Performance</p>', unsafe_allow_html=True)

    # Normalized Performance
    if not normalized.empty:
        fig_norm = chart_normalized_performance(
            normalized,
            title=f"Relative Performance — Base 100 ({period.upper()})",
        )
        st.plotly_chart(fig_norm, width='stretch', config={"displayModeBar": True})

    # Candlestick
    st.markdown("---")
    st.markdown(f'<p class="section-header">🕯️ {cfg.TICKER_MAP.get(chart_ticker, type("", (), {"name": chart_ticker})()).name} — Deep Dive</p>',
                unsafe_allow_html=True)

    df_chart = histories.get(chart_ticker)
    if df_chart is not None and not df_chart.empty:
        col_candle, col_rsi = st.columns([3, 1])
        with col_candle:
            fig_candle = chart_candlestick(df_chart, chart_ticker)
            st.plotly_chart(fig_candle, width='stretch', config={"displayModeBar": True})
        with col_rsi:
            fig_rsi = chart_rsi(df_chart, chart_ticker)
            st.plotly_chart(fig_rsi, width='stretch', config={"displayModeBar": False})

        # Bollinger Bands
        fig_bb = chart_bollinger_bands(df_chart, chart_ticker)
        st.plotly_chart(fig_bb, width='stretch', config={"displayModeBar": True})
    else:
        st.warning(f"No chart data available for {chart_ticker}.")

    # ── Volume & Returns ──────────────────────────────────────
    st.markdown("---")
    col_vol, col_ret = st.columns(2)

    with col_vol:
        st.markdown('<p class="section-header">📊 Relative Volume</p>', unsafe_allow_html=True)
        fig_vol = chart_relative_volume(metrics)
        st.plotly_chart(fig_vol, width='stretch', config={"displayModeBar": False})

    with col_ret:
        st.markdown(f'<p class="section-header">💹 Returns — {ret_period.upper()}</p>', unsafe_allow_html=True)
        fig_ret = chart_returns_comparison(metrics, period=ret_period)
        st.plotly_chart(fig_ret, width='stretch', config={"displayModeBar": False})

    # ── Alerts ────────────────────────────────────────────────
    st.markdown("---")
    render_alerts_panel(alerts)

    # ── Footer ────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-top:48px;padding:16px;text-align:center;border-top:1px solid #21262D;">
      <p style="color:#484F58;font-size:11px;margin:0;">
        Collective Mining Ltd. · Executive Intelligence Dashboard ·
        Data: Yahoo Finance (15-min delay) · Automated alerts: Microsoft Teams + Email ·
        For internal use only — CIBC Global Mining Group
      </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
