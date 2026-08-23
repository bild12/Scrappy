"""
================================================================
Collective Mining Ltd. — Executive Intelligence Dashboard
app.py  ·  Entry point: `streamlit run app.py`

Visual structure follows the Collective Mining Design System
(see src/theme.py). Data, metrics and alert logic are untouched.

Layout:
  [0] Top bar — logo lockup, listing, market status, timestamp
  [1] CNL Hero Scorecard — 6 KPI cards + volume / range / trend
  [2] Peer Comparison Table — navy head, zebra rows, CNL highlighted
  [3] Normalized Performance Chart — rebased to 100
  [4] Deep Dive — candlestick + volume + MAs, RSI, Bollinger Bands
  [5] Relative Volume + Returns by Period
  [6] Active Alerts Panel — log of triggered signals
  [7] Navy footer band
  [S] Sidebar — controls (period, refresh, dispatch)
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
from src import theme
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

# ── DESIGN SYSTEM ─────────────────────────────────────────────

theme.inject(st)


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


# ── FORMATTING HELPERS ────────────────────────────────────────

DASH = '<span class="cm-faint">—</span>'


def _pct(value, decimals: int = 2) -> str:
    """Signed percentage with the CM up/down marks. Unicode, never emoji."""
    if value is None:
        return DASH
    mark = "▲" if value >= 0 else "▼"
    cls  = "cm-pos" if value >= 0 else "cm-neg"
    return f'<span class="{cls}">{mark} {abs(value):.{decimals}f}%</span>'


def _tone(value) -> str:
    if value is None:
        return "cm-accent"
    return "cm-pos" if value >= 0 else "cm-neg"


def _money(value, fmt: str = ".3f") -> str:
    return f"${value:{fmt}}" if value is not None else DASH


def _num(value, fmt: str = ".2f") -> str:
    return f"{value:{fmt}}" if value is not None else DASH


def _fmt_vol(vol: int) -> str:
    if vol >= 1_000_000: return f"{vol/1_000_000:.1f}M"
    if vol >= 1_000:     return f"{vol/1_000:.0f}K"
    return str(vol)


def _hex_to_rgb_str(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


# ── [0] TOP BAR ───────────────────────────────────────────────

def render_header():
    market_open  = is_market_open()
    status_class = "cm-status-open" if market_open else "cm-status-closed"
    status_label = market_status_label()   # the CSS dot carries the colour
    now_est      = datetime.now(EST).strftime("%b %d, %Y  ·  %I:%M %p EST")

    logo = theme.asset_data_uri("logo-horizontal.png")
    logo_html = (
        f'<img src="{logo}" alt="Collective Mining Ltd." />'
        f'<span class="cm-brand-divider"></span>'
        if logo else ""
    )

    st.markdown(f"""
    <div class="cm-topbar">
      <div class="cm-brand">
        {logo_html}
        <div class="cm-brand-copy">
          <p class="cm-brand-title">Executive Intelligence Dashboard</p>
          <p class="cm-brand-sub">{cfg.DASHBOARD_SUBTITLE}</p>
        </div>
      </div>
      <div class="cm-topbar-meta">
        <span class="cm-listing">Nasdaq &amp; TSX: CNL</span>
        <span class="cm-timestamp">{now_est}</span>
        <span class="cm-status {status_class}">{status_label}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── [1] CNL HERO SCORECARD ────────────────────────────────────

def render_cnl_scorecard(metrics: dict, histories: dict, quotes: dict):
    tk = cfg.TARGET.ticker_primary
    m  = metrics.get(tk, {})
    df = histories.get(tk)

    price   = m.get("price", 0)
    chg_pct = m.get("change_1d_pct", 0) or 0
    ret_ytd = (m.get("returns") or {}).get("ytd")
    ret_1m  = (m.get("returns") or {}).get("1m")
    rsi     = m.get("rsi")
    beta    = m.get("beta")
    vol     = m.get("volume", {})
    sr      = m.get("support_resistance", {})
    curr    = m.get("currency", "CAD")

    st.markdown(
        theme.section_heading(
            eyebrow="Target Company",
            title="Collective Mining Ltd.",
            note=f"{cfg.TARGET.ticker_display} · Guayabales, Caldas · Apollo system",
        ),
        unsafe_allow_html=True,
    )

    kpis = [
        ("Price",      f"${price:.3f}",                       curr,                            "cm-accent"),
        ("1D Change",  _pct(chg_pct),                         "vs. previous close",            ""),
        ("1M Return",  _pct(ret_1m),                          "30 calendar days",              ""),
        ("YTD Return", _pct(ret_ytd),                         "Year-to-date",                  ""),
        ("RSI (14d)",  f"{rsi:.0f}" if rsi else DASH,         "Overbought &gt;70 · Oversold &lt;30", "cm-accent"),
        ("Beta (60d)", f"{beta:.2f}" if beta else DASH,       f"vs. {cfg.BENCHMARK_DISPLAY}",  "cm-accent"),
    ]

    for col, (label, value, sub, tone) in zip(st.columns(6), kpis):
        with col:
            st.markdown(theme.stat_card(label, value, sub, tone), unsafe_allow_html=True)

    # Second row — volume, 52-week range, 90-day trend
    c1, c2, c3 = st.columns([1, 1, 2])

    with c1:
        rel_vol = vol.get("rel_vol_20d", 0)
        rv_tone = "cm-neg" if vol.get("is_spike") else "cm-accent"
        st.markdown(
            theme.stat_card(
                "Relative Volume",
                f"{rel_vol:.1f}×",
                f"vs. 20-day average · {_fmt_vol(vol.get('vol_today', 0))} today",
                rv_tone,
            ),
            unsafe_allow_html=True,
        )

    with c2:
        w52h = sr.get("w52_high")
        w52l = sr.get("w52_low")
        range_value = (
            f"{_money(w52l)} — {_money(w52h)}"
            if w52l is not None and w52h is not None else DASH
        )
        st.markdown(
            theme.stat_card(
                "52-Week Range",
                range_value,
                f"{sr.get('dist_52wh_pct', 0):+.1f}% from high · "
                f"{sr.get('dist_52wl_pct', 0):+.1f}% from low",
                "cm-accent",
                small=True,
            ),
            unsafe_allow_html=True,
        )

    with c3:
        if df is not None and not df.empty:
            st.markdown(
                '<div class="cm-spark-head">'
                '<div class="cm-card-label">90-Day Trend</div>'
                "</div>",
                unsafe_allow_html=True,
            )
            fig = chart_sparkline(df, cfg.TARGET, days=90)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ── [2] PEER COMPARISON TABLE ────────────────────────────────

def render_peer_table(metrics: dict, period: str = "1d"):
    period_map = {"1d": "1 Day", "1w": "1 Wk", "1m": "1 Mo",
                  "3m": "3 Mo", "ytd": "YTD", "1y": "1 Year"}

    st.markdown(
        theme.section_heading(
            eyebrow="Peer Set",
            title="Junior Mining Comparison",
            note="Collective Mining against five TSX / TSX-V exploration and development peers.",
        ),
        unsafe_allow_html=True,
    )

    rows_html = ""
    for company in cfg.COMPANIES:
        tk   = company.ticker_primary
        m    = metrics.get(tk, {})
        chg  = m.get("change_1d_pct")
        ret  = (m.get("returns") or {}).get(period)
        rsi  = m.get("rsi")
        beta = m.get("beta")
        rvol = m.get("volume", {}).get("rel_vol_20d")
        w52h = m.get("support_resistance", {}).get("w52_high")

        row_class = "cm-target" if company.is_target else ""
        rvol_style = (
            f"color:{theme.STATUS_DANGER};font-weight:600;"
            if (rvol or 0) >= cfg.VOLUME_ALERT_MULTIPLIER else ""
        )
        tag_style = (
            f"color:{company.color};"
            f"background:rgba({_hex_to_rgb_str(company.color)},0.08);"
        )

        rows_html += f"""
        <tr class="{row_class}">
          <td>
            <span class="cm-tag" style="{tag_style}">{company.ticker_display}</span>
            <span class="cm-company">{company.short_name}</span>
          </td>
          <td>{_money(m.get("price"))}</td>
          <td>{_pct(chg)}</td>
          <td>{_pct(ret)}</td>
          <td>{_num(rsi, ".0f")}</td>
          <td>{_num(beta)}</td>
          <td style="{rvol_style}">{_num(rvol, ".1f")}×</td>
          <td>{_money(w52h)}</td>
        </tr>"""

    st.markdown(f"""
    <div class="cm-table-wrap">
      <table class="cm-table">
        <thead>
          <tr>
            <th>Company</th>
            <th>Price (CAD)</th>
            <th>1D Chg</th>
            <th>{period_map.get(period, period.upper())} Rtn</th>
            <th>RSI</th>
            <th>Beta</th>
            <th>Rel. Vol</th>
            <th>52W High</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    <p class="cm-table-note">
      Source: Yahoo Finance · 15-minute delay · Beta calculated against {cfg.BENCHMARK_DISPLAY}
    </p>
    """, unsafe_allow_html=True)


# ── [6] ALERTS PANEL ─────────────────────────────────────────

def render_alerts_panel(alerts: list):
    n = len(alerts)
    has_critical = any(a["severity"] == "critical" for a in alerts)

    if n == 0:
        note = "All monitored thresholds are within range."
    elif has_critical:
        note = f"{n} signal(s) triggered — at least one is critical."
    else:
        note = f"{n} signal(s) triggered."

    st.markdown(
        theme.section_heading(eyebrow="Signals", title="Active Alerts", note=note),
        unsafe_allow_html=True,
    )

    if not alerts:
        st.markdown(
            '<div class="cm-empty">No signals fired. '
            "Price, volume, RSI and moving-average thresholds are all within normal range.</div>",
            unsafe_allow_html=True,
        )
        return

    for a in alerts:
        severity = a.get("severity", "info")
        st.markdown(f"""
        <div class="cm-alert cm-alert-{severity}">
          <div>
            <span class="cm-alert-ticker">{a['display']}</span>
            <span class="cm-faint" style="margin:0 8px;">·</span>
            <span class="cm-alert-type">{a['type'].replace('_', ' ')}</span>
            <div class="cm-alert-msg">{a['message']}</div>
          </div>
        </div>""", unsafe_allow_html=True)


# ── [S] SIDEBAR ───────────────────────────────────────────────

def render_sidebar() -> dict:
    with st.sidebar:
        st.markdown('<p class="cm-side-title">Dashboard Controls</p>', unsafe_allow_html=True)
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
        st.markdown('<p class="cm-side-title">Alert Channels</p>', unsafe_allow_html=True)
        teams_cls = "cm-channel-on" if cfg.TEAMS_WEBHOOK_URL else "cm-channel-off"
        email_cls = "cm-channel-on" if cfg.RESEND_API_KEY else "cm-channel-off"
        st.markdown(
            f'<div class="cm-channel {teams_cls}">Microsoft Teams</div>'
            f'<div class="cm-channel {email_cls}">Email (Resend)</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        if st.button("Force Refresh Data", width="stretch"):
            st.cache_data.clear()
            st.rerun()

        send_now = st.button("Send Alert Now", width="stretch", type="primary")

        st.markdown("---")
        st.markdown(f"""
        <div class="cm-side-block">
          <b>Data Source</b><br>
          Yahoo Finance · 15-minute delay<br><br>
          <b>Refresh Interval</b><br>
          {cfg.CACHE_TTL_SECONDS // 60} minutes<br><br>
          <b>Benchmark</b><br>
          {cfg.BENCHMARK_DISPLAY}
        </div>
        """, unsafe_allow_html=True)

    return {"period": period, "ret_period": ret_period,
            "chart_ticker": chart_ticker, "send_now": send_now}


# ── [7] FOOTER ────────────────────────────────────────────────

def render_footer():
    st.markdown("""
    <div class="cm-footer">
      <p class="cm-footer-mark">Collective Mining Ltd.</p>
      <p class="cm-footer-copy">
        Executive Intelligence Dashboard · Nasdaq &amp; TSX: CNL<br>
        Data: Yahoo Finance, 15-minute delay · Automated alerts dispatched to
        Microsoft Teams and email<br>
        Internal use only — prepared for the C-Level and the CIBC Global Mining Group.
      </p>
    </div>
    """, unsafe_allow_html=True)


# ── MAIN APP ──────────────────────────────────────────────────

def main():
    controls     = render_sidebar()
    period       = controls["period"]
    ret_period   = controls["ret_period"]
    chart_ticker = controls["chart_ticker"]

    # Load data
    with st.spinner("Fetching market data…"):
        histories, quotes, metrics, alerts, normalized = load_data(period)

    # Handle manual alert send
    if controls.get("send_now"):
        from src.alerts import dispatch_alerts
        results = dispatch_alerts(alerts, metrics, force=True)
        if all(results.values()):
            st.toast("Alerts dispatched.")
        else:
            st.toast("Some channels failed. Check the logs.")

    render_header()
    render_cnl_scorecard(metrics, histories, quotes)

    st.markdown("---")
    render_peer_table(metrics, period=ret_period)

    # ── Price performance ─────────────────────────────────────
    st.markdown("---")
    st.markdown(
        theme.section_heading(
            eyebrow="Relative Performance",
            title="Price Performance",
            note=f"All tickers rebased to 100 at the start of the selected period ({period.upper()}).",
        ),
        unsafe_allow_html=True,
    )

    if not normalized.empty:
        fig_norm = chart_normalized_performance(
            normalized,
            title=f"Relative Performance — Base 100 ({period.upper()})",
        )
        st.plotly_chart(fig_norm, width="stretch", config={"displayModeBar": True})

    # ── Deep dive ─────────────────────────────────────────────
    st.markdown("---")
    deep_dive_name = cfg.TICKER_MAP[chart_ticker].name if chart_ticker in cfg.TICKER_MAP else chart_ticker
    st.markdown(
        theme.section_heading(
            eyebrow="Deep Dive",
            title=deep_dive_name,
            note=f"Candlestick with MA{cfg.MA_SHORT}/{cfg.MA_MEDIUM}/{cfg.MA_LONG}, "
                 f"volume, RSI({cfg.RSI_PERIOD}) and Bollinger Bands "
                 f"({cfg.BB_PERIOD}, {cfg.BB_STD}).",
        ),
        unsafe_allow_html=True,
    )

    df_chart = histories.get(chart_ticker)
    if df_chart is not None and not df_chart.empty:
        col_candle, col_rsi = st.columns([3, 1])
        with col_candle:
            st.plotly_chart(chart_candlestick(df_chart, chart_ticker),
                            width="stretch", config={"displayModeBar": True})
        with col_rsi:
            st.plotly_chart(chart_rsi(df_chart, chart_ticker),
                            width="stretch", config={"displayModeBar": False})

        st.plotly_chart(chart_bollinger_bands(df_chart, chart_ticker),
                        width="stretch", config={"displayModeBar": True})
    else:
        st.warning(f"No chart data available for {chart_ticker}.")

    # ── Volume & returns ──────────────────────────────────────
    st.markdown("---")
    col_vol, col_ret = st.columns(2)

    with col_vol:
        st.markdown(
            theme.section_heading(eyebrow="Liquidity", title="Relative Volume"),
            unsafe_allow_html=True,
        )
        st.plotly_chart(chart_relative_volume(metrics),
                        width="stretch", config={"displayModeBar": False})

    with col_ret:
        st.markdown(
            theme.section_heading(eyebrow="Performance", title=f"Returns — {ret_period.upper()}"),
            unsafe_allow_html=True,
        )
        st.plotly_chart(chart_returns_comparison(metrics, period=ret_period),
                        width="stretch", config={"displayModeBar": False})

    # ── Alerts ────────────────────────────────────────────────
    st.markdown("---")
    render_alerts_panel(alerts)

    # ── Footer ────────────────────────────────────────────────
    render_footer()


if __name__ == "__main__":
    main()
