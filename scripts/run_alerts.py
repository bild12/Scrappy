"""
================================================================
Collective Mining — Executive Dashboard
scripts/run_alerts.py

Standalone script called by GitHub Actions to:
  1. Fetch all market data
  2. Compute metrics
  3. Detect alert signals
  4. Dispatch to Teams + Email
  5. Print structured summary to stdout (visible in Actions log)

Usage:
  python scripts/run_alerts.py [--force] [--mode eod|open]
================================================================
"""

import argparse
import json
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import config as cfg
from src.data_fetcher import fetch_all_histories, fetch_all_quotes
from src.metrics import build_all_metrics, detect_alerts
from src.alerts import dispatch_alerts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_alerts")


def print_summary(metrics: dict, alerts: list):
    """Print a clean GitHub Actions log summary."""
    target_tk = cfg.TARGET.ticker_primary
    m = metrics.get(target_tk, {})

    price   = m.get("price", "—")
    chg     = m.get("change_1d_pct")
    ret_ytd = (m.get("returns") or {}).get("ytd")
    rsi     = m.get("rsi", "—")
    beta    = m.get("beta", "—")

    print("\n" + "═" * 60)
    print("  Collective Mining Ltd. — Market Intelligence Report")
    print("═" * 60)
    print(f"  Ticker  : {cfg.TARGET.ticker_display}")
    print(f"  Price   : ${price:.3f} CAD" if isinstance(price, float) else f"  Price   : {price}")
    print(f"  1D Chg  : {chg:+.2f}%" if chg is not None else "  1D Chg  : —")
    print(f"  YTD Rtn : {ret_ytd:+.2f}%" if ret_ytd is not None else "  YTD Rtn : —")
    print(f"  RSI     : {rsi}")
    print(f"  Beta    : {beta}")
    print()

    print("  Peers:")
    print(f"  {'Ticker':<15} {'Price':>8}  {'1D':>7}  {'YTD':>7}")
    print("  " + "-" * 42)
    for company in cfg.COMPANIES:
        tk  = company.ticker_primary
        m2  = metrics.get(tk, {})
        p   = m2.get("price")
        c   = m2.get("change_1d_pct")
        r   = (m2.get("returns") or {}).get("ytd")
        star = "⭐" if company.is_target else "  "
        p_str = f"${p:.3f}" if p is not None else "   —  "
        c_str = f"{c:+.2f}%" if c is not None else "   —  "
        r_str = f"{r:+.2f}%" if r is not None else "   —  "
        print(f"  {star} {company.ticker_display:<13} {p_str:>8}  {c_str:>7}  {r_str:>7}")

    print()
    print(f"  🚨 Alerts triggered: {len(alerts)}")
    for a in alerts:
        sev_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(a["severity"], "⚪")
        print(f"     {sev_icon} [{a['display']}] {a['message']}")
    print("═" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="CNL Alert Runner")
    parser.add_argument("--force", action="store_true",
                        help="Send notifications even if no alerts triggered")
    parser.add_argument("--mode", choices=["open", "eod", "check"], default="check",
                        help="open=market open report, eod=end of day, check=alerts only")
    args = parser.parse_args()

    logger.info("Starting CNL Alert Runner | mode=%s force=%s", args.mode, args.force)

    # Fetch data
    logger.info("Fetching market data for %d tickers…", len(cfg.ALL_TICKERS))
    period    = cfg.PERIOD_1Y if args.mode == "eod" else cfg.PERIOD_3M
    histories = fetch_all_histories(cfg.ALL_TICKERS + [cfg.BENCHMARK_TICKER], period=period)
    quotes    = fetch_all_quotes()

    logger.info("Computing metrics…")
    metrics = build_all_metrics(histories, quotes)
    alerts  = detect_alerts(metrics)

    logger.info("Alerts detected: %d", len(alerts))

    # Print summary
    print_summary(metrics, alerts)

    # Dispatch
    should_send = args.force or len(alerts) > 0 or args.mode in ("open", "eod")
    if should_send:
        logger.info("Dispatching notifications…")
        results = dispatch_alerts(alerts, metrics, force=(args.force or args.mode in ("open", "eod")))
        logger.info("Dispatch results: %s", results)
        if any(results.values()):
            print("  ✅ Notifications sent successfully.")
        else:
            print("  ⚠️  No notifications sent (check credentials in secrets).")
    else:
        logger.info("No alerts to dispatch.")

    # Exit code: 0 always (don't fail CI on missing alerts)
    sys.exit(0)


if __name__ == "__main__":
    main()
