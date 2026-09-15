"""
================================================================
Collective Mining Ltd. — Executive Intelligence Dashboard
app.py  ·  Entry point: `streamlit run app.py`

Visual structure follows the Collective Mining Design System
(see src/theme.py). Expanded with Multi-Market support, TradingView
widget embedding, NASDAQ/GDXJ index benchmarking, and a complete
Peer Group Benchmarking Matrix.
================================================================
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

import config as cfg
from src import theme
from src.data_fetcher import (
    fetch_all_histories,
    fetch_all_quotes,
    fetch_cnl_multimarket_quotes,
    is_market_open,
    market_status_label,
    normalize_to_base100,
)
from src.metrics import (
    build_all_metrics,
    detect_alerts,
    compute_multi_index_analysis,
)
from src.charts import (
    chart_normalized_performance,
    chart_candlestick,
    chart_rsi,
    chart_bollinger_bands,
    chart_relative_volume,
    chart_returns_comparison,
    chart_sparkline,
    render_tradingview_widget,
    chart_index_comparison,
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
    histories   = fetch_all_histories(period=period)
    quotes      = fetch_all_quotes()
    metrics     = build_all_metrics(histories, quotes)
    alerts      = detect_alerts(metrics)
    normalized  = normalize_to_base100(histories)
    
    target_df   = histories.get(cfg.TARGET.ticker_primary)
    index_analysis = compute_multi_index_analysis(target_df, histories)
    multimarket_quotes = fetch_cnl_multimarket_quotes()

    return histories, quotes, metrics, alerts, normalized, index_analysis, multimarket_quotes


# ── FORMATTING HELPERS ────────────────────────────────────────

DASH = '<span class="cm-faint">—</span>'


def _pct(value, decimals: int = 2) -> str:
    """Signed percentage with the CM up/down marks."""
    if value is None:
        return DASH
    mark = "▲" if value >= 0 else "▼"
    cls  = "cm-pos" if value >= 0 else "cm-neg"
    return f'<span class="{cls}">{mark} {abs(value):.{decimals}f}%</span>'


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
    status_label = market_status_label()
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
        <span class="cm-listing">TSX: CNL · NYSE: CNL · FWB: GG1</span>
        <span class="cm-timestamp">{now_est}</span>
        <span class="cm-status {status_class}">{status_label}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── [1] CNL HERO SCORECARD ────────────────────────────────────

def render_cnl_scorecard(metrics: dict, histories: dict, index_analysis: dict):
    tk = cfg.TARGET.ticker_primary
    m  = metrics.get(tk, {})
    df = histories.get(tk)

    price   = m.get("price", 0)
    chg_pct = m.get("change_1d_pct", 0) or 0
    ret_ytd = (m.get("returns") or {}).get("ytd")
    ret_1m  = (m.get("returns") or {}).get("1m")
    rsi     = m.get("rsi")
    vol     = m.get("volume", {})
    sr      = m.get("support_resistance", {})
    curr    = m.get("currency", "CAD")

    # Get Beta vs NASDAQ
    nasdaq_beta = (index_analysis.get("^IXIC", {}).get("windows", {}).get("3M", {}).get("beta"))

    st.markdown(
        theme.section_heading(
            eyebrow="Target Company",
            title="Collective Mining Ltd. (CNL)",
            note=f"Guayabales & San Antonio (Caldas, Colombia) · TSX: CNL.TO · NYSE: CNL · FWB: GG1.F",
        ),
        unsafe_allow_html=True,
    )

    kpis = [
        ("Price",          f"${price:.3f}",               curr,                           "cm-accent"),
        ("1D Change",      _pct(chg_pct),                 "vs. previous close",           ""),
        ("1M Return",      _pct(ret_1m),                  "30 calendar days",             ""),
        ("YTD Return",     _pct(ret_ytd),                 "Year-to-date",                 ""),
        ("RSI (14d)",      f"{rsi:.0f}" if rsi else DASH, "Overbought &gt;70 · Oversold &lt;30", "cm-accent"),
        ("Beta (3M vs NASDAQ)", f"{nasdaq_beta:.2f}" if nasdaq_beta else DASH, "vs. NASDAQ Composite (^IXIC)", "cm-accent"),
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
                '<div class="cm-card-label">90-Day Price Trend</div>'
                "</div>",
                unsafe_allow_html=True,
            )
            fig = chart_sparkline(df, cfg.TARGET, days=90)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── [2] MULTI-MARKET & TRADINGVIEW WIDGET ─────────────────────

def render_multimarket_section(multimarket_quotes: dict):
    st.markdown(
        theme.section_heading(
            eyebrow="Global Listings",
            title="Multi-Market Quotes & TradingView Terminal",
            note="Live prices and TradingView interactive charting across TSX, NYSE American, and Börse Frankfurt.",
        ),
        unsafe_allow_html=True,
    )

    m_cols = st.columns(3)
    markets_order = ["TSX", "NYSE AMERICAN", "FRANKFURT"]

    for col, m_key in zip(m_cols, markets_order):
        q = multimarket_quotes.get(m_key, {})
        price   = q.get("price")
        chg     = q.get("change_1d_pct")
        curr    = q.get("currency", "")
        display = q.get("display_name", m_key)

        price_str = f"${price:.3f} {curr}" if price is not None else DASH
        with col:
            st.markdown(
                theme.stat_card(
                    display,
                    price_str,
                    _pct(chg),
                    "cm-accent" if chg is None or chg >= 0 else "cm-neg",
                ),
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_right = st.columns([1, 4])

    with c_left:
        st.markdown("<b>Select Exchange Market:</b>", unsafe_allow_html=True)
        selected_market = st.radio(
            "Market Symbol",
            options=["TSX:CNL", "NASDAQ:CNL", "AMEX:CNL", "FWB:GG1"],
            format_func=lambda x: {
                "TSX:CNL": "TSX (Toronto) — CNL",
                "NASDAQ:CNL": "NASDAQ — CNL",
                "AMEX:CNL": "NYSE (NYSE American) — CNL",
                "FWB:GG1": "Börse Frankfurt — GG1",
            }[x],
            key="tv_market_selector",
        )

    with c_right:
        tv_html = render_tradingview_widget(selected_market, height=460)
        components.html(tv_html, height=470)


# ── [3] INDEX BENCHMARKING (NASDAQ / GDXJ / GDX / XEG) ─────────

def render_index_benchmarking_section(index_analysis: dict):
    st.markdown(
        theme.section_heading(
            eyebrow="Macro & Index Benchmarks",
            title="NASDAQ Composite & Mining Index Relative Metrics",
            note="Comparative Beta and Pearson Correlation against NASDAQ (^IXIC), GDXJ (Junior Gold Miners), GDX (Gold Miners), and XEG (TSX Energy).",
        ),
        unsafe_allow_html=True,
    )

    if not index_analysis:
        st.info("Index benchmark data loading...")
        return

    # Index KPI Cards Row
    idx_cols = st.columns(len(index_analysis))
    for col, (symbol, data) in zip(idx_cols, index_analysis.items()):
        disp = data["display"]
        color = data["color"]
        w_3m = data["windows"].get("3M", {})
        b_3m = w_3m.get("beta")
        c_3m = w_3m.get("correlation")

        beta_str = f"Beta: {b_3m:.2f}" if b_3m is not None else "Beta: —"
        corr_str = f"Corr: {c_3m:+.2f}" if c_3m is not None else "Corr: —"

        with col:
            rgb = _hex_to_rgb_str(color)
            tag_style = f"color:{color};background:rgba({rgb},0.10);border:1px solid rgba({rgb},0.30);"
            card_html = (
                f'<div class="cm-card" style="padding:14px 16px;">'
                f'<span class="cm-tag" style="{tag_style}">{symbol}</span>'
                f'<p class="cm-card-label" style="margin-top:6px;font-size:11px;">{data["name"]}</p>'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;">'
                f'<span style="font-size:16px;font-weight:700;color:var(--text-heading);">{beta_str}</span>'
                f'<span class="cm-badge" style="{tag_style}">{corr_str}</span>'
                f'</div>'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([5, 7])

    with c1:
        st.markdown("<p style='font-size:12px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--cyan-600);margin-bottom:8px;'>Index Sensitivity Matrix (1M / 3M / 1Y)</p>", unsafe_allow_html=True)
        idx_rows = ""
        for symbol, data in index_analysis.items():
            color = data["color"]
            rgb = _hex_to_rgb_str(color)
            tag_style = f"color:{color};background:rgba({rgb},0.08);"
            
            wins = data.get("windows", {})
            w1m = wins.get("1M", {})
            w3m = wins.get("3M", {})
            w1y = wins.get("1Y", {})

            b1 = f"{w1m.get('beta'):.2f}" if w1m.get('beta') is not None else DASH
            b3 = f"{w3m.get('beta'):.2f}" if w3m.get('beta') is not None else DASH
            b1y = f"{w1y.get('beta'):.2f}" if w1y.get('beta') is not None else DASH

            c3 = w3m.get("correlation")
            c3_str = f"{c3:+.2f}" if c3 is not None else DASH
            
            corr_cls = "cm-badge-target" if c3 and c3 >= 0.5 else ("cm-badge-mid" if c3 and c3 < 0 else "cm-badge-major")

            idx_rows += f'<tr><td><span class="cm-tag" style="{tag_style}">{symbol}</span><span class="cm-company">{data["name"]}</span></td><td><b>{b1}</b></td><td><b>{b3}</b></td><td><b>{b1y}</b></td><td><span class="cm-badge {corr_cls}">{c3_str}</span></td></tr>'

        table_html = (
            '<div class="cm-table-wrap">'
            '<table class="cm-table">'
            '<thead>'
            '<tr>'
            '<th>Benchmark Index</th>'
            '<th>Beta (1M)</th>'
            '<th>Beta (3M)</th>'
            '<th>Beta (1Y)</th>'
            '<th>Correlation (3M)</th>'
            '</tr>'
            '</thead>'
            f'<tbody>{idx_rows}</tbody>'
            '</table>'
            '</div>'
            '<p class="cm-table-note">'
            'Beta &amp; Pearson Correlation calculated daily against CNL.TO prices.'
            '</p>'
        )
        st.markdown(table_html, unsafe_allow_html=True)

    with c2:
        metric_choice = st.radio(
            "Display Chart Metric:",
            options=["beta", "correlation"],
            format_func=lambda x: "Beta (Sensitivity / Relative Risk)" if x == "beta" else "Pearson Correlation Coefficient",
            horizontal=True,
            key="idx_metric_choice",
        )
        fig_idx = chart_index_comparison(index_analysis, metric=metric_choice)
        st.plotly_chart(fig_idx, use_container_width=True, config={"displayModeBar": False})


# ── [4] PEER BENCHMARKING MATRIX ──────────────────────────────

def render_peer_matrix_section(metrics: dict, normalized: pd.DataFrame, period: str = "1d"):
    st.markdown(
        theme.section_heading(
            eyebrow="Comparable Companies",
            title="Peer Group Benchmarking Matrix",
            note="Comprehensive evaluation of Colombia Basin Mid-Tiers, Regional Explorers, and Global Majors.",
        ),
        unsafe_allow_html=True,
    )

    # Category Filter
    col_filter, col_period = st.columns([2, 1])
    with col_filter:
        cat_filter = st.selectbox(
            "Filter Peer Category",
            options=["All Categories", "Mid-Tier / Explorer", "Major / Conglomerate"],
            key="peer_category_filter",
        )
    with col_period:
        table_period = st.selectbox(
            "Return Window",
            options=["1d", "1w", "1m", "3m", "ytd", "1y"],
            format_func=lambda x: {
                "1d": "1 Day", "1w": "1 Wk", "1m": "1 Mo",
                "3m": "3 Mo", "ytd": "YTD", "1y": "1 Yr",
            }[x],
            index=4,
            key="peer_table_period",
        )

    # Filter companies
    filtered_companies = cfg.COMPANIES
    if cat_filter != "All Categories":
        filtered_companies = [c for c in cfg.COMPANIES if c.category == cat_filter or c.is_target]

    rows_html = ""
    for company in filtered_companies:
        tk   = company.ticker_primary
        m    = metrics.get(tk, {})
        chg  = m.get("change_1d_pct")
        ret  = (m.get("returns") or {}).get(table_period)
        rsi  = m.get("rsi")
        beta = m.get("beta")
        rvol = m.get("volume", {}).get("rel_vol_20d")
        w52h = m.get("support_resistance", {}).get("w52_high")
        mcap = m.get("market_cap_str", "—")
        rel  = company.relevance

        row_class = "cm-target" if company.is_target else ""
        rvol_style = (
            f"color:{theme.STATUS_DANGER};font-weight:600;"
            if (rvol or 0) >= cfg.VOLUME_ALERT_MULTIPLIER else ""
        )
        tag_style = (
            f"color:{company.color};"
            f"background:rgba({_hex_to_rgb_str(company.color)},0.08);"
        )

        cat_badge_cls = "cm-badge-major" if company.category == "Major / Conglomerate" else "cm-badge-mid"
        if company.is_target:
            cat_badge_cls = "cm-badge-target"

        rows_html += f'<tr class="{row_class}"><td><span class="cm-tag" style="{tag_style}">{company.ticker_display}</span><span class="cm-company">{company.short_name}</span></td><td><span class="cm-badge {cat_badge_cls}">{company.category}</span></td><td>{_money(m.get("price"))}</td><td>{_pct(chg)}</td><td>{_pct(ret)}</td><td><b>{mcap}</b></td><td style="{rvol_style}">{_num(rvol, ".1f")}×</td><td>{_num(beta)}</td><td><span class="cm-faint">{rel}</span></td></tr>'

    peer_table_html = (
        '<div class="cm-table-wrap">'
        '<table class="cm-table">'
        '<thead>'
        '<tr>'
        '<th>Company</th>'
        '<th>Category</th>'
        '<th>Price</th>'
        '<th>1D Chg</th>'
        f'<th>{table_period.upper()} Return</th>'
        '<th>Market Cap</th>'
        '<th>Rel. Vol</th>'
        '<th>Beta</th>'
        '<th>Operational Relevance / Cuenca</th>'
        '</tr>'
        '</thead>'
        f'<tbody>{rows_html}</tbody>'
        '</table>'
        '</div>'
    )
    st.markdown(peer_table_html, unsafe_allow_html=True)

    # ── Normalized Performance Comparison ────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### Interactive Normalized Price Return Comparison (Base 100)")

    available_tickers = list(normalized.columns) if not normalized.empty else []
    default_selected = [c.ticker_primary for c in cfg.COMPANIES if c.is_target or c.short_name in ["Aris Mining", "Mineros", "Agnico Eagle", "Zijin Mining"]]
    default_selected = [t for t in default_selected if t in available_tickers]

    selected_peers = st.multiselect(
        "Select Companies & Indices to Compare:",
        options=available_tickers,
        default=default_selected,
        format_func=lambda x: cfg.TICKER_MAP[x].short_name if x in cfg.TICKER_MAP else cfg.BENCHMARK_INDICES.get(x, {}).get("display", x),
        key="peer_multiselect",
    )

    if not normalized.empty and selected_peers:
        fig_norm = chart_normalized_performance(
            normalized,
            selected_tickers=selected_peers,
            title=f"Cumulative Performance Comparison — Base 100",
        )
        st.plotly_chart(fig_norm, use_container_width=True, config={"displayModeBar": True})


# ── [5] ALERTS PANEL ─────────────────────────────────────────

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
        theme.section_heading(eyebrow="Signals", title="Active Market Alerts", note=note),
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

        chart_ticker = st.selectbox(
            "Technical Deep-Dive Ticker",
            options=[c.ticker_primary for c in cfg.COMPANIES],
            format_func=lambda x: cfg.TICKER_MAP[x].name if x in cfg.TICKER_MAP else x,
            key="chart_ticker",
        )

        st.markdown("---")
        st.markdown('<p class="cm-side-title">Email Executive Summary</p>', unsafe_allow_html=True)
        default_email = cfg.ALERT_EMAIL_TO[0] if cfg.ALERT_EMAIL_TO else ""
        recipient_email = st.text_input(
            "Recipient Email:",
            value=default_email,
            placeholder="executive@collectivemining.com",
            key="recipient_email_input",
        )

        send_now = st.button("Send Executive Summary", use_container_width=True, type="primary")

        st.markdown("---")
        if st.button("Force Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.markdown(f"""
        <div class="cm-side-block">
          <b>Data Sources</b><br>
          Yahoo Finance &amp; TradingView · 15m delay<br><br>
          <b>Cache Refresh</b><br>
          {cfg.CACHE_TTL_SECONDS // 60} minutes<br><br>
          <b>Monitored Universe</b><br>
          1 Target + 14 Peers + 4 Indices
        </div>
        """, unsafe_allow_html=True)

    return {"period": period, "chart_ticker": chart_ticker, "send_now": send_now, "recipient_email": recipient_email}


# ── [7] FOOTER ────────────────────────────────────────────────

def render_footer():
    st.markdown("""
    <div class="cm-footer">
      <p class="cm-footer-mark">Collective Mining Ltd.</p>
      <p class="cm-footer-copy">
        Executive Intelligence Dashboard · TSX: CNL · NYSE: CNL · FWB: GG1<br>
        Data: Yahoo Finance &amp; TradingView · Automated email reports dispatched on demand<br>
        Internal use only — prepared for the C-Level and the CIBC Global Mining Group.
      </p>
    </div>
    """, unsafe_allow_html=True)


# ── MAIN APP ──────────────────────────────────────────────────

def main():
    controls     = render_sidebar()
    period       = controls["period"]
    chart_ticker = controls["chart_ticker"]

    # Load data
    with st.spinner("Fetching market data & index analytics…"):
        histories, quotes, metrics, alerts, normalized, index_analysis, multimarket_quotes = load_data(period)

    # Handle manual alert send / email report dispatch
    if controls.get("send_now"):
        target_email = controls.get("recipient_email", "").strip()
        if not target_email:
            st.warning("Please enter a valid recipient email address.")
        else:
            with st.spinner(f"Sending Executive Summary to {target_email}…"):
                from src.alerts import send_email_alert, build_html_email
                now_str = datetime.now(EST).strftime("%I:%M %p EST  |  %b %d, %Y")
                sent_ok = send_email_alert(alerts, metrics, recipient_email=target_email, period=period)
                
                if sent_ok:
                    st.success(f"Executive Summary sent to **{target_email}** (Requested: {now_str}, Period: {period.upper()}).")
                else:
                    st.info(f"Executive Summary report generated for **{target_email}** (Requested: {now_str}, Period: {period.upper()}).")
                    with st.expander("📄 View Executive Summary Preview (Executive Intelligence Dashboard)", expanded=True):
                        preview_html = build_html_email(alerts, metrics)
                        components.html(preview_html, height=520, scrolling=True)

    render_header()

    # ── EXECUTIVE TABS ─────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "📊 CNL & Multi-Market Overview",
        "🏢 Peer Group Matrix",
        "📈 Technical Analysis & Alerts",
    ])

    with tab1:
        render_cnl_scorecard(metrics, histories, index_analysis)
        st.markdown("---")
        render_multimarket_section(multimarket_quotes)
        st.markdown("---")
        render_index_benchmarking_section(index_analysis)

    with tab2:
        render_peer_matrix_section(metrics, normalized, period="ytd")

    with tab3:
        deep_dive_name = cfg.TICKER_MAP[chart_ticker].name if chart_ticker in cfg.TICKER_MAP else chart_ticker
        st.markdown(
            theme.section_heading(
                eyebrow="Technical Deep Dive",
                title=deep_dive_name,
                note=f"Candlestick with MA{cfg.MA_SHORT}/{cfg.MA_MEDIUM}/{cfg.MA_LONG}, "
                     f"volume, RSI({cfg.RSI_PERIOD}) and Bollinger Bands.",
            ),
            unsafe_allow_html=True,
        )

        df_chart = histories.get(chart_ticker)
        if df_chart is not None and not df_chart.empty:
            col_candle, col_rsi = st.columns([3, 1])
            with col_candle:
                st.plotly_chart(chart_candlestick(df_chart, chart_ticker),
                                use_container_width=True, config={"displayModeBar": True})
            with col_rsi:
                st.plotly_chart(chart_rsi(df_chart, chart_ticker),
                                use_container_width=True, config={"displayModeBar": False})

            st.plotly_chart(chart_bollinger_bands(df_chart, chart_ticker),
                            use_container_width=True, config={"displayModeBar": True})
        else:
            st.warning(f"No chart data available for {chart_ticker}.")

        st.markdown("---")
        col_vol, col_ret = st.columns(2)
        with col_vol:
            st.markdown(
                theme.section_heading(eyebrow="Liquidity", title="Relative Volume"),
                unsafe_allow_html=True,
            )
            st.plotly_chart(chart_relative_volume(metrics),
                            use_container_width=True, config={"displayModeBar": False})

        with col_ret:
            st.markdown(
                theme.section_heading(eyebrow="Performance", title="YTD Returns Comparison"),
                unsafe_allow_html=True,
            )
            st.plotly_chart(chart_returns_comparison(metrics, period="ytd"),
                            use_container_width=True, config={"displayModeBar": False})

        st.markdown("---")
        render_alerts_panel(alerts)

    render_footer()


if __name__ == "__main__":
    main()
