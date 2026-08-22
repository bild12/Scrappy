"""
================================================================
Collective Mining — Executive Dashboard
src/alerts.py

Notification engine — Microsoft Teams + Email (Resend API)
Channels: NO Telegram, NO Slack per company policy.

Features:
  - Teams Adaptive Card (color-coded, structured)
  - HTML email report (Resend API)
  - Plain-text email fallback
  - Alert formatting with severity levels
================================================================
"""

from __future__ import annotations

import json
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import requests

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config as cfg

logger = logging.getLogger(__name__)

EST = ZoneInfo("America/New_York")


# ── FORMATTING HELPERS ────────────────────────────────────────

def _now_est() -> str:
    return datetime.now(EST).strftime("%I:%M %p EST  |  %b %d, %Y")


def _severity_color(severity: str) -> str:
    """Teams Adaptive Card color token."""
    return {"critical": "Attention", "warning": "Warning", "info": "Accent"}.get(severity, "Default")


def _pct_arrow(value: float) -> str:
    return f"▲ {value:+.2f}%" if value >= 0 else f"▼ {value:.2f}%"


def _format_volume(vol: int) -> str:
    if vol >= 1_000_000:
        return f"{vol / 1_000_000:.1f}M"
    if vol >= 1_000:
        return f"{vol / 1_000:.0f}K"
    return str(vol)


# ── MICROSOFT TEAMS ADAPTIVE CARD ────────────────────────────

def build_teams_card(alerts: List[Dict], metrics: Dict[str, Dict]) -> Dict:
    """
    Builds a full Teams Adaptive Card payload for all triggered alerts.
    Groups CNL alerts at the top. Includes a summary metrics table.
    """
    target_tk = cfg.TARGET.ticker_primary
    target_m  = metrics.get(target_tk, {})

    # Header facts (CNL snapshot)
    price     = target_m.get("price", "N/A")
    chg_pct   = target_m.get("change_1d_pct", 0) or 0
    rsi       = target_m.get("rsi", "—")
    ret_ytd   = (target_m.get("returns") or {}).get("ytd", None)
    ret_1m    = (target_m.get("returns") or {}).get("1m",  None)
    beta      = target_m.get("beta", "—")
    vol       = (target_m.get("volume") or {}).get("vol_today", 0)
    rel_vol   = (target_m.get("volume") or {}).get("rel_vol_20d", 0)

    chg_color = "Good" if chg_pct >= 0 else "Attention"
    chg_str   = _pct_arrow(chg_pct)

    # Build alert fact rows
    alert_facts = []
    for a in alerts[:10]:   # max 10 alerts per card
        icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(a["severity"], "⚪")
        alert_facts.append({
            "title": f"{icon} {a['display']}",
            "value": a["message"],
        })

    card_body = [
        # Title
        {
            "type": "TextBlock",
            "text": "⛏️ Collective Mining — Market Intelligence Alert",
            "size": "Large",
            "weight": "Bolder",
            "color": "Warning",
            "wrap": True,
        },
        {
            "type": "TextBlock",
            "text": _now_est(),
            "isSubtle": True,
            "size": "Small",
            "spacing": "None",
        },
        {"type": "Separator"},
        # CNL snapshot
        {
            "type": "TextBlock",
            "text": f"CNL (TSX) Snapshot",
            "weight": "Bolder",
            "color": "Warning",
            "spacing": "Medium",
        },
        {
            "type": "FactSet",
            "facts": [
                {"title": "Price",      "value": f"${price:.3f} CAD"},
                {"title": "1D Change",  "value": chg_str},
                {"title": "YTD Return", "value": f"{ret_ytd:+.1f}%" if ret_ytd is not None else "—"},
                {"title": "1M Return",  "value": f"{ret_1m:+.1f}%"  if ret_1m  is not None else "—"},
                {"title": "RSI",        "value": f"{rsi}" if rsi else "—"},
                {"title": "Beta (60d)", "value": f"{beta}" if beta else "—"},
                {"title": "Volume",     "value": f"{_format_volume(vol)} ({rel_vol:.1f}× avg)"},
            ],
        },
    ]

    # Add alerts section if any
    if alerts:
        card_body += [
            {"type": "Separator"},
            {
                "type": "TextBlock",
                "text": f"🚨 {len(alerts)} Alert(s) Triggered",
                "weight": "Bolder",
                "color": "Attention" if any(a["severity"] == "critical" for a in alerts) else "Warning",
                "spacing": "Medium",
            },
            {
                "type": "FactSet",
                "facts": alert_facts,
            },
        ]
    else:
        card_body.append({
            "type": "TextBlock",
            "text": "✅ No alerts triggered — all thresholds within normal range.",
            "color": "Good",
            "spacing": "Medium",
        })

    # Competitor mini-table (TextBlock column sets)
    card_body.append({"type": "Separator"})
    card_body.append({
        "type": "TextBlock",
        "text": "Peer Performance",
        "weight": "Bolder",
        "spacing": "Medium",
    })

    for company in cfg.COMPANIES:
        tk = company.ticker_primary
        m  = metrics.get(tk, {})
        chg = m.get("change_1d_pct", None)
        p   = m.get("price", None)
        chg_str_peer = f"{chg:+.2f}%" if chg is not None else "—"
        p_str        = f"${p:.3f}"    if p  is not None else "—"
        star = "⭐ " if company.is_target else ""
        card_body.append({
            "type": "TextBlock",
            "text": f"{star}{company.short_name} ({company.ticker_display})  •  {p_str}  •  {chg_str_peer}",
            "size": "Small",
            "wrap": False,
            "spacing": "None",
        })

    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": card_body,
                },
            }
        ],
    }
    return payload


def send_teams_alert(
    alerts: List[Dict],
    metrics: Dict[str, Dict],
    webhook_url: str = "",
) -> bool:
    """
    POST an Adaptive Card to a Teams channel Incoming Webhook.
    Returns True on success.
    """
    url = webhook_url or cfg.TEAMS_WEBHOOK_URL
    if not url:
        logger.warning("TEAMS_WEBHOOK_URL not set — skipping Teams notification.")
        return False

    payload = build_teams_card(alerts, metrics)
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code in (200, 202):
            logger.info("Teams alert sent successfully.")
            return True
        logger.error("Teams webhook error %s: %s", resp.status_code, resp.text[:200])
        return False
    except requests.RequestException as exc:
        logger.error("Teams request failed: %s", exc)
        return False


# ── EMAIL — HTML TEMPLATE ────────────────────────────────────

def build_html_email(alerts: List[Dict], metrics: Dict[str, Dict]) -> str:
    """
    Renders a premium HTML email with CNL metrics + competitor table.
    Compatible with major email clients (inline CSS only).
    """
    target_tk = cfg.TARGET.ticker_primary
    target_m  = metrics.get(target_tk, {})

    price   = target_m.get("price", "—")
    chg_pct = target_m.get("change_1d_pct", 0) or 0
    rsi     = target_m.get("rsi", "—")
    ret_ytd = (target_m.get("returns") or {}).get("ytd", None)
    ret_1m  = (target_m.get("returns") or {}).get("1m",  None)
    beta    = target_m.get("beta", "—")
    vol     = (target_m.get("volume") or {}).get("vol_today", 0)
    rel_vol = (target_m.get("volume") or {}).get("rel_vol_20d", 0)

    chg_color = "#00C853" if chg_pct >= 0 else "#FF1744"
    chg_str   = f"{'▲' if chg_pct >= 0 else '▼'} {abs(chg_pct):.2f}%"

    # Alerts rows
    alert_rows_html = ""
    if alerts:
        for a in alerts:
            sev_colors = {"critical": "#FF1744", "warning": "#FFD600", "info": "#00B4D8"}
            dot_color  = sev_colors.get(a["severity"], "#8B949E")
            alert_rows_html += f"""
            <tr>
              <td style="padding:6px 12px;border-bottom:1px solid #21262D;">
                <span style="display:inline-block;width:10px;height:10px;border-radius:50%;
                             background:{dot_color};margin-right:8px;"></span>
                <b style="color:#E6EDF3;">{a['display']}</b>
              </td>
              <td style="padding:6px 12px;border-bottom:1px solid #21262D;color:#C9D1D9;">{a['message']}</td>
            </tr>"""
    else:
        alert_rows_html = """
        <tr><td colspan="2" style="padding:12px;text-align:center;color:#00C853;">
          ✅ No alerts triggered — all thresholds within normal range.
        </td></tr>"""

    # Peer table rows
    peer_rows_html = ""
    for company in cfg.COMPANIES:
        tk  = company.ticker_primary
        m   = metrics.get(tk, {})
        chg = m.get("change_1d_pct", None)
        p   = m.get("price", None)
        ret = (m.get("returns") or {}).get("ytd", None)
        c_color   = "#00C853" if (chg or 0) >= 0 else "#FF1744"
        row_bg    = "#1C2128" if company.is_target else "#161B22"
        star      = "⭐ " if company.is_target else ""
        peer_rows_html += f"""
        <tr style="background:{row_bg};">
          <td style="padding:8px 12px;border-bottom:1px solid #21262D;color:{company.color};font-weight:bold;">
            {star}{company.ticker_display}
          </td>
          <td style="padding:8px 12px;border-bottom:1px solid #21262D;color:#E6EDF3;">
            {company.short_name}
          </td>
          <td style="padding:8px 12px;border-bottom:1px solid #21262D;color:#E6EDF3;text-align:right;">
            {"${:.3f}".format(p) if p is not None else "—"}
          </td>
          <td style="padding:8px 12px;border-bottom:1px solid #21262D;color:{c_color};text-align:right;font-weight:bold;">
            {"▲" if (chg or 0) >= 0 else "▼"} {abs(chg):.2f}% if chg is not None else "—"
          </td>
          <td style="padding:8px 12px;border-bottom:1px solid #21262D;color:{c_color};text-align:right;">
            {"{:+.1f}%".format(ret) if ret is not None else "—"}
          </td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CNL Market Intelligence Alert</title></head>
<body style="margin:0;padding:0;background:#0D1117;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0D1117;padding:24px 0;">
  <tr><td align="center">
    <table width="680" cellpadding="0" cellspacing="0" style="background:#161B22;border-radius:12px;
           border:1px solid #21262D;overflow:hidden;max-width:100%;">

      <!-- Header -->
      <tr>
        <td style="background:linear-gradient(135deg,#1C2128 0%,#0D1117 100%);
                   padding:28px 32px;border-bottom:2px solid #FFD700;">
          <h1 style="margin:0;color:#FFD700;font-size:20px;font-weight:700;letter-spacing:0.5px;">
            ⛏️ Collective Mining Ltd.
          </h1>
          <p style="margin:4px 0 0;color:#8B949E;font-size:13px;">
            Market Intelligence Alert  ·  {_now_est()}
          </p>
        </td>
      </tr>

      <!-- CNL KPI Bar -->
      <tr>
        <td style="padding:24px 32px;background:#1C2128;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="text-align:center;padding:12px;">
                <div style="color:#8B949E;font-size:11px;text-transform:uppercase;letter-spacing:1px;">Price</div>
                <div style="color:#E6EDF3;font-size:24px;font-weight:700;margin-top:4px;">${price:.3f}</div>
                <div style="color:#8B949E;font-size:11px;">CAD</div>
              </td>
              <td style="text-align:center;padding:12px;border-left:1px solid #21262D;">
                <div style="color:#8B949E;font-size:11px;text-transform:uppercase;letter-spacing:1px;">1D Change</div>
                <div style="color:{chg_color};font-size:24px;font-weight:700;margin-top:4px;">{chg_str}</div>
                <div style="color:#8B949E;font-size:11px;">vs. Yesterday</div>
              </td>
              <td style="text-align:center;padding:12px;border-left:1px solid #21262D;">
                <div style="color:#8B949E;font-size:11px;text-transform:uppercase;letter-spacing:1px;">YTD Return</div>
                <div style="color:{"#00C853" if (ret_ytd or 0) >= 0 else "#FF1744"};font-size:24px;font-weight:700;margin-top:4px;">
                  {"{:+.1f}%".format(ret_ytd) if ret_ytd is not None else "—"}
                </div>
                <div style="color:#8B949E;font-size:11px;">Year-to-Date</div>
              </td>
              <td style="text-align:center;padding:12px;border-left:1px solid #21262D;">
                <div style="color:#8B949E;font-size:11px;text-transform:uppercase;letter-spacing:1px;">RSI ({cfg.RSI_PERIOD}d)</div>
                <div style="color:#FFD700;font-size:24px;font-weight:700;margin-top:4px;">{rsi}</div>
                <div style="color:#8B949E;font-size:11px;">Beta: {beta}</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- Alerts Table -->
      <tr>
        <td style="padding:0 32px 24px;">
          <h2 style="margin:20px 0 12px;color:#E6EDF3;font-size:14px;font-weight:600;
                     text-transform:uppercase;letter-spacing:1px;">
            🚨 Triggered Alerts
          </h2>
          <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;
                 border:1px solid #21262D;border-radius:8px;overflow:hidden;">
            <thead>
              <tr style="background:#21262D;">
                <th style="padding:8px 12px;text-align:left;color:#8B949E;font-size:12px;font-weight:600;">Ticker</th>
                <th style="padding:8px 12px;text-align:left;color:#8B949E;font-size:12px;font-weight:600;">Signal</th>
              </tr>
            </thead>
            <tbody>{alert_rows_html}</tbody>
          </table>
        </td>
      </tr>

      <!-- Peer Comparison Table -->
      <tr>
        <td style="padding:0 32px 32px;">
          <h2 style="margin:0 0 12px;color:#E6EDF3;font-size:14px;font-weight:600;
                     text-transform:uppercase;letter-spacing:1px;">
            📊 Peer Performance
          </h2>
          <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;
                 border:1px solid #21262D;border-radius:8px;overflow:hidden;">
            <thead>
              <tr style="background:#21262D;">
                <th style="padding:8px 12px;text-align:left;color:#8B949E;font-size:12px;">Ticker</th>
                <th style="padding:8px 12px;text-align:left;color:#8B949E;font-size:12px;">Company</th>
                <th style="padding:8px 12px;text-align:right;color:#8B949E;font-size:12px;">Price</th>
                <th style="padding:8px 12px;text-align:right;color:#8B949E;font-size:12px;">1D Chg</th>
                <th style="padding:8px 12px;text-align:right;color:#8B949E;font-size:12px;">YTD</th>
              </tr>
            </thead>
            <tbody>{peer_rows_html}</tbody>
          </table>
        </td>
      </tr>

      <!-- Footer -->
      <tr>
        <td style="background:#0D1117;padding:16px 32px;border-top:1px solid #21262D;">
          <p style="margin:0;color:#484F58;font-size:11px;text-align:center;">
            Collective Mining Ltd. · Executive Market Intelligence System ·
            Data sourced from Yahoo Finance (15-min delay) ·
            This is an automated alert — do not reply to this email.
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""
    return html


# ── EMAIL SEND — RESEND API ──────────────────────────────────

def send_email_alert(
    alerts: List[Dict],
    metrics: Dict[str, Dict],
    subject: Optional[str] = None,
) -> bool:
    """
    Send HTML email report via Resend API.
    Returns True on success.
    Docs: https://resend.com/docs/api-reference/emails/send-email
    """
    api_key = cfg.RESEND_API_KEY
    if not api_key:
        logger.warning("RESEND_API_KEY not set — skipping email notification.")
        return False

    if not cfg.ALERT_EMAIL_TO:
        logger.warning("ALERT_EMAIL_TO not configured — skipping email.")
        return False

    n_alerts   = len(alerts)
    has_crit   = any(a["severity"] == "critical" for a in alerts)
    target_chg = metrics.get(cfg.TARGET.ticker_primary, {}).get("change_1d_pct", 0) or 0
    chg_arrow  = "▲" if target_chg >= 0 else "▼"

    if subject is None:
        if n_alerts > 0:
            prefix = "🔴 CRITICAL" if has_crit else "🟡 ALERT"
            subject = f"{prefix} — CNL {chg_arrow}{abs(target_chg):.1f}% | {n_alerts} signal(s) | {_now_est()}"
        else:
            subject = f"✅ CNL Daily Report | {chg_arrow}{abs(target_chg):.1f}% | {_now_est()}"

    html_body = build_html_email(alerts, metrics)

    payload = {
        "from":    cfg.ALERT_EMAIL_FROM,
        "to":      cfg.ALERT_EMAIL_TO,
        "subject": subject,
        "html":    html_body,
    }

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
            },
            json=payload,
            timeout=15,
        )
        if resp.status_code == 200:
            logger.info("Email sent via Resend API. ID: %s", resp.json().get("id"))
            return True
        logger.error("Resend API error %s: %s", resp.status_code, resp.text[:300])
        return False
    except requests.RequestException as exc:
        logger.error("Email send failed: %s", exc)
        return False


# ── DISPATCH — SEND ALL CHANNELS ────────────────────────────

def dispatch_alerts(
    alerts: List[Dict],
    metrics: Dict[str, Dict],
    force: bool = False,
) -> Dict[str, bool]:
    """
    Send notifications to all configured channels.
    Skips silently if no alerts and force=False.

    Returns: {channel: success_bool}
    """
    if not alerts and not force:
        logger.info("No alerts triggered — notifications suppressed.")
        return {"teams": False, "email": False}

    results = {
        "teams": send_teams_alert(alerts, metrics),
        "email": send_email_alert(alerts, metrics),
    }
    logger.info("Dispatch results: %s", results)
    return results
