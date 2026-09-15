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
    short_name: str           # For chart labels (max 12 chars)
    ticker_primary: str       # yfinance symbol
    ticker_display: str       # Human-readable ticker shown in UI
    exchange: str
    color: str                # Plotly-compatible hex color
    category: str = "Mid-Tier / Explorer" # "Target", "Mid-Tier / Explorer", "Major / Conglomerate"
    relevance: str = ""       # Operational relevance / region / M&A relationship
    tradingview_symbol: str = "" # e.g. "TSX:CNL"
    secondary_tickers: List[str] = None
    is_target: bool = False

    def __post_init__(self):
        if self.secondary_tickers is None:
            self.secondary_tickers = []


# CNL Multi-Market Symbols
CNL_MULTIMARKET_TICKERS = {
    "TSX": {"symbol": "CNL.TO", "display": "CNL.TO (TSX Toronto)", "tv": "TSX:CNL", "currency": "CAD"},
    "NYSE AMERICAN": {"symbol": "CNL", "display": "CNL (NYSE American USA)", "tv": "AMEX:CNL", "currency": "USD"},
    "FRANKFURT": {"symbol": "GG1.F", "display": "GG1.F (Börse Frankfurt)", "tv": "FWB:GG1", "currency": "EUR"},
}


# All companies monitored (CNL + Group A Mid-Tiers & Regional + Group B Majors & Global)
COMPANIES: List[Company] = [
    # TARGET
    Company(
        name="Collective Mining Ltd.",
        short_name="Collective",
        ticker_primary="CNL.TO",
        ticker_display="CNL (TSX / NYSE)",
        exchange="TSX / NYSE",
        color="#20A7C9",          # --cyan-500 · target accent
        category="Target",
        relevance="Guayabales & San Antonio (Caldas, Colombia)",
        tradingview_symbol="TSX:CNL",
        secondary_tickers=["CNL", "GG1.F"],
        is_target=True,
    ),
    # GROUP A: MID-TIERS & ADVANCED EXPLORERS (COLOMBIA BASIN / REGIONAL)
    Company(
        name="Aris Mining Corp.",
        short_name="Aris Mining",
        ticker_primary="ARIS.TO",
        ticker_display="ARIS (TSX / NYSE)",
        exchange="TSX",
        color="#E06D53",
        category="Mid-Tier / Explorer",
        relevance="Marmato (Caldas) & Segovia (Antioquia)",
        tradingview_symbol="TSX:ARIS",
        secondary_tickers=["ARIS"],
    ),
    Company(
        name="Mineros S.A.",
        short_name="Mineros",
        ticker_primary="MSA.TO",
        ticker_display="MSA (TSX / BVC)",
        exchange="TSX",
        color="#C9A227",
        category="Mid-Tier / Explorer",
        relevance="Bajo Cauca (Antioquia) & LatAm",
        tradingview_symbol="TSX:MSA",
    ),
    Company(
        name="Soma Gold Corp.",
        short_name="Soma Gold",
        ticker_primary="SOMA.V",
        ticker_display="SOMA (TSX-V)",
        exchange="TSX-V",
        color="#2E7D51",
        category="Mid-Tier / Explorer",
        relevance="El Bagre (Antioquia)",
        tradingview_symbol="TSXV:SOMA",
    ),
    Company(
        name="Atico Mining Corp.",
        short_name="Atico Mining",
        ticker_primary="ATY.V",
        ticker_display="ATY (TSX-V)",
        exchange="TSX-V",
        color="#B4703C",
        category="Mid-Tier / Explorer",
        relevance="El Roble (Chocó, Cu-Au)",
        tradingview_symbol="TSXV:ATY",
    ),
    Company(
        name="Cordoba Minerals Corp.",
        short_name="Cordoba Min.",
        ticker_primary="CDB.V",
        ticker_display="CDB (TSX-V)",
        exchange="TSX-V",
        color="#3B7A57",
        category="Mid-Tier / Explorer",
        relevance="San Matías / Alacrán (Córdoba)",
        tradingview_symbol="TSXV:CDB",
    ),
    Company(
        name="GoldMining Inc.",
        short_name="GoldMining",
        ticker_primary="GOLD.TO",
        ticker_display="GOLD (TSX)",
        exchange="TSX",
        color="#DAA520",
        category="Mid-Tier / Explorer",
        relevance="La Mina (Antioquia)",
        tradingview_symbol="TSX:GOLD",
    ),
    Company(
        name="Outcrop Silver & Gold",
        short_name="Outcrop",
        ticker_primary="OCG.TO",
        ticker_display="OCG (TSX)",
        exchange="TSX",
        color="#A8B0B8",
        category="Mid-Tier / Explorer",
        relevance="Santa Ana (Tolima, Ag-Au)",
        tradingview_symbol="TSX:OCG",
    ),
    Company(
        name="Orosur Mining Inc.",
        short_name="Orosur",
        ticker_primary="OMI.V",
        ticker_display="OMI (TSX-V)",
        exchange="TSX-V",
        color="#708090",
        category="Mid-Tier / Explorer",
        relevance="Anzá (Middle Cauca, Antioquia)",
        tradingview_symbol="TSXV:OMI",
    ),
    Company(
        name="Denarius Metals Corp.",
        short_name="Denarius",
        ticker_primary="DMET.NE",
        ticker_display="DMET (CBOE / NEO)",
        exchange="CBOE",
        color="#6A5ACD",
        category="Mid-Tier / Explorer",
        relevance="Zancudo & Titiribí (Antioquia)",
        tradingview_symbol="NEO:DMET",
    ),
    # GROUP B: MAJORS & GLOBAL CONGLOMERATES
    Company(
        name="Agnico Eagle Mines Ltd.",
        short_name="Agnico Eagle",
        ticker_primary="AEM",
        ticker_display="AEM (NYSE / TSX)",
        exchange="NYSE",
        color="#1E5A80",
        category="Major / Conglomerate",
        relevance="Strategic Shareholder ~15% in CNL",
        tradingview_symbol="NYSE:AEM",
        secondary_tickers=["AEM.TO"],
    ),
    Company(
        name="Zijin Mining Group",
        short_name="Zijin Mining",
        ticker_primary="ZIJMF",
        ticker_display="ZIJMF / 2899 (HKEX / OTC)",
        exchange="OTC / HKEX",
        color="#D9534F",
        category="Major / Conglomerate",
        relevance="Operator of Buriticá (ex-Continental Gold)",
        tradingview_symbol="OTC:ZIJMF",
        secondary_tickers=["2899.HK"],
    ),
    Company(
        name="AngloGold Ashanti plc",
        short_name="AngloGold",
        ticker_primary="AU",
        ticker_display="AU (NYSE)",
        exchange="NYSE",
        color="#F0AD4E",
        category="Major / Conglomerate",
        relevance="Quebradona & La Colosa (Colombia)",
        tradingview_symbol="NYSE:AU",
    ),
    Company(
        name="Lundin Mining Corp.",
        short_name="Lundin Mining",
        ticker_primary="LUN.TO",
        ticker_display="LUN (TSX)",
        exchange="TSX",
        color="#5BC0DE",
        category="Major / Conglomerate",
        relevance="Andean Cu-Au Porphyries",
        tradingview_symbol="TSX:LUN",
    ),
    Company(
        name="Newmont Corporation",
        short_name="Newmont",
        ticker_primary="NEM",
        ticker_display="NEM (NYSE)",
        exchange="NYSE",
        color="#4A90E2",
        category="Major / Conglomerate",
        relevance="Global Precious Metals Leader",
        tradingview_symbol="NYSE:NEM",
    ),
    Company(
        name="Barrick Gold Corp.",
        short_name="Barrick Gold",
        ticker_primary="GOLD",
        ticker_display="GOLD (NYSE)",
        exchange="NYSE",
        color="#E67E22",
        category="Major / Conglomerate",
        relevance="Tier-1 Global Gold/Copper Producer",
        tradingview_symbol="NYSE:GOLD",
    ),
]

# Quick lookups
TICKER_MAP: Dict[str, Company] = {c.ticker_primary: c for c in COMPANIES}
TARGET: Company = next(c for c in COMPANIES if c.is_target)
ALL_TICKERS: List[str] = [c.ticker_primary for c in COMPANIES]

# Reference Indices
BENCHMARK_INDICES: Dict[str, Dict] = {
    "^IXIC": {"name": "NASDAQ Composite", "display": "NASDAQ (^IXIC)", "color": "#00A8E8"},
    "GDXJ":  {"name": "VanEck Junior Gold Miners ETF", "display": "GDXJ (Junior Gold)", "color": "#FF9900"},
    "GDX":   {"name": "VanEck Gold Miners ETF", "display": "GDX (Gold Miners)", "color": "#FFCC00"},
    "XEG.TO": {"name": "iShares TSX Energy", "display": "XEG (TSX)", "color": "#5C6B73"},
}

BENCHMARK_TICKER  = "^IXIC"
BENCHMARK_DISPLAY = "NASDAQ (^IXIC)"

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
