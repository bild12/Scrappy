# ⛏️ Collective Mining — Executive Intelligence Dashboard

> **Real-time C-Level market monitoring** for Collective Mining Ltd. (CNL) and 5 key junior mining peers.  
> Designed for presentations to CEO, VP Ejecutivo, and CIBC Global Mining Group.

---

## 📸 What It Does

| Feature | Details |
|---|---|
| **Price Dashboard** | Live prices, 1D/1M/YTD returns, Beta, RSI for all 6 tickers |
| **Peer Comparison Table** | Color-coded grid — CNL vs. FDY, MARI, LMCU, NCX, OM |
| **Normalized Performance Chart** | All tickers rebased to 100 — visual relative outperformance |
| **Candlestick + MA** | OHLCV chart with MA20/50/200 overlays + volume bars |
| **RSI Panel** | Relative Strength Index with overbought/oversold zones |
| **Bollinger Bands** | Volatility envelope around price |
| **Relative Volume** | Volume spikes vs. 20-day average |
| **Alert System** | Auto-dispatched to **Microsoft Teams** + **Email** when signals fire |
| **GitHub Actions** | Serverless automation — no server needed, runs on schedule |

---

## 🏗️ Project Structure

```
Scrappy/
├── app.py                          ← Streamlit dashboard (entry point)
├── config.py                       ← Central config: tickers, thresholds, colors
├── requirements.txt
├── .env.example                    ← Copy to .env and fill credentials
│
├── src/
│   ├── data_fetcher.py             ← yfinance ingestion, quotes, normalized returns
│   ├── metrics.py                  ← RSI, Beta, BB, VWAP, S/R, alert detection
│   ├── charts.py                   ← All Plotly chart components
│   └── alerts.py                   ← Teams Adaptive Card + Resend email
│
├── scripts/
│   └── run_alerts.py               ← Standalone runner (called by GitHub Actions)
│
├── .github/workflows/
│   ├── daily_open_report.yml       ← 9:45 AM EST — morning open report
│   ├── intraday_alerts.yml         ← Every 30 min during market hours
│   └── eod_report.yml              ← 4:30 PM EST — end-of-day report
│
└── .streamlit/
    └── config.toml                 ← Dark gold theme
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/your-org/Scrappy.git
cd Scrappy
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configure Credentials

```bash
copy .env.example .env
```

Edit `.env`:

```env
# Microsoft Teams — from channel: ... → Connectors → Incoming Webhook
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...

# Resend API — sign up free at resend.com
RESEND_API_KEY=re_xxxxxxxxxxxx
ALERT_EMAIL_FROM=alerts@yourdomain.com
ALERT_EMAIL_TO=ceo@collectivemining.com,vp@collectivemining.com
```

### 3. Run the Dashboard

```bash
streamlit run app.py
```

Open: **http://localhost:8501**

### 4. Test Alert Dispatch

```bash
python scripts/run_alerts.py --mode check --force
```

---

## 🤖 GitHub Actions Setup

To enable automated alerts with zero infrastructure:

1. **Push this repo to GitHub**

2. **Add secrets** in GitHub → Settings → Secrets and Variables → Actions:
   | Secret | Value |
   |---|---|
   | `TEAMS_WEBHOOK_URL` | Your Teams Incoming Webhook URL |
   | `RESEND_API_KEY` | Your Resend API key |
   | `ALERT_EMAIL_FROM` | Sender email |
   | `ALERT_EMAIL_TO` | Comma-separated recipient list |

3. **GitHub Actions will run automatically**:
   - **9:45 AM EST** Mon–Fri → Morning open report
   - **Every 30 min** during market hours → Intraday alert check
   - **4:30 PM EST** Mon–Fri → End-of-day executive report

> You can also trigger any workflow manually from the **Actions** tab.

---

## 📊 Tickers Monitored

| Company | Ticker (yfinance) | Exchange | Color |
|---|---|---|---|
| ⭐ **Collective Mining Ltd.** | `CNL.TO` | TSX | 🟡 Gold |
| Faraday Copper Corp. | `FDY.TO` | TSX | 🔵 Blue |
| Marimaca Copper Corp. | `MARI.TO` | TSX | 🟢 Teal |
| Lumina Metals Corp. | `LMCU.TO` | TSX | 🟠 Orange |
| NorthIsle Copper and Gold | `NCX.V` | TSX-V | 🟣 Purple |
| Osisko Metals Inc. | `OM.TO` | TSX | 🩷 Magenta |

**Benchmark**: `XEG.TO` (iShares S&P/TSX Capped Energy — used for Beta calculation)

---

## 🚨 Alert Triggers

| Signal | Default Threshold |
|---|---|
| Price change | ±3% in 1 day |
| Volume spike | >2× the 20-day average |
| RSI overbought | RSI > 70 |
| RSI oversold | RSI < 30 |
| MA Crossover | MA20 crosses MA50 |
| 52-week high/low | Price within 0.5% of extreme |

Thresholds are configurable via `.env` or GitHub Variables.

---

## 📧 Notification Channels

| Channel | Format | When |
|---|---|---|
| **Microsoft Teams** | Adaptive Card (color-coded, structured table) | On alert trigger |
| **Email (Resend API)** | Premium HTML report with peer comparison | On alert + EOD |

> ⛔ **Telegram and Slack are NOT used** per company policy.

---

## ☁️ Deploy to Streamlit Community Cloud (Free)

1. Push repo to a **public or private** GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select your repo → set **Main file: `app.py`**
4. Add secrets in Streamlit Cloud → **App Settings → Secrets**:
   ```toml
   TEAMS_WEBHOOK_URL = "..."
   RESEND_API_KEY = "..."
   ALERT_EMAIL_FROM = "..."
   ALERT_EMAIL_TO = "..."
   ```
5. Click **Deploy** — your dashboard is live in ~2 minutes.

---

## 📐 Metrics Reference

| Metric | Formula / Source |
|---|---|
| **Return 1D/1M/YTD** | `(P_end / P_start - 1) × 100` |
| **Beta (60d)** | `Cov(stock, benchmark) / Var(benchmark)` rolling 60 trading days |
| **RSI (14d)** | Wilder's exponential smoothing |
| **Bollinger Bands** | SMA(20) ± 2σ |
| **Relative Volume** | `Vol_today / Avg_20d_Vol` |
| **Support/Resistance** | 52-week H/L + Classic Pivot Points |
| **VWAP** | `Σ(Typical Price × Volume) / Σ(Volume)` (intraday) |

---

*Collective Mining Ltd. · Executive Intelligence System · Internal Use Only*
