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
        severity = a["severity"].upper()
        alert_facts.append({
            "title": f"{a['display']} · {severity}",
            "value": a["message"],
        })

    card_body = [
        # Title
        {
            "type": "TextBlock",
            "text": "COLLECTIVE MINING — MARKET INTELLIGENCE ALERT",
            "size": "Large",
            "weight": "Bolder",
            "color": "Accent",
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
            "text": "CNL (TSX) SNAPSHOT",
            "weight": "Bolder",
            "color": "Accent",
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
                "text": f"{len(alerts)} ALERT(S) TRIGGERED",
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
            "text": "No alerts triggered — all thresholds within normal range.",
            "color": "Good",
            "spacing": "Medium",
        })

    # Competitor mini-table (TextBlock column sets)
    card_body.append({"type": "Separator"})
    card_body.append({
        "type": "TextBlock",
        "text": "PEER PERFORMANCE",
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
        card_body.append({
            "type": "TextBlock",
            "text": f"{company.short_name} ({company.ticker_display})  ·  {p_str}  ·  {chg_str_peer}",
            "size": "Small",
            "weight": "Bolder" if company.is_target else "Default",
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

    # ── Collective Mining Design System tokens (inline — email clients
    #    strip <style>, so every value is written out on the element).
    CM_CYAN    = "#20A7C9"   # --cyan-500 · the single accent
    CM_CYAN_D  = "#146D84"   # --cyan-700
    CM_NAVY    = "#0E2943"   # --navy-800 · dark ground
    INK        = "#333333"   # --text-heading
    BODY       = "#4A4A4A"   # --text-body
    MUTED      = "#666666"   # --text-muted
    FAINT      = "#9AA3AC"   # --text-faint
    LINE       = "#E1E5E9"   # --border-subtle
    ZEBRA      = "#F7F8F9"   # --neutral-50
    HILITE     = "#E4F5F9"   # --cyan-100 · the CNL row
    OK         = "#2E7D51"   # --status-success
    WARN       = "#C97B20"   # --status-warning
    BAD        = "#B3341F"   # --status-danger
    # Montserrat is the brand face; Arial is the mandated fallback for
    # correspondence and the only face email clients reliably have.
    FONT       = "'Montserrat',Arial,Helvetica,sans-serif"

    LABEL = (f"color:{MUTED};font-size:10px;font-weight:700;"
             "text-transform:uppercase;letter-spacing:1.8px;")
    CELL  = f"padding:12px 16px;border-bottom:1px solid {LINE};"
    HEAD  = (f"padding:10px 16px;background:{CM_NAVY};color:#FFFFFF;font-size:10px;"
             "font-weight:700;text-transform:uppercase;letter-spacing:1.8px;")

    chg_color = OK if chg_pct >= 0 else BAD
    chg_str   = f"{'▲' if chg_pct >= 0 else '▼'} {abs(chg_pct):.2f}%"
    ytd_color = OK if (ret_ytd or 0) >= 0 else BAD

    def _eyebrow(text: str) -> str:
        """The CM section device: a 40x3 cyan rule above a tracked label."""
        return (
            f'<div style="width:40px;height:3px;background:{CM_CYAN};'
            'font-size:0;line-height:0;margin:0 0 10px;">&nbsp;</div>'
            f'<div style="color:{CM_CYAN_D};font-size:11px;font-weight:700;'
            f'text-transform:uppercase;letter-spacing:2.1px;margin:0 0 12px;">{text}</div>'
        )

    # ── Alert rows ───────────────────────────────────────────
    sev_colors = {"critical": BAD, "warning": WARN, "info": CM_CYAN}
    alert_rows_html = ""
    if alerts:
        for a in alerts:
            rule = sev_colors.get(a["severity"], FAINT)
            alert_rows_html += f"""
            <tr>
              <td style="{CELL}border-left:3px solid {rule};color:{INK};font-weight:700;
                         white-space:nowrap;">{a['display']}</td>
              <td style="{CELL}color:{BODY};">{a['message']}</td>
            </tr>"""
    else:
        alert_rows_html = f"""
        <tr><td colspan="2" style="{CELL}border-left:3px solid {OK};color:{BODY};">
          No alerts triggered — all thresholds within normal range.
        </td></tr>"""

    # ── Peer rows ────────────────────────────────────────────
    peer_rows_html = ""
    for idx, company in enumerate(cfg.COMPANIES):
        m   = metrics.get(company.ticker_primary, {})
        chg = m.get("change_1d_pct", None)
        pr  = m.get("price", None)
        ret = (m.get("returns") or {}).get("ytd", None)

        row_bg  = HILITE if company.is_target else (ZEBRA if idx % 2 else "#FFFFFF")
        weight  = "700" if company.is_target else "400"
        chg_col = FAINT if chg is None else (OK if chg >= 0 else BAD)
        ret_col = FAINT if ret is None else (OK if ret >= 0 else BAD)
        chg_txt = "—" if chg is None else f"{'▲' if chg >= 0 else '▼'} {abs(chg):.2f}%"
        ret_txt = "—" if ret is None else f"{ret:+.1f}%"
        pr_txt  = "—" if pr  is None else f"${pr:.3f}"

        peer_rows_html += f"""
        <tr style="background:{row_bg};">
          <td style="{CELL}color:{company.color};font-weight:700;white-space:nowrap;">
            {company.ticker_display}
          </td>
          <td style="{CELL}color:{INK};font-weight:{weight};">{company.short_name}</td>
          <td style="{CELL}color:{INK};text-align:right;font-weight:{weight};">{pr_txt}</td>
          <td style="{CELL}color:{chg_col};text-align:right;font-weight:700;">{chg_txt}</td>
          <td style="{CELL}color:{ret_col};text-align:right;">{ret_txt}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Collective Mining — Market Intelligence Alert</title></head>
<body style="margin:0;padding:0;background:{ZEBRA};font-family:{FONT};">
<table width="100%" cellpadding="0" cellspacing="0" style="background:{ZEBRA};padding:24px 0;">
  <tr><td align="center">
    <table width="680" cellpadding="0" cellspacing="0" style="background:#FFFFFF;
           border:1px solid {LINE};border-radius:3px;overflow:hidden;max-width:100%;">

      <!-- Header — navy ground, cyan rule -->
      <tr>
        <td style="background:{CM_NAVY};padding:28px 32px;border-bottom:3px solid {CM_CYAN};">
          <div style="color:#7FD0E2;font-size:11px;font-weight:700;text-transform:uppercase;
                      letter-spacing:2.1px;margin:0 0 8px;">Nasdaq &amp; TSX: CNL</div>
          <h1 style="margin:0;color:#FFFFFF;font-size:20px;font-weight:700;
                     text-transform:uppercase;letter-spacing:-0.2px;">
            Collective Mining Ltd.
          </h1>
          <p style="margin:6px 0 0;color:rgba(255,255,255,.72);font-size:12px;">
            Market Intelligence Alert  ·  {_now_est()}
          </p>
        </td>
      </tr>

      <!-- CNL KPI bar -->
      <tr>
        <td style="padding:24px 24px 8px;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="text-align:center;padding:12px;">
                <div style="{LABEL}">Price</div>
                <div style="color:{INK};font-size:24px;font-weight:700;margin-top:6px;">${price:.3f}</div>
                <div style="color:{MUTED};font-size:11px;margin-top:2px;">CAD</div>
              </td>
              <td style="text-align:center;padding:12px;border-left:1px solid {LINE};">
                <div style="{LABEL}">1D Change</div>
                <div style="color:{chg_color};font-size:24px;font-weight:700;margin-top:6px;">{chg_str}</div>
                <div style="color:{MUTED};font-size:11px;margin-top:2px;">vs. previous close</div>
              </td>
              <td style="text-align:center;padding:12px;border-left:1px solid {LINE};">
                <div style="{LABEL}">YTD Return</div>
                <div style="color:{ytd_color};font-size:24px;font-weight:700;margin-top:6px;">
                  {"{:+.1f}%".format(ret_ytd) if ret_ytd is not None else "—"}
                </div>
                <div style="color:{MUTED};font-size:11px;margin-top:2px;">Year-to-date</div>
              </td>
              <td style="text-align:center;padding:12px;border-left:1px solid {LINE};">
                <div style="{LABEL}">RSI ({cfg.RSI_PERIOD}d)</div>
                <div style="color:{CM_CYAN_D};font-size:24px;font-weight:700;margin-top:6px;">{rsi}</div>
                <div style="color:{MUTED};font-size:11px;margin-top:2px;">
                  Beta {beta} · Vol {_format_volume(vol)} ({rel_vol:.1f}×)
                </div>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- Alerts -->
      <tr>
        <td style="padding:16px 32px 8px;">
          {_eyebrow("Signals")}
          <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;
                 border:1px solid {LINE};">
            <thead>
              <tr>
                <th style="{HEAD}text-align:left;">Ticker</th>
                <th style="{HEAD}text-align:left;">Signal</th>
              </tr>
            </thead>
            <tbody>{alert_rows_html}</tbody>
          </table>
        </td>
      </tr>

      <!-- Peer comparison -->
      <tr>
        <td style="padding:24px 32px 32px;">
          {_eyebrow("Peer Set")}
          <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;
                 border:1px solid {LINE};">
            <thead>
              <tr>
                <th style="{HEAD}text-align:left;">Ticker</th>
                <th style="{HEAD}text-align:left;">Company</th>
                <th style="{HEAD}text-align:right;">Price</th>
                <th style="{HEAD}text-align:right;">1D Chg</th>
                <th style="{HEAD}text-align:right;">YTD</th>
              </tr>
            </thead>
            <tbody>{peer_rows_html}</tbody>
          </table>
        </td>
      </tr>

      <!-- Footer — navy contact bar -->
      <tr>
        <td style="background:{CM_NAVY};padding:20px 32px;border-top:3px solid {CM_CYAN};">
          <p style="margin:0;color:rgba(255,255,255,.72);font-size:11px;line-height:1.7;text-align:center;">
            Collective Mining Ltd. · Executive Market Intelligence System<br>
            Data sourced from Yahoo Finance, 15-minute delay ·
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
    recipient_email: Optional[str] = None,
    subject: Optional[str] = None,
    period: str = "1d",
) -> bool:
    """
    Send HTML email report via Resend API to recipient_email (or cfg.ALERT_EMAIL_TO).
    Returns True on success.
    Docs: https://resend.com/docs/api-reference/emails/send-email
    """
    api_key = cfg.RESEND_API_KEY
    if not api_key:
        logger.warning("RESEND_API_KEY not set — skipping email notification.")
        return False

    to_emails = [recipient_email.strip()] if recipient_email else cfg.ALERT_EMAIL_TO
    if not to_emails or not to_emails[0]:
        logger.warning("No recipient email specified — skipping email.")
        return False

    n_alerts   = len(alerts)
    has_crit   = any(a["severity"] == "critical" for a in alerts)
    target_chg = metrics.get(cfg.TARGET.ticker_primary, {}).get("change_1d_pct", 0) or 0
    chg_arrow  = "▲" if target_chg >= 0 else "▼"

    if subject is None:
        subject = f"Executive Intelligence Dashboard Report | CNL {chg_arrow}{abs(target_chg):.1f}% | Period: {period.upper()} | {_now_est()}"

    html_body = build_html_email(alerts, metrics)

    payload = {
        "from":    cfg.ALERT_EMAIL_FROM,
        "to":      to_emails,
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
