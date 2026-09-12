"""
================================================================
Collective Mining Ltd. — Executive Intelligence Dashboard
src/theme.py

VISUAL LAYER ONLY.

Ports the Collective Mining Design System (tokens/colors.css,
typography.css, spacing.css, radius.css, elevation.css,
motion.css) onto the Streamlit surface.

Nothing in this module touches data ingestion, metrics or alert
dispatch — it only exposes brand tokens and the stylesheet.

Brand rules honoured here
-------------------------
  · Cyan #20A7C9 is the single accent. Nothing competes with it.
  · Navy #0E2943 is the dark ground (sidebar, table head, footer).
  · Hard-edged: 3px radius on cards/inputs, 2px on tags, 0 on bands.
  · Cards are defined by a 1px rule + a 3px cyan top edge, not by
    elevation. Shadows are navy-tinted and appear on hover only.
  · Montserrat everywhere; numerals set with tabular figures.
  · Headings and CTAs are UPPERCASE; eyebrows are 12/700/.18em cyan.
  · No emoji, on any surface.
================================================================
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


# ══════════════════════════════════════════════════════════════
#  TOKENS  —  mirrored from the design system for Python callers
#             (charts, badges, inline styles)
# ══════════════════════════════════════════════════════════════

# Brand core
CM_CYAN        = "#20A7C9"   # --cyan-500  · mark colour, only accent
CM_NAVY        = "#0E2943"   # --navy-800  · dark ground
CM_CHARCOAL    = "#333333"   # --neutral-800 · heading ink
CM_GRAY        = "#666666"   # --neutral-600 · "MINING" gray

# Cyan ramp
CYAN_100, CYAN_200, CYAN_300 = "#E4F5F9", "#BCE7F0", "#7FD0E2"
CYAN_400, CYAN_500, CYAN_600 = "#45B9D3", "#20A7C9", "#1A8AA7"
CYAN_700, CYAN_800           = "#146D84", "#0F5162"

# Navy ramp
NAVY_500, NAVY_600, NAVY_700 = "#1E5A80", "#154866", "#0E3450"
NAVY_800, NAVY_900           = "#0E2943", "#081A2C"

# Neutral ramp
NEUTRAL_0, NEUTRAL_50, NEUTRAL_100 = "#FFFFFF", "#F7F8F9", "#EFF1F3"
NEUTRAL_200, NEUTRAL_300, NEUTRAL_400 = "#E1E5E9", "#C7CDD3", "#9AA3AC"
NEUTRAL_500, NEUTRAL_600, NEUTRAL_700 = "#767F88", "#666666", "#4A4A4A"
NEUTRAL_800, NEUTRAL_900              = "#333333", "#1C1C1C"

# Commodity accents — tags and charts only
COMMODITY_GOLD     = "#C9A227"
COMMODITY_SILVER   = "#A8B0B8"
COMMODITY_COPPER   = "#B4703C"
COMMODITY_TUNGSTEN = "#5C6B73"

# Semantic status — muted, forms and tables only
STATUS_SUCCESS = "#2E7D51"
STATUS_WARNING = "#C97B20"
STATUS_DANGER  = "#B3341F"
STATUS_INFO    = CYAN_600

# Type
FONT_DISPLAY  = "Montserrat, 'Helvetica Neue', Arial, sans-serif"
FONT_DOCUMENT = "Arial, 'Helvetica Neue', Helvetica, sans-serif"


# ══════════════════════════════════════════════════════════════
#  ASSETS
# ══════════════════════════════════════════════════════════════

@lru_cache(maxsize=8)
def asset_data_uri(filename: str) -> str:
    """Inline a brand asset as a data URI (Streamlit serves no static dir)."""
    path = ASSETS_DIR / filename
    if not path.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def favicon_path() -> str:
    """Absolute path to the CM mark, for st.set_page_config(page_icon=…)."""
    path = ASSETS_DIR / "favicon.png"
    return str(path) if path.exists() else ""


# ══════════════════════════════════════════════════════════════
#  STYLESHEET
# ══════════════════════════════════════════════════════════════

CM_STYLESHEET = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;900&display=swap');

/* ─── TOKENS ─────────────────────────────────────────────── */
:root{
  --cm-cyan:#20A7C9; --cm-charcoal:#333333; --cm-gray:#666666;
  --cm-navy:#0E2943; --cm-teal-deep:#009CBB; --cm-navy-ink:#003554;

  --cyan-100:#E4F5F9; --cyan-200:#BCE7F0; --cyan-300:#7FD0E2; --cyan-400:#45B9D3;
  --cyan-500:#20A7C9; --cyan-600:#1A8AA7; --cyan-700:#146D84; --cyan-800:#0F5162;

  --navy-500:#1E5A80; --navy-600:#154866; --navy-700:#0E3450;
  --navy-800:#0E2943; --navy-900:#081A2C;

  --neutral-0:#FFFFFF; --neutral-50:#F7F8F9; --neutral-100:#EFF1F3;
  --neutral-200:#E1E5E9; --neutral-300:#C7CDD3; --neutral-400:#9AA3AC;
  --neutral-500:#767F88; --neutral-600:#666666; --neutral-700:#4A4A4A;
  --neutral-800:#333333; --neutral-900:#1C1C1C;

  --commodity-gold:#C9A227; --commodity-silver:#A8B0B8;
  --commodity-copper:#B4703C; --commodity-tungsten:#5C6B73;

  --status-success:#2E7D51; --status-warning:#C97B20;
  --status-danger:#B3341F;  --status-info:var(--cyan-600);

  --surface-page:var(--neutral-0);   --surface-subtle:var(--neutral-50);
  --surface-card:var(--neutral-0);   --surface-sunken:var(--neutral-100);
  --surface-inverse:var(--navy-800); --surface-inverse-raised:#143351;

  --text-heading:var(--neutral-800); --text-body:var(--neutral-700);
  --text-muted:var(--neutral-600);   --text-faint:var(--neutral-400);
  --text-on-inverse:var(--neutral-0);
  --text-on-inverse-muted:rgba(255,255,255,.72);

  --border-subtle:var(--neutral-200); --border-default:var(--neutral-300);
  --border-accent:var(--cyan-500);    --border-on-inverse:rgba(255,255,255,.16);
  --focus-ring:0 0 0 3px rgba(32,167,201,.38);

  --font-display:"Montserrat","Helvetica Neue",Arial,sans-serif;

  --fs-h1:36px; --fs-h2:28px; --fs-h3:22px; --fs-h4:18px;
  --fs-body:16px; --fs-small:14px; --fs-caption:12px;
  --fs-eyebrow:12px; --ls-eyebrow:.18em; --ls-label:.06em;
  --ls-display:-0.01em; --ls-wordmark:.14em; --ls-tight:-0.02em;

  --space-1:4px; --space-2:8px; --space-3:12px; --space-4:16px;
  --space-5:20px; --space-6:24px; --space-8:32px; --space-12:48px;
  --gutter:24px; --container-max:1200px; --page-margin:32px;
  --section-y-compact:56px;

  --radius-xs:2px; --radius-sm:3px; --radius-md:4px;

  --shadow-xs:0 1px 2px rgba(14,41,67,.07);
  --shadow-sm:0 2px 6px rgba(14,41,67,.09);
  --shadow-md:0 6px 18px rgba(14,41,67,.12);

  --ease-standard:cubic-bezier(.4,0,.2,1);
  --dur-fast:160ms; --dur-base:240ms;
}

/* ─── GROUND ─────────────────────────────────────────────── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"]{
  background:var(--surface-page) !important;
  font-family:var(--font-display) !important;
  color:var(--text-body);
}
/* Keep the toolbar reachable (it carries the sidebar toggle) but let the
   brand ground show through it. */
[data-testid="stHeader"]{ background:transparent !important; }
footer{ visibility:hidden; }

[data-testid="stMain"] .block-container,
[data-testid="stMainBlockContainer"]{
  max-width:var(--container-max);
  padding-left:var(--page-margin) !important;
  padding-right:var(--page-margin) !important;
  padding-top:72px !important;   /* clears the floating Streamlit toolbar */
  padding-bottom:var(--space-12) !important;
}

/* Numerals line up in columns wherever they appear */
.cm-num, .cm-card-value, .cm-table td, .cm-tag{
  font-variant-numeric:tabular-nums;
  font-feature-settings:"tnum" 1;
}

/* Streamlit's horizontal rule → CM hairline */
hr, [data-testid="stMarkdownContainer"] hr{
  border:0; border-top:1px solid var(--border-subtle);
  margin:var(--space-8) 0 var(--space-6);
}

/* ─── TOP BAR ────────────────────────────────────────────── */
.cm-topbar{
  display:flex; align-items:center; justify-content:space-between;
  flex-wrap:wrap; gap:var(--space-4);
  background:var(--surface-page);
  border-bottom:3px solid var(--cyan-500);
  padding:var(--space-5) 0 var(--space-4);
  margin-bottom:var(--space-8);
}
.cm-brand{ display:flex; align-items:center; gap:var(--space-5); min-width:0; }
.cm-brand img{ height:44px; width:auto; display:block; }
.cm-brand-divider{ width:1px; height:40px; background:var(--border-subtle); flex:0 0 1px; }
.cm-brand-copy{ min-width:0; }
.cm-brand-title{
  margin:0; font-size:var(--fs-h4); font-weight:700; text-transform:uppercase;
  letter-spacing:var(--ls-display); color:var(--text-heading); line-height:1.25;
}
.cm-brand-sub{
  margin:2px 0 0; font-size:var(--fs-caption); color:var(--text-muted);
  line-height:1.45;
}
.cm-topbar-meta{
  display:flex; align-items:center; gap:var(--space-4);
  flex-wrap:wrap; justify-content:flex-end;
}
.cm-listing{
  font-size:var(--fs-eyebrow); font-weight:700; letter-spacing:var(--ls-eyebrow);
  text-transform:uppercase; color:var(--cyan-600);
}
.cm-timestamp{
  font-size:var(--fs-caption); color:var(--text-muted);
  font-variant-numeric:tabular-nums; letter-spacing:.02em;
}
.cm-status{
  display:inline-flex; align-items:center; gap:8px;
  padding:6px 14px; border-radius:var(--radius-sm);
  font-size:11px; font-weight:700; letter-spacing:var(--ls-eyebrow);
  text-transform:uppercase; border:1px solid;
}
.cm-status::before{ content:''; width:7px; height:7px; border-radius:50%; background:currentColor; }
.cm-status-open{ color:var(--status-success); border-color:rgba(46,125,81,.35); background:rgba(46,125,81,.07); }
.cm-status-closed{ color:var(--neutral-600); border-color:var(--border-default); background:var(--neutral-50); }

/* ─── SECTION HEADING (eyebrow + rule + title) ───────────── */
.cm-section{ margin:var(--space-8) 0 var(--space-5); }
.cm-eyebrow{
  display:flex; align-items:center; gap:12px;
  font-size:var(--fs-eyebrow); font-weight:700; letter-spacing:var(--ls-eyebrow);
  text-transform:uppercase; color:var(--cyan-600); margin:0 0 var(--space-2);
}
.cm-eyebrow::before{ content:''; width:40px; height:3px; background:var(--cyan-500); flex:0 0 40px; }
.cm-section-title{
  margin:0; font-size:var(--fs-h3); font-weight:700; text-transform:uppercase;
  letter-spacing:var(--ls-display); color:var(--text-heading); line-height:1.28;
}
.cm-section-note{
  margin:var(--space-2) 0 0; font-size:var(--fs-caption); color:var(--text-muted);
}

/* ─── CARD (1px rule + 3px cyan top edge, never elevation) ─ */
.cm-card{
  position:relative; background:var(--surface-card);
  border:1px solid var(--border-subtle); border-top:3px solid var(--cyan-500);
  border-radius:var(--radius-sm); padding:var(--space-4) var(--space-5);
  height:100%;
  transition:box-shadow var(--dur-base) var(--ease-standard),
             transform var(--dur-base) var(--ease-standard);
}
.cm-card:hover{ transform:translateY(-2px); box-shadow:var(--shadow-md); }
.cm-card-label{
  font-size:11px; font-weight:700; letter-spacing:var(--ls-eyebrow);
  text-transform:uppercase; color:var(--text-muted); margin-bottom:var(--space-2);
}
.cm-card-value{
  font-size:26px; font-weight:700; line-height:1; letter-spacing:var(--ls-tight);
  color:var(--text-heading); margin-bottom:6px;
}
.cm-card-value.cm-sm{ font-size:18px; }
.cm-card-sub{ font-size:var(--fs-caption); color:var(--text-muted); line-height:1.45; }

.cm-pos{ color:var(--status-success) !important; }
.cm-neg{ color:var(--status-danger) !important; }
.cm-accent{ color:var(--cyan-600) !important; }
.cm-faint{ color:var(--text-faint) !important; }

/* ─── PEER TABLE ─────────────────────────────────────────── */
.cm-table-wrap{
  border:1px solid var(--border-subtle); border-radius:var(--radius-sm);
  overflow-x:auto; -webkit-overflow-scrolling:touch; background:var(--surface-card);
}
.cm-table{ width:100%; border-collapse:collapse; font-size:var(--fs-small); }
.cm-table th{
  background:var(--navy-800); color:var(--text-on-inverse);
  font-size:11px; font-weight:700; letter-spacing:var(--ls-eyebrow);
  text-transform:uppercase; padding:12px 16px; text-align:right; white-space:nowrap;
}
.cm-table th:first-child{ text-align:left; }
.cm-table td{
  padding:12px 16px; border-bottom:1px solid var(--border-subtle);
  color:var(--text-body); text-align:right; white-space:nowrap;
}
.cm-table td:first-child{ text-align:left; }
.cm-table tbody tr:nth-child(even){ background:var(--neutral-50); }
.cm-table tbody tr:hover td{ background:var(--cyan-100); }
.cm-table tr.cm-target td{
  background:var(--cyan-100); font-weight:600; color:var(--text-heading);
}
.cm-table tr.cm-target td:first-child{ box-shadow:inset 3px 0 0 var(--cyan-500); }
.cm-tag{
  display:inline-block; padding:3px 8px; border-radius:var(--radius-xs);
  font-size:11px; font-weight:700; letter-spacing:var(--ls-label);
  border:1px solid currentColor;
}
.cm-company{ font-size:var(--fs-caption); color:var(--text-muted); margin-left:8px; }
.cm-badge{
  display:inline-block; padding:2px 7px; border-radius:3px;
  font-size:10px; font-weight:700; letter-spacing:.04em; text-transform:uppercase;
}
.cm-badge-target{ background:rgba(32,167,201,0.12); color:#20A7C9; border:1px solid rgba(32,167,201,0.35); }
.cm-badge-mid{ background:rgba(224,109,83,0.12); color:#E06D53; border:1px solid rgba(224,109,83,0.35); }
.cm-badge-major{ background:rgba(30,90,128,0.12); color:#1E5A80; border:1px solid rgba(30,90,128,0.35); }
.cm-table-note{
  margin:var(--space-2) 0 0; font-size:11px; color:var(--text-faint);
  letter-spacing:.02em;
}

/* ─── ALERTS ─────────────────────────────────────────────── */
.cm-alert{
  display:flex; gap:var(--space-3); align-items:flex-start;
  background:var(--surface-card); border:1px solid var(--border-subtle);
  border-left:3px solid var(--neutral-400); border-radius:var(--radius-sm);
  padding:var(--space-3) var(--space-4); margin-bottom:var(--space-2);
}
.cm-alert-critical{ border-left-color:var(--status-danger); }
.cm-alert-warning { border-left-color:var(--status-warning); }
.cm-alert-info    { border-left-color:var(--cyan-500); }
.cm-alert-ticker{
  font-size:var(--fs-small); font-weight:700; color:var(--text-heading);
  letter-spacing:var(--ls-label);
}
.cm-alert-type{
  font-size:11px; font-weight:700; letter-spacing:var(--ls-eyebrow);
  text-transform:uppercase; color:var(--text-muted);
}
.cm-alert-msg{ font-size:var(--fs-small); color:var(--text-body); margin-top:2px; }
.cm-empty{
  background:var(--neutral-50); border:1px solid var(--border-subtle);
  border-left:3px solid var(--status-success); border-radius:var(--radius-sm);
  padding:var(--space-4); font-size:var(--fs-small); color:var(--text-body);
}

/* ─── FOOTER (navy band) ─────────────────────────────────── */
.cm-footer{
  background:var(--navy-800); border-top:3px solid var(--cyan-500);
  padding:var(--space-6) var(--space-8); margin-top:var(--space-12);
  border-radius:var(--radius-sm);
}
.cm-footer-mark{
  font-size:var(--fs-eyebrow); font-weight:700; letter-spacing:var(--ls-wordmark);
  text-transform:uppercase; color:var(--neutral-0); margin:0 0 var(--space-2);
}
.cm-footer-copy{
  font-size:11px; line-height:1.7; color:var(--text-on-inverse-muted); margin:0;
}

/* ─── SIDEBAR (navy ground) ──────────────────────────────── */
[data-testid="stSidebar"]{
  background:var(--navy-800) !important;
  border-right:1px solid var(--border-on-inverse);
}
[data-testid="stSidebar"] *{ color:var(--text-on-inverse); }
[data-testid="stSidebar"] hr{ border-top:1px solid var(--border-on-inverse); margin:var(--space-5) 0; }
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{
  font-size:11px !important; font-weight:700 !important;
  letter-spacing:var(--ls-eyebrow) !important; text-transform:uppercase !important;
  color:var(--text-on-inverse-muted) !important;
}
/* Select field — covers both the BaseWeb (<=1.4x) and react-aria (>=1.5x)
   markup Streamlit has shipped, so the control stays legible on navy. */
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] .react-aria-ComboBox [role="group"]{
  background:rgba(255,255,255,.08) !important;
  border:1px solid var(--border-on-inverse) !important;
  border-radius:var(--radius-sm) !important;
  color:var(--neutral-0) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div:focus-within,
[data-testid="stSidebar"] .react-aria-ComboBox [role="group"]:focus-within{
  border-color:var(--cyan-500) !important; box-shadow:var(--focus-ring) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] .react-aria-ComboBox input,
[data-testid="stSidebar"] .react-aria-ComboBox [role="combobox"]{
  color:var(--neutral-0) !important; background:transparent !important;
}

/* Dropdown popovers are hard-edged too */
[data-testid="portal"] [role="listbox"],
.react-aria-Popover, [data-baseweb="popover"] [role="listbox"]{
  border-radius:var(--radius-sm) !important;
}
.cm-side-title{
  font-size:var(--fs-eyebrow); font-weight:700; letter-spacing:var(--ls-eyebrow);
  text-transform:uppercase; color:var(--cyan-300); margin:0 0 var(--space-2);
}
.cm-side-block{ font-size:11px; line-height:1.7; color:var(--text-on-inverse-muted); }
.cm-side-block b{ color:var(--neutral-0); font-weight:600; }
.cm-channel{ display:flex; align-items:center; gap:8px; font-size:var(--fs-caption); padding:3px 0; }
.cm-channel::before{ content:''; width:7px; height:7px; border-radius:50%; background:currentColor; }
.cm-channel-on{ color:var(--cyan-300); }
.cm-channel-off{ color:rgba(255,255,255,.45); }

/* ─── BUTTONS (uppercase, hard-edged, one ramp step on hover) */
.stButton > button{
  width:100%; border-radius:var(--radius-sm) !important;
  font-family:var(--font-display) !important;
  font-size:12px !important; font-weight:700 !important;
  letter-spacing:var(--ls-label) !important; text-transform:uppercase !important;
  padding:10px 18px !important;
  transition:background var(--dur-fast) var(--ease-standard),
             border-color var(--dur-fast) var(--ease-standard);
}
.stButton > button[kind="secondary"]{
  background:transparent !important; color:var(--neutral-0) !important;
  border:1px solid var(--cyan-500) !important;
}
.stButton > button[kind="secondary"]:hover{
  background:var(--cyan-500) !important; color:var(--neutral-0) !important;
}
.stButton > button[kind="primary"]{
  background:var(--cyan-500) !important; color:var(--neutral-0) !important;
  border:1px solid var(--cyan-500) !important;
}
.stButton > button[kind="primary"]:hover{
  background:var(--cyan-600) !important; border-color:var(--cyan-600) !important;
}
.stButton > button:active{ transform:translateY(1px); }
.stButton > button:focus-visible{ box-shadow:var(--focus-ring) !important; }

/* ─── CHART PANEL ────────────────────────────────────────── */
/* Charts get the same card treatment: 1px rule + 3px cyan top edge */
[data-testid="stMain"] [data-testid="stPlotlyChart"]{
  border:1px solid var(--border-subtle); border-top:3px solid var(--cyan-500);
  border-radius:var(--radius-sm); padding:var(--space-2);
  background:var(--surface-card);
}
[data-testid="stMain"] [data-testid="stPlotlyChart"] > div{ width:100% !important; }

/* Sparkline sits inside its own labelled card */
.cm-spark-head{
  border:1px solid var(--border-subtle); border-top:3px solid var(--cyan-500);
  border-bottom:0; border-radius:var(--radius-sm) var(--radius-sm) 0 0;
  padding:var(--space-3) var(--space-5) 0; background:var(--surface-card);
  margin-bottom:-1px;
}
[data-testid="stElementContainer"]:has(.cm-spark-head)
  + [data-testid="stElementContainer"] [data-testid="stPlotlyChart"]{
  border-top:1px solid var(--border-subtle) !important;
  border-radius:0 0 var(--radius-sm) var(--radius-sm) !important;
  padding-top:0;
}

/* Warnings / toasts keep the muted brand status colours */
[data-testid="stAlert"]{
  border-radius:var(--radius-sm) !important;
  border-left:3px solid var(--status-warning) !important;
}

/* ─── RESPONSIVE ─────────────────────────────────────────── */
@media (max-width:1024px){
  [data-testid="stMain"] .block-container{ padding-left:var(--space-6); padding-right:var(--space-6); }
  [data-testid="stHorizontalBlock"]{ flex-wrap:wrap; gap:var(--space-3); }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{
    flex:1 1 calc(33.333% - var(--space-3)); min-width:180px;
  }
}
@media (max-width:768px){
  [data-testid="stMain"] .block-container{ padding-left:var(--space-4); padding-right:var(--space-4); }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{
    flex:1 1 calc(50% - var(--space-3)); min-width:150px;
  }
  .cm-topbar{ padding-top:var(--space-4); }
  .cm-topbar-meta{ justify-content:flex-start; width:100%; }
  .cm-brand img{ height:34px; }
  .cm-brand-divider{ display:none; }
  .cm-brand-title{ font-size:var(--fs-small); }
  .cm-section-title{ font-size:var(--fs-h4); }
  .cm-card-value{ font-size:22px; }
  .cm-footer{ padding:var(--space-5) var(--space-4); }
}
@media (max-width:480px){
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{
    flex:1 1 100%; min-width:100%;
  }
  .cm-table th, .cm-table td{ padding:10px 12px; }
}

/* Motion is restrained — respect the OS setting outright */
@media (prefers-reduced-motion:reduce){
  *{ transition:none !important; animation:none !important; }
  .cm-card:hover{ transform:none; }
}
</style>
"""


def inject(st_module) -> None:
    """Attach the Collective Mining stylesheet to the running Streamlit app."""
    st_module.markdown(CM_STYLESHEET, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  SMALL MARKUP HELPERS  (SectionHeading / Eyebrow from the DS)
# ══════════════════════════════════════════════════════════════

def section_heading(eyebrow: str, title: str, note: str = "") -> str:
    """Eyebrow rule + uppercase title — the CM section device."""
    note_html = f'<p class="cm-section-note">{note}</p>' if note else ""
    return (
        '<div class="cm-section">'
        f'<p class="cm-eyebrow">{eyebrow}</p>'
        f'<h2 class="cm-section-title">{title}</h2>'
        f"{note_html}"
        "</div>"
    )


def stat_card(label: str, value: str, sub: str = "", tone: str = "", small: bool = False) -> str:
    """KPI card: 1px rule, 3px cyan top edge, tabular numerals."""
    size_cls = " cm-sm" if small else ""
    tone_cls = f" {tone}" if tone else ""
    sub_html = f'<div class="cm-card-sub">{sub}</div>' if sub else ""
    return (
        '<div class="cm-card">'
        f'<div class="cm-card-label">{label}</div>'
        f'<div class="cm-card-value{size_cls}{tone_cls}">{value}</div>'
        f"{sub_html}"
        "</div>"
    )
