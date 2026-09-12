"""
================================================================
Collective Mining — Executive Dashboard
src/charts.py

All Plotly chart components used by the Streamlit dashboard.
Each function returns a go.Figure ready to pass to st.plotly_chart().

Styling follows the Collective Mining Design System: white ground,
Montserrat, --border-subtle grid, cyan #20A7C9 as the single accent,
muted status colours for up/down. Chart logic is untouched.

Charts:
  1. Normalized price performance (base 100, all tickers)
  2. CNL candlestick with volume bars
  3. RSI panel
  4. Bollinger Bands overlay
  5. Relative volume bar chart (all tickers)
  6. KPI comparison bar chart (returns by period)
================================================================
"""

from __future__ import annotations

from typing import Dict, Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots 

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config as cfg
from src.metrics import add_moving_averages, compute_rsi, compute_bollinger_bands


# ── SHARED LAYOUT DEFAULTS ────────────────────────────────────

def _title(text: str, size: int = 13) -> dict:
    """CM headings are always uppercase, set in heading ink."""
    return dict(text=text.upper(), font=dict(size=size, color=cfg.CHART_TITLE_COLOR,
                                             family=cfg.CHART_FONT_FAMILY), x=0.01)


def _base_layout(**kwargs) -> dict:
    """
    Common Collective Mining layout overrides (white ground, cyan accent).
    Uses flat underscore notation (xaxis_gridcolor, yaxis_showgrid…) so
    callers can still pass xaxis=dict(…) or yaxis=dict(…) without a
    duplicate-keyword TypeError.  kwargs safely override any default.
    """
    base = dict(
        paper_bgcolor=cfg.CHART_PAPER_COLOR,
        plot_bgcolor =cfg.CHART_BG_COLOR,
        font=dict(family=cfg.CHART_FONT_FAMILY, color=cfg.CHART_FONT_COLOR, size=12),
        # Axis grid — flat notation avoids conflicts with explicit xaxis=/yaxis= kwargs
        xaxis_gridcolor=cfg.CHART_GRID_COLOR,
        xaxis_showgrid=True,
        xaxis_zeroline=False,
        xaxis_showline=False,
        yaxis_gridcolor=cfg.CHART_GRID_COLOR,
        yaxis_showgrid=True,
        yaxis_zeroline=False,
        yaxis_showline=False,
        legend=dict(
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor=cfg.CHART_GRID_COLOR,
            borderwidth=1,
            font=dict(size=11, color=cfg.CHART_FONT_COLOR),
        ),
        hoverlabel=dict(
            bgcolor=cfg.CHART_PAPER_COLOR,
            bordercolor=cfg.CHART_GRID_COLOR,
            font=dict(family=cfg.CHART_FONT_FAMILY, color=cfg.CHART_FONT_COLOR, size=11),
        ),
        margin=dict(l=50, r=20, t=50, b=40),
        hovermode="x unified",
    )
    base.update(kwargs)   # callers can override any key
    return base



# ── 1. NORMALIZED PERFORMANCE CHART ──────────────────────────

def chart_normalized_performance(
    normalized_df: pd.DataFrame,
    selected_tickers: list[str] | None = None,
    title: str = "Relative Price Performance (Base 100)",
) -> go.Figure:
    """
    Multi-line chart rebased to 100 at the start of the period.
    Supports filtering by selected_tickers, and highlights CNL.
    Reference indices (NASDAQ, GDXJ, GDX) are shown with dashed lines.
    """
    fig = go.Figure()

    if normalized_df.empty:
        return fig

    columns_to_plot = selected_tickers if selected_tickers else list(normalized_df.columns)

    for ticker in columns_to_plot:
        if ticker not in normalized_df.columns:
            continue

        company = cfg.TICKER_MAP.get(ticker)
        index_info = cfg.BENCHMARK_INDICES.get(ticker)

        if company:
            color = company.color
            name  = company.short_name
            width = 3.5 if company.is_target else 2.0
            dash  = "solid"
        elif index_info:
            color = index_info["color"]
            name  = index_info["display"]
            width = 2.0
            dash  = "dash"
        else:
            color = cfg.CHART_NEUTRAL
            name  = ticker
            width = 1.5
            dash  = "solid"

        fig.add_trace(go.Scatter(
            x=normalized_df.index,
            y=normalized_df[ticker].round(2),
            name=name,
            line=dict(color=color, width=width, dash=dash),
            mode="lines",
            hovertemplate=f"<b>{name}</b><br>%{{x|%b %d, %Y}}<br>%{{y:.1f}}<extra></extra>",
        ))

    # Reference line at 100
    fig.add_hline(
        y=100,
        line_dash="dot",
        line_color=cfg.CHART_NEUTRAL,
        line_width=1,
        annotation_text="Base 100",
        annotation_position="bottom right",
        annotation_font_color=cfg.CHART_NEUTRAL,
    )

    fig.update_layout(
        title=_title(title, size=14),
        **_base_layout(),
    )
    return fig


# ── 2. CANDLESTICK + VOLUME + MA ─────────────────────────────

def chart_candlestick(
    df: pd.DataFrame,
    ticker: str,
    show_volume: bool = True,
    show_ma: bool = True,
) -> go.Figure:
    """
    Full-featured financial chart:
    - Candlestick OHLC (upper panel)
    - Volume bars with red/green coloring (lower panel)
    - MA20, MA50, MA200 overlays
    """
    company   = cfg.TICKER_MAP.get(ticker)
    name      = company.short_name if company else ticker

    df_ma = add_moving_averages(df) if show_ma else df

    rows   = 2 if show_volume else 1
    h_spec = [{"ratio": 0.75}, {"ratio": 0.25}] if show_volume else [{}]

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[r["ratio"] for r in h_spec],
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        name=name,
        increasing_line_color=cfg.CANDLESTICK_UP,
        decreasing_line_color=cfg.CANDLESTICK_DOWN,
        increasing_fillcolor=cfg.CANDLESTICK_UP,
        decreasing_fillcolor=cfg.CANDLESTICK_DOWN,
    ), row=1, col=1)

    # Moving Averages
    if show_ma:
        ma_configs = [
            (f"MA{cfg.MA_SHORT}",  cfg.CHART_NEUTRAL,     1.2, "dot"),
            (f"MA{cfg.MA_MEDIUM}", cfg.CHART_ACCENT_DEEP, 1.4, "solid"),
            (f"MA{cfg.MA_LONG}",   cfg.CHART_ACCENT,      2.0, "solid"),
        ]
        for col_name, color, width, dash in ma_configs:
            if col_name in df_ma.columns:
                fig.add_trace(go.Scatter(
                    x=df_ma.index, y=df_ma[col_name].round(4),
                    name=col_name,
                    line=dict(color=color, width=width, dash=dash),
                    mode="lines",
                    hovertemplate=f"<b>{col_name}</b>: %{{y:.4f}}<extra></extra>",
                ), row=1, col=1)

    # Volume bars
    if show_volume:
        vol_colors = [
            cfg.CANDLESTICK_UP if row["Close"] >= row["Open"] else cfg.CANDLESTICK_DOWN
            for _, row in df.iterrows()
        ]
        fig.add_trace(go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker_color=vol_colors,
            marker_line_width=0,
            showlegend=False,
            hovertemplate="Vol: %{y:,.0f}<extra></extra>",
        ), row=2, col=1)

    fig.update_layout(
        title=_title(f"{name} — Price & Volume", size=14),
        xaxis_rangeslider_visible=False,
        **_base_layout(),
    )
    fig.update_yaxes(title_text="Price (CAD)", row=1, col=1,
                     gridcolor=cfg.CHART_GRID_COLOR, showgrid=True)
    fig.update_yaxes(title_text="Volume", row=2, col=1,
                     gridcolor=cfg.CHART_GRID_COLOR, showgrid=True)

    return fig


# ── 3. RSI PANEL ─────────────────────────────────────────────

def chart_rsi(df: pd.DataFrame, ticker: str) -> go.Figure:
    """
    RSI indicator chart with overbought/oversold bands.
    """
    company = cfg.TICKER_MAP.get(ticker)
    name    = company.short_name if company else ticker
    rsi     = compute_rsi(df)

    fig = go.Figure()

    # RSI line
    fig.add_trace(go.Scatter(
        x=rsi.index, y=rsi.round(1),
        name="RSI",
        line=dict(color=cfg.CHART_ACCENT, width=2),
        mode="lines",
        hovertemplate="RSI: %{y:.1f}<extra></extra>",
    ))

    # Overbought / Oversold zones
    fig.add_hrect(y0=cfg.RSI_OVERBOUGHT, y1=100, fillcolor=cfg.CHART_NEGATIVE,
                  opacity=0.08, line_width=0)
    fig.add_hrect(y0=0, y1=cfg.RSI_OVERSOLD, fillcolor=cfg.CHART_POSITIVE,
                  opacity=0.08, line_width=0)
    fig.add_hline(y=cfg.RSI_OVERBOUGHT, line_dash="dash",
                  line_color=cfg.CHART_NEGATIVE, line_width=1,
                  annotation_text=f"Overbought ({cfg.RSI_OVERBOUGHT:.0f})",
                  annotation_font_color=cfg.CHART_NEGATIVE)
    fig.add_hline(y=cfg.RSI_OVERSOLD, line_dash="dash",
                  line_color=cfg.CHART_POSITIVE, line_width=1,
                  annotation_text=f"Oversold ({cfg.RSI_OVERSOLD:.0f})",
                  annotation_font_color=cfg.CHART_POSITIVE)
    fig.add_hline(y=50, line_dash="dot", line_color=cfg.CHART_NEUTRAL, line_width=1)

    fig.update_layout(
        title=_title(f"{name} — RSI ({cfg.RSI_PERIOD})"),
        yaxis=dict(range=[0, 100], dtick=10, gridcolor=cfg.CHART_GRID_COLOR),
        **_base_layout(),
    )
    return fig


# ── 4. BOLLINGER BANDS ───────────────────────────────────────

def chart_bollinger_bands(df: pd.DataFrame, ticker: str) -> go.Figure:
    """
    Price chart with Bollinger Band upper/lower fill.
    """
    company = cfg.TICKER_MAP.get(ticker)
    name    = company.short_name if company else ticker
    bb_df   = compute_bollinger_bands(df)

    fig = go.Figure()

    # Fill between bands
    fig.add_trace(go.Scatter(
        x=bb_df.index, y=bb_df["BB_Upper"].round(4),
        name="BB Upper", mode="lines",
        line=dict(color="rgba(30,90,128,0.35)", width=1),
        hovertemplate="BB Upper: %{y:.4f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=bb_df.index, y=bb_df["BB_Lower"].round(4),
        name="BB Lower", mode="lines",
        line=dict(color="rgba(30,90,128,0.35)", width=1),
        fill="tonexty",
        fillcolor="rgba(30,90,128,0.06)",
        hovertemplate="BB Lower: %{y:.4f}<extra></extra>",
    ))

    # Midline (SMA)
    fig.add_trace(go.Scatter(
        x=bb_df.index, y=bb_df["BB_Mid"].round(4),
        name="BB Mid (SMA)", mode="lines",
        line=dict(color=cfg.CHART_ACCENT_DEEP, width=1.2, dash="dot"),
        hovertemplate="BB Mid: %{y:.4f}<extra></extra>",
    ))

    # Close price
    color = company.color if company else cfg.CHART_ACCENT
    fig.add_trace(go.Scatter(
        x=bb_df.index, y=bb_df["Close"].round(4),
        name=name, mode="lines",
        line=dict(color=color, width=2.5),
        hovertemplate="Close: %{y:.4f}<extra></extra>",
    ))

    fig.update_layout(
        title=_title(f"{name} — Bollinger Bands ({cfg.BB_PERIOD},{cfg.BB_STD})"),
        **_base_layout(),
    )
    return fig


# ── 5. RELATIVE VOLUME BAR CHART ─────────────────────────────

def chart_relative_volume(metrics: Dict[str, Dict]) -> go.Figure:
    """
    Horizontal bar chart showing each ticker's relative volume vs 20-day avg.
    Bar colored red/green. Threshold line at VOLUME_ALERT_MULTIPLIER.
    """
    companies = [c for c in cfg.COMPANIES]
    names     = [c.short_name for c in companies]
    tickers   = [c.ticker_primary for c in companies]
    colors_map = {c.ticker_primary: c.color for c in companies}

    rel_vols = []
    colors   = []
    for tk in tickers:
        m   = metrics.get(tk, {})
        vol = m.get("volume", {})
        rv  = vol.get("rel_vol_20d", 0)
        rel_vols.append(rv)
        colors.append(cfg.CHART_NEGATIVE if rv >= cfg.VOLUME_ALERT_MULTIPLIER
                      else colors_map.get(tk, cfg.CHART_NEUTRAL))

    fig = go.Figure(go.Bar(
        x=rel_vols,
        y=names,
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        text=[f"{v:.1f}×" for v in rel_vols],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Rel. Volume: %{x:.2f}×<extra></extra>",
    ))

    fig.add_vline(
        x=cfg.VOLUME_ALERT_MULTIPLIER,
        line_dash="dash",
        line_color=cfg.CHART_NEGATIVE,
        line_width=1.5,
        annotation_text=f"Alert threshold ({cfg.VOLUME_ALERT_MULTIPLIER:.0f}×)",
        annotation_font_color=cfg.CHART_NEGATIVE,
        annotation_position="top right",
    )
    fig.add_vline(x=1.0, line_dash="dot", line_color=cfg.CHART_NEUTRAL, line_width=1)

    fig.update_layout(
        title=_title("Relative Volume vs 20-Day Average"),
        xaxis_title="Relative Volume (×)",
        **_base_layout(hovermode="y unified"),
    )
    return fig


# ── 6. RETURNS COMPARISON BAR ─────────────────────────────────

def chart_returns_comparison(
    metrics: Dict[str, Dict],
    period: str = "ytd",
) -> go.Figure:
    """
    Grouped horizontal bar chart comparing returns across all tickers
    for the selected period. CNL highlighted.
    """
    period_labels = {
        "1d": "1 Day", "1w": "1 Week", "1m": "1 Month",
        "3m": "3 Months", "ytd": "YTD", "1y": "1 Year",
    }
    companies = cfg.COMPANIES
    names     = [c.short_name for c in companies]
    tickers   = [c.ticker_primary for c in companies]

    values = []
    bar_colors = []
    for tk in tickers:
        m      = metrics.get(tk, {})
        ret    = m.get("returns", {}).get(period)
        values.append(ret if ret is not None else 0)
        company = cfg.TICKER_MAP.get(tk)
        if ret is None:
            bar_colors.append(cfg.CHART_NEUTRAL)
        elif ret >= 0:
            bar_colors.append(cfg.CHART_POSITIVE if not (company and company.is_target) else cfg.CHART_ACCENT)
        else:
            bar_colors.append(cfg.CHART_NEGATIVE)

    fig = go.Figure(go.Bar(
        x=values,
        y=names,
        orientation="h",
        marker_color=bar_colors,
        marker_line_width=0,
        text=[f"{v:+.1f}%" if v != 0 else "N/A" for v in values],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Return: %{x:+.2f}%<extra></extra>",
    ))

    fig.add_vline(x=0, line_color=cfg.CHART_NEUTRAL, line_width=1)

    label = period_labels.get(period, period.upper())
    fig.update_layout(
        title=_title(f"Returns — {label}"),
        xaxis_title="Return (%)",
        **_base_layout(hovermode="y unified"),
    )
    return fig


# ── 7. MINI SPARKLINE ─────────────────────────────────────────

def chart_sparkline(df: pd.DataFrame, company: object, days: int = 30) -> go.Figure:
    """
    Ultra-compact price sparkline for KPI cards.
    No axes, minimal chrome.
    """
    subset = df["Close"].tail(days)
    color  = cfg.CHART_POSITIVE if subset.iloc[-1] >= subset.iloc[0] else cfg.CHART_NEGATIVE

    fig = go.Figure(go.Scatter(
        x=subset.index, y=subset.round(4),
        mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=f"rgba({_hex_to_rgb(color)}, 0.10)",
        hoverinfo="skip",
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
        height=60,
    )
    return fig


def _hex_to_rgb(hex_color: str) -> str:
    """Convert #RRGGBB to 'R, G, B' string for rgba() usage."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r}, {g}, {b}"


# ── 8. TRADINGVIEW EMBED WIDGET ──────────────────────────────

def render_tradingview_widget(symbol: str = "TSX:CNL", height: int = 480) -> str:
    """
    Returns HTML string for TradingView Advanced Real-Time Chart widget.
    Can be rendered via st.components.v1.html(html_code, height=height).
    """
    container_id = f"tv_chart_{symbol.replace(':', '_').replace('.', '_')}"
    return f"""
    <div class="tradingview-widget-container" style="height:{height}px;width:100%;">
      <div id="{container_id}" style="height:calc(100% - 32px);width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "{symbol}",
        "interval": "D",
        "timezone": "America/New_York",
        "theme": "light",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "allow_symbol_change": true,
        "container_id": "{container_id}"
      }});
      </script>
    </div>
    """


# ── 9. INDEX COMPARISON (BETA & CORRELATION) ──────────────────

def chart_index_comparison(multi_index_data: dict, metric: str = "beta") -> go.Figure:
    """
    Grouped bar chart comparing CNL's Beta or Correlation vs indices (^IXIC, GDXJ, GDX, XEG.TO)
    across windows: 1M, 3M, 1Y.
    """
    fig = go.Figure()

    if not multi_index_data:
        return fig

    windows = ["1M", "3M", "1Y"]

    for idx_symbol, data in multi_index_data.items():
        display = data.get("display", idx_symbol)
        color   = data.get("color", cfg.CHART_ACCENT)
        win_data = data.get("windows", {})

        y_vals = []
        for w in windows:
            val = win_data.get(w, {}).get(metric)
            y_vals.append(val if val is not None else 0)

        fig.add_trace(go.Bar(
            x=windows,
            y=y_vals,
            name=display,
            marker_color=color,
            hovertemplate=f"<b>{display}</b><br>Window: %{{x}}<br>{metric.title()}: %{{y:.3f}}<extra></extra>",
        ))

    title_label = "Beta Relative to Reference Indices" if metric == "beta" else "Pearson Correlation vs Reference Indices"

    fig.update_layout(
        title=_title(title_label, size=13),
        barmode="group",
        xaxis_title="Time Window",
        yaxis_title=metric.title(),
        **_base_layout(),
    )
    return fig

