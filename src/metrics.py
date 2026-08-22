"""
================================================================
Collective Mining — Executive Dashboard
src/metrics.py

Executive-grade financial metrics:
  - Price returns (1D / 1W / 1M / 3M / YTD / 1Y)
  - Beta (rolling 60-day vs benchmark)
  - Volume analysis (relative volume, spikes)
  - Technical indicators: RSI, Bollinger Bands, VWAP, MA
  - Support / Resistance levels (52-week + Pivot Points)
  - Alert signal detection
================================================================
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config as cfg

logger = logging.getLogger(__name__)


# ── MOVING AVERAGES ──────────────────────────────────────────

def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds MA_short, MA_medium, MA_long columns to a OHLCV DataFrame.
    Uses simple moving average (SMA) on Close price.
    """
    df = df.copy()
    df[f"MA{cfg.MA_SHORT}"]  = df["Close"].rolling(cfg.MA_SHORT).mean()
    df[f"MA{cfg.MA_MEDIUM}"] = df["Close"].rolling(cfg.MA_MEDIUM).mean()
    df[f"MA{cfg.MA_LONG}"]   = df["Close"].rolling(cfg.MA_LONG).mean()
    return df


def detect_ma_crossover(df: pd.DataFrame) -> Optional[str]:
    """
    Detect MA20/MA50 crossover on the last two rows.
    Returns 'bullish', 'bearish', or None.
    """
    df = add_moving_averages(df)
    col_short  = f"MA{cfg.MA_SHORT}"
    col_medium = f"MA{cfg.MA_MEDIUM}"
    tail = df[[col_short, col_medium]].dropna().tail(2)
    if len(tail) < 2:
        return None
    prev_short, prev_medium = tail.iloc[-2][col_short], tail.iloc[-2][col_medium]
    curr_short, curr_medium = tail.iloc[-1][col_short], tail.iloc[-1][col_medium]
    if prev_short <= prev_medium and curr_short > curr_medium:
        return "bullish"
    if prev_short >= prev_medium and curr_short < curr_medium:
        return "bearish"
    return None


# ── RSI ──────────────────────────────────────────────────────

def compute_rsi(df: pd.DataFrame, period: int = cfg.RSI_PERIOD) -> pd.Series:
    """
    Wilder's RSI on the Close column.
    Returns a Series indexed like df.
    """
    delta  = df["Close"].diff()
    gain   = delta.clip(lower=0)
    loss   = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs  = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.rename("RSI")


# ── BOLLINGER BANDS ──────────────────────────────────────────

def compute_bollinger_bands(
    df: pd.DataFrame,
    period: int = cfg.BB_PERIOD,
    std: float  = cfg.BB_STD,
) -> pd.DataFrame:
    """
    Adds BB_Mid, BB_Upper, BB_Lower columns to the DataFrame.
    """
    df = df.copy()
    df["BB_Mid"]   = df["Close"].rolling(period).mean()
    rolling_std    = df["Close"].rolling(period).std()
    df["BB_Upper"] = df["BB_Mid"] + std * rolling_std
    df["BB_Lower"] = df["BB_Mid"] - std * rolling_std
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / df["BB_Mid"]   # normalized width
    return df


# ── VWAP (intraday) ───────────────────────────────────────────

def compute_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Volume-Weighted Average Price.
    Meaningful only for intraday data (15m bars of a single trading day).
    """
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    cumulative_tp_vol = (typical_price * df["Volume"]).cumsum()
    cumulative_vol    = df["Volume"].cumsum()
    vwap = cumulative_tp_vol / cumulative_vol.replace(0, np.nan)
    return vwap.rename("VWAP")


# ── VOLUME METRICS ───────────────────────────────────────────

def volume_metrics(df: pd.DataFrame) -> Dict:
    """
    Returns relative volume stats for the latest session.
    """
    if df is None or len(df) < 2:
        return {}
    vol_today  = float(df["Volume"].iloc[-1])
    avg_20d    = float(df["Volume"].tail(21).iloc[:-1].mean())  # exclude today
    rel_vol    = (vol_today / avg_20d) if avg_20d > 0 else 0.0
    avg_3m     = float(df["Volume"].tail(63).mean())
    return {
        "vol_today":    int(vol_today),
        "avg_20d":      int(avg_20d),
        "avg_3m":       int(avg_3m),
        "rel_vol_20d":  round(rel_vol, 2),
        "is_spike":     rel_vol >= cfg.VOLUME_ALERT_MULTIPLIER,
    }


# ── SUPPORT & RESISTANCE ─────────────────────────────────────

def support_resistance(df: pd.DataFrame) -> Dict:
    """
    Key price levels:
    - 52-week high / low
    - Standard Pivot Points (Classic method, based on last complete session)
    - Distance of current price from 52-week high (drawdown %)
    """
    if df is None or df.empty:
        return {}

    year_data = df.tail(252)     # ~1 trading year
    w52_high  = float(year_data["High"].max())
    w52_low   = float(year_data["Low"].min())
    curr      = float(df["Close"].iloc[-1])

    # Classic Pivot Points from the LAST COMPLETE session
    prev = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]
    H, L, C = float(prev["High"]), float(prev["Low"]), float(prev["Close"])
    pivot = (H + L + C) / 3
    r1 = (2 * pivot) - L
    s1 = (2 * pivot) - H
    r2 = pivot + (H - L)
    s2 = pivot - (H - L)

    dist_from_52wh = round((curr / w52_high - 1) * 100, 2)
    dist_from_52wl = round((curr / w52_low  - 1) * 100, 2)

    return {
        "w52_high":        round(w52_high, 4),
        "w52_low":         round(w52_low,  4),
        "dist_52wh_pct":   dist_from_52wh,
        "dist_52wl_pct":   dist_from_52wl,
        "pivot":           round(pivot, 4),
        "resistance_1":    round(r1, 4),
        "resistance_2":    round(r2, 4),
        "support_1":       round(s1, 4),
        "support_2":       round(s2, 4),
    }


# ── BETA ─────────────────────────────────────────────────────

def compute_beta(
    stock_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    window: int = cfg.BETA_PERIOD_DAYS,
) -> Optional[float]:
    """
    Rolling Beta of stock vs. benchmark over the last `window` trading days.
    Beta = Cov(stock_returns, bench_returns) / Var(bench_returns)
    """
    if stock_df is None or benchmark_df is None:
        return None
    stock_ret = stock_df["Close"].pct_change().dropna()
    bench_ret = benchmark_df["Close"].pct_change().dropna()
    combined  = pd.DataFrame({"stock": stock_ret, "bench": bench_ret}).dropna().tail(window)
    if len(combined) < 10:
        return None
    cov_matrix = np.cov(combined["stock"], combined["bench"])
    var_bench  = cov_matrix[1, 1]
    if var_bench == 0:
        return None
    return round(float(cov_matrix[0, 1] / var_bench), 3)


# ── FULL METRICS BUNDLE ───────────────────────────────────────

def build_company_metrics(
    ticker: str,
    df: pd.DataFrame,
    benchmark_df: Optional[pd.DataFrame],
    quote: Optional[Dict],
) -> Dict:
    """
    Assembles the full metrics dictionary for a single company.
    Used by the dashboard and the alert engine.
    """
    if df is None or df.empty:
        return {"ticker": ticker, "error": "No data"}

    from src.data_fetcher import compute_period_return

    rsi_series = compute_rsi(df)
    bb_df      = compute_bollinger_bands(df)
    vol_stats  = volume_metrics(df)
    sr         = support_resistance(df)
    ma_cross   = detect_ma_crossover(df)
    beta       = compute_beta(df, benchmark_df) if benchmark_df is not None else None

    latest_rsi   = float(rsi_series.iloc[-1]) if not rsi_series.empty else None
    latest_close = float(df["Close"].iloc[-1])
    latest_bb_u  = float(bb_df["BB_Upper"].iloc[-1]) if "BB_Upper" in bb_df else None
    latest_bb_l  = float(bb_df["BB_Lower"].iloc[-1]) if "BB_Lower" in bb_df else None

    returns = {p: compute_period_return(df, p) for p in ["1d", "1w", "1m", "3m", "ytd", "1y"]}

    return {
        "ticker":        ticker,
        "price":         quote.get("price", latest_close) if quote else latest_close,
        "currency":      quote.get("currency", "CAD") if quote else "CAD",
        "change_1d_pct": quote.get("change_1d_pct", returns.get("1d")) if quote else returns.get("1d"),
        "returns":       returns,
        "beta":          beta,
        "rsi":           round(latest_rsi, 1) if latest_rsi is not None else None,
        "rsi_signal":    _rsi_signal(latest_rsi),
        "bb_upper":      latest_bb_u,
        "bb_lower":      latest_bb_l,
        "volume":        vol_stats,
        "support_resistance": sr,
        "ma_crossover":  ma_cross,
        "week52_high":   sr.get("w52_high"),
        "week52_low":    sr.get("w52_low"),
    }


def build_all_metrics(
    histories: Dict[str, pd.DataFrame],
    quotes: Dict[str, Dict],
) -> Dict[str, Dict]:
    """
    Build metrics for all companies in one pass.
    Returns {ticker: metrics_dict}.
    """
    benchmark_df = histories.get(cfg.BENCHMARK_TICKER)
    result = {}
    for company in cfg.COMPANIES:
        tk = company.ticker_primary
        df = histories.get(tk)
        q  = quotes.get(tk)
        result[tk] = build_company_metrics(tk, df, benchmark_df, q)
    return result


# ── ALERT SIGNAL DETECTION ───────────────────────────────────

def _rsi_signal(rsi: Optional[float]) -> Optional[str]:
    if rsi is None:
        return None
    if rsi >= cfg.RSI_OVERBOUGHT:
        return "overbought"
    if rsi <= cfg.RSI_OVERSOLD:
        return "oversold"
    return "neutral"


def detect_alerts(metrics: Dict[str, Dict]) -> List[Dict]:
    """
    Scans all tickers' metrics and returns a list of triggered alert dicts.
    Each alert: {ticker, company_name, type, severity, message, value}
    Severity: 'info' | 'warning' | 'critical'
    """
    alerts: List[Dict] = []

    for tk, m in metrics.items():
        if "error" in m:
            continue

        company = cfg.TICKER_MAP.get(tk)
        name    = company.name if company else tk
        display = company.ticker_display if company else tk

        # --- Price change alert ---
        chg = m.get("change_1d_pct")
        if chg is not None and abs(chg) >= cfg.PRICE_ALERT_THRESHOLD:
            severity = "critical" if abs(chg) >= cfg.PRICE_ALERT_THRESHOLD * 1.5 else "warning"
            direction = "▲" if chg > 0 else "▼"
            alerts.append({
                "ticker":       tk,
                "display":      display,
                "company_name": name,
                "type":         "price_change",
                "severity":     severity,
                "value":        chg,
                "message":      f"{direction} {abs(chg):.1f}% price move — {m['price']:.3f} {m['currency']}",
            })

        # --- Volume spike alert ---
        vol = m.get("volume", {})
        if vol.get("is_spike"):
            rv = vol.get("rel_vol_20d", 0)
            alerts.append({
                "ticker":       tk,
                "display":      display,
                "company_name": name,
                "type":         "volume_spike",
                "severity":     "warning",
                "value":        rv,
                "message":      f"Volume spike: {rv:.1f}× the 20-day average",
            })

        # --- RSI extremes ---
        rsi_sig = m.get("rsi_signal")
        if rsi_sig in ("overbought", "oversold"):
            alerts.append({
                "ticker":       tk,
                "display":      display,
                "company_name": name,
                "type":         f"rsi_{rsi_sig}",
                "severity":     "info",
                "value":        m.get("rsi"),
                "message":      f"RSI {m['rsi']:.0f} — {rsi_sig.title()} condition",
            })

        # --- MA Crossover ---
        cross = m.get("ma_crossover")
        if cross:
            alerts.append({
                "ticker":       tk,
                "display":      display,
                "company_name": name,
                "type":         f"ma_crossover_{cross}",
                "severity":     "info",
                "value":        cross,
                "message":      f"MA{cfg.MA_SHORT}/MA{cfg.MA_MEDIUM} {cross.title()} crossover detected",
            })

        # --- 52-week high/low ---
        price  = m.get("price", 0)
        w52h   = m.get("week52_high")
        w52l   = m.get("week52_low")
        if w52h and price >= w52h * 0.995:
            alerts.append({
                "ticker":       tk,
                "display":      display,
                "company_name": name,
                "type":         "new_52w_high",
                "severity":     "critical",
                "value":        price,
                "message":      f"Near/at 52-week HIGH: {price:.3f} (high: {w52h:.3f})",
            })
        elif w52l and price <= w52l * 1.005:
            alerts.append({
                "ticker":       tk,
                "display":      display,
                "company_name": name,
                "type":         "new_52w_low",
                "severity":     "critical",
                "value":        price,
                "message":      f"Near/at 52-week LOW: {price:.3f} (low: {w52l:.3f})",
            })

    # Sort: CNL alerts first, then by severity
    sev_order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: (0 if a["ticker"] == cfg.TARGET.ticker_primary else 1,
                               sev_order.get(a["severity"], 9)))
    return alerts
