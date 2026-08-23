"""
================================================================
Collective Mining — Executive Dashboard
src/data_fetcher.py

Async data ingestion via yfinance.
Handles multi-ticker downloads, caching, error recovery,
and market status detection.
================================================================
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Dict, Optional, Tuple

import pandas as pd
import yfinance as yf

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config as cfg

logger = logging.getLogger(__name__)


# ── MARKET STATUS ─────────────────────────────────────────────

def is_market_open() -> bool:
    """
    Returns True if TSX is currently open (9:30–16:00 EST, Mon–Fri).
    Uses local system time; adjust TZ if running in UTC (GitHub Actions).
    """
    from zoneinfo import ZoneInfo

    now_est = datetime.now(ZoneInfo("America/New_York"))
    if now_est.weekday() >= 5:   # Saturday or Sunday
        return False
    market_open  = now_est.replace(hour=9,  minute=30, second=0, microsecond=0)
    market_close = now_est.replace(hour=16, minute=0,  second=0, microsecond=0)
    return market_open <= now_est <= market_close


def market_status_label() -> str:
    """Human-readable market status string."""
    if is_market_open():
        return "TSX Open"
    now = datetime.now()
    if now.weekday() >= 5:
        return "Market Closed (Weekend)"
    return "TSX Closed (After Hours)"


# ── SINGLE-TICKER FETCH ───────────────────────────────────────

def fetch_history(
    ticker: str,
    period: str = cfg.PERIOD_1Y,
    interval: str = "1d",
) -> Optional[pd.DataFrame]:
    """
    Download OHLCV history for a single ticker.

    Returns a DataFrame with columns: Open, High, Low, Close, Volume
    indexed by date, or None on failure.
    """
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            logger.warning("No data returned for %s (period=%s)", ticker, period)
            return None
        df.index = pd.to_datetime(df.index)
        df.index = df.index.tz_localize(None)   # strip tz for Plotly compatibility
        return df[["Open", "High", "Low", "Close", "Volume"]]
    except Exception as exc:
        logger.error("fetch_history(%s) failed: %s", ticker, exc)
        return None


def fetch_current_quote(ticker: str) -> Optional[Dict]:
    """
    Fetch the latest fast-info snapshot for a single ticker.
    Returns a dict with: price, change_1d, change_1d_pct, volume,
    market_cap, 52w_high, 52w_low, currency.
    """
    try:
        tk = yf.Ticker(ticker)
        info = tk.fast_info
        price      = info.last_price
        prev_close = info.previous_close

        if price is None or prev_close is None:
            # Fallback: use last close from recent history
            hist = fetch_history(ticker, period="5d", interval="1d")
            if hist is None or hist.empty:
                return None
            price      = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price

        change_1d     = price - prev_close
        change_1d_pct = (change_1d / prev_close) * 100 if prev_close else 0.0

        return {
            "price":         round(float(price), 4),
            "prev_close":    round(float(prev_close), 4),
            "change_1d":     round(float(change_1d), 4),
            "change_1d_pct": round(float(change_1d_pct), 2),
            "volume":        int(getattr(info, "three_month_average_volume", 0) or 0),
            "day_volume":    int(getattr(info, "last_volume", 0) or 0),
            "market_cap":    getattr(info, "market_cap", None),
            # yfinance ≥1.1 uses year_high/year_low; older used fifty_two_week_*
            "week52_high":   getattr(info, "year_high",
                             getattr(info, "fifty_two_week_high", None)),
            "week52_low":    getattr(info, "year_low",
                             getattr(info, "fifty_two_week_low",  None)),
            "currency":      getattr(info, "currency", "CAD") or "CAD",
        }
    except Exception as exc:
        logger.error("fetch_current_quote(%s) failed: %s", ticker, exc)
        return None


# ── MULTI-TICKER BATCH FETCH ──────────────────────────────────

def fetch_all_histories(
    tickers: list[str] | None = None,
    period: str = cfg.PERIOD_1Y,
) -> Dict[str, pd.DataFrame]:
    """
    Batch download history for all tickers.
    Returns {ticker: DataFrame} for tickers that succeeded.
    """
    if tickers is None:
        tickers = cfg.ALL_TICKERS + [cfg.BENCHMARK_TICKER]

    results: Dict[str, pd.DataFrame] = {}
    for ticker in tickers:
        df = fetch_history(ticker, period=period)
        if df is not None:
            results[ticker] = df
        else:
            logger.warning("Skipping %s — no data available.", ticker)
    return results


def fetch_all_quotes(tickers: list[str] | None = None) -> Dict[str, Dict]:
    """
    Batch fetch current quotes for all tickers.
    Returns {ticker: quote_dict}.
    """
    if tickers is None:
        tickers = cfg.ALL_TICKERS

    results: Dict[str, Dict] = {}
    for ticker in tickers:
        quote = fetch_current_quote(ticker)
        if quote is not None:
            results[ticker] = quote
    return results


# ── YTD & PERIOD RETURNS ─────────────────────────────────────

def compute_period_return(df: pd.DataFrame, period: str) -> Optional[float]:
    """
    Compute a simple price return (%) for a given period label.
    period: '1d' | '1w' | '1m' | '3m' | 'ytd' | '1y'
    """
    if df is None or df.empty:
        return None

    today     = df.index[-1]
    end_price = float(df["Close"].iloc[-1])

    if period == "1d":
        start_date = today - timedelta(days=1)
    elif period == "1w":
        start_date = today - timedelta(weeks=1)
    elif period == "1m":
        start_date = today - timedelta(days=30)
    elif period == "3m":
        start_date = today - timedelta(days=91)
    elif period == "ytd":
        start_date = pd.Timestamp(date(today.year, 1, 1))
    elif period == "1y":
        start_date = today - timedelta(days=365)
    else:
        raise ValueError(f"Unknown period: {period}")

    subset = df[df.index <= start_date]
    if subset.empty:
        return None
    start_price = float(subset["Close"].iloc[-1])
    if start_price == 0:
        return None
    return round((end_price / start_price - 1) * 100, 2)


def compute_all_period_returns(
    histories: Dict[str, pd.DataFrame],
) -> Dict[str, Dict[str, Optional[float]]]:
    """
    Returns {ticker: {period: return_%}} for all tickers and periods.
    """
    periods = ["1d", "1w", "1m", "3m", "ytd", "1y"]
    result = {}
    for ticker, df in histories.items():
        result[ticker] = {p: compute_period_return(df, p) for p in periods}
    return result


# ── NORMALIZED PRICE SERIES (BASE 100) ───────────────────────

def normalize_to_base100(
    histories: Dict[str, pd.DataFrame],
    start_date: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Returns a DataFrame with each ticker's price rebased to 100
    at start_date (or at the earliest common date).
    Columns: ticker symbols. Index: dates.
    """
    series = {}
    for ticker, df in histories.items():
        if cfg.BENCHMARK_TICKER and ticker == cfg.BENCHMARK_TICKER:
            continue
        s = df["Close"].copy()
        if start_date is not None:
            s = s[s.index >= start_date]
        if s.empty:
            continue
        series[ticker] = (s / s.iloc[0]) * 100

    if not series:
        return pd.DataFrame()

    result = pd.DataFrame(series)
    result.sort_index(inplace=True)
    return result


# ── INTRADAY FETCH ───────────────────────────────────────────

def fetch_intraday(ticker: str) -> Optional[pd.DataFrame]:
    """
    Fetch today's 15-minute intraday OHLCV bars.
    Falls back gracefully outside market hours.
    """
    return fetch_history(ticker, period="1d", interval=cfg.INTRADAY_INTERVAL)
