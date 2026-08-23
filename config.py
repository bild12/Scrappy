"""
================================================================
Collective Mining — Executive Dashboard
config.py — Central configuration for all tickers, thresholds,
             colors, and display parameters.
================================================================
"""

import os
from dataclasses import dataclass
from typing import Dict, List


# ── COMPANY UNIVERSE ─────────────────────────────────────────

@dataclass
class Company:
    name: str
    short_name: str       # For chart labels (max 12 chars)
    ticker_primary: str   # yfinance symbol
    ticker_display: str   # Human-readable ticker shown in UI
    exchange: str
    color: str            # Plotly-compatible hex color
    is_target: bool = False


# All companies monitored. CNL is always the star.
COMPANIES: List[Company] = [
    Company(
        name="Collective Mining Ltd.",
        short_name="Collective",
        ticker_primary="CNL.TO",
        ticker_display="CNL (TSX)",
        exchange="TSX",
        color="#20A7C9",          # --cyan-500 · the brand accent
        is_target=True,
    ),
    Company(
        name="Faraday Copper Corp.",
        short_name="Faraday",
        ticker_primary="FDY.TO",
        ticker_display="FDY (TSX)",
        exchange="TSX",
        color="#B4703C",          # --commodity-copper
    ),
    Company(
        name="Marimaca Copper Corp.",
        short_name="Marimaca",
        ticker_primary="MARI.TO",
        ticker_display="MARI (TSX)",
        exchange="TSX",
        color="#1E5A80",          # --navy-500
    ),
    Company(
        name="Lumina Metals Corp.",
        short_name="Lumina",
        ticker_primary="LMCU.TO",
        ticker_display="LMCU (TSX)",
        exchange="TSX",
        color="#C9A227",          # --commodity-gold
    ),
    Company(
        name="NorthIsle Copper and Gold",
        short_name="NorthIsle",
        ticker_primary="NCX.V",
        ticker_display="NCX (TSX-V)",
        exchange="TSX-V",
        color="#5C6B73",          # --commodity-tungsten
    ),
    Company(
        name="Osisko Metals Inc.",
        short_name="Osisko Met.",
        ticker_primary="OM.TO",
        ticker_display="OM (TSX)",
        exchange="TSX",
        color="#A8B0B8",          # --commodity-silver
    ),
]

# Quick lookups
TICKER_MAP: Dict[str, Company] = {c.ticker_primary: c for c in COMPANIES}
TARGET: Company = next(c for c in COMPANIES if c.is_target)
ALL_TICKERS: List[str] = [c.ticker_primary for c in COMPANIES]

# Benchmark index (for Beta calculation)
BENCHMARK_TICKER  = "XEG.TO"
BENCHMARK_DISPLAY = "XEG (TSX)"

# ── DATA PARAMETERS ──────────────────────────────────────────

PERIOD_1D   = "5d"
PERIOD_1M   = "1mo"
PERIOD_3M   = "3mo"
PERIOD_YTD  = "ytd"
PERIOD_1Y   = "1y"

INTRADAY_INTERVAL    = "15m"
CACHE_TTL_SECONDS    = 900      # 15 min

# Technical analysis windows
MA_SHORT    = 20
MA_MEDIUM   = 50
MA_LONG     = 200
RSI_PERIOD  = 14
BB_PERIOD   = 20
BB_STD      = 2.0
BETA_PERIOD_DAYS = 60

# ── ALERT THRESHOLDS ─────────────────────────────────────────

PRICE_ALERT_THRESHOLD   = float(os.getenv("PRICE_ALERT_THRESHOLD", "3.0"))
VOLUME_ALERT_MULTIPLIER = float(os.getenv("VOLUME_ALERT_MULTIPLIER", "2.0"))
RSI_OVERBOUGHT          = float(os.getenv("RSI_OVERBOUGHT", "70"))
RSI_OVERSOLD            = float(os.getenv("RSI_OVERSOLD", "30"))

# ── NOTIFICATION CHANNELS — Teams + Email ONLY ───────────────

TEAMS_WEBHOOK_URL  = os.getenv("TEAMS_WEBHOOK_URL", "")

RESEND_API_KEY     = os.getenv("RESEND_API_KEY", "")
ALERT_EMAIL_FROM   = os.getenv("ALERT_EMAIL_FROM", "alerts@collectivemining.com")
ALERT_EMAIL_TO     = [e.strip() for e in os.getenv("ALERT_EMAIL_TO", "").split(",") if e.strip()]

# ── DASHBOARD SETTINGS ───────────────────────────────────────

DASHBOARD_TITLE    = "Collective Mining — Executive Intelligence Dashboard"
DASHBOARD_SUBTITLE = "Real-Time Market Monitoring  ·  C-Level & CIBC Global Mining Group"

MARKET_OPEN_HOUR   = 9
MARKET_OPEN_MIN    = 30
MARKET_CLOSE_HOUR  = 16
MARKET_CLOSE_MIN   = 0

_FAVICON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "favicon.png")

PAGE_CONFIG = {
    "page_title": "Collective Mining — Executive Intelligence",
    "page_icon": _FAVICON if os.path.exists(_FAVICON) else None,
    "layout": "wide",
    "initial_sidebar_state": "collapsed",
}

# ── CHART / THEME TOKENS ─────────────────────────────────────
# Sourced from the Collective Mining Design System (tokens/colors.css).
# The full token set lives in src/theme.py; these aliases keep the chart
# layer readable and are the only colours Plotly ever sees.

CHART_BG_COLOR    = "#FFFFFF"   # --surface-page
CHART_PAPER_COLOR = "#FFFFFF"   # --surface-card
CHART_GRID_COLOR  = "#E1E5E9"   # --border-subtle
CHART_FONT_COLOR  = "#4A4A4A"   # --text-body
CHART_TITLE_COLOR = "#333333"   # --text-heading
CHART_POSITIVE    = "#2E7D51"   # --status-success
CHART_NEGATIVE    = "#B3341F"   # --status-danger
CHART_NEUTRAL     = "#9AA3AC"   # --neutral-400
CHART_ACCENT      = "#20A7C9"   # --cyan-500 · the single accent
CHART_ACCENT_DEEP = "#1E5A80"   # --navy-500
CHART_FONT_FAMILY = "Montserrat, 'Helvetica Neue', Arial, sans-serif"

CANDLESTICK_UP    = "#2E7D51"
CANDLESTICK_DOWN  = "#B3341F"
