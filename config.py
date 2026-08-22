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
        color="#FFD700",          # Gold — brand color
        is_target=True,
    ),
    Company(
        name="Faraday Copper Corp.",
        short_name="Faraday",
        ticker_primary="FDY.TO",
        ticker_display="FDY (TSX)",
        exchange="TSX",
        color="#00B4D8",          # Blue
    ),
    Company(
        name="Marimaca Copper Corp.",
        short_name="Marimaca",
        ticker_primary="MARI.TO",
        ticker_display="MARI (TSX)",
        exchange="TSX",
        color="#06D6A0",          # Teal
    ),
    Company(
        name="Lumina Metals Corp.",
        short_name="Lumina",
        ticker_primary="LMCU.TO",
        ticker_display="LMCU (TSX)",
        exchange="TSX",
        color="#FF6B35",          # Orange
    ),
    Company(
        name="NorthIsle Copper and Gold",
        short_name="NorthIsle",
        ticker_primary="NCX.V",
        ticker_display="NCX (TSX-V)",
        exchange="TSX-V",
        color="#C77DFF",          # Purple
    ),
    Company(
        name="Osisko Metals Inc.",
        short_name="Osisko Met.",
        ticker_primary="OM.TO",
        ticker_display="OM (TSX)",
        exchange="TSX",
        color="#F72585",          # Magenta
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

PAGE_CONFIG = {
    "page_title": "CNL Executive Dashboard",
    "page_icon": "⛏️",
    "layout": "wide",
    "initial_sidebar_state": "collapsed",
}

# ── CHART / THEME TOKENS ─────────────────────────────────────

CHART_BG_COLOR    = "#0D1117"
CHART_PAPER_COLOR = "#161B22"
CHART_GRID_COLOR  = "#21262D"
CHART_FONT_COLOR  = "#E6EDF3"
CHART_POSITIVE    = "#00C853"
CHART_NEGATIVE    = "#FF1744"
CHART_NEUTRAL     = "#8B949E"
CHART_ACCENT      = "#FFD700"

CANDLESTICK_UP    = "#00C853"
CANDLESTICK_DOWN  = "#FF1744"
