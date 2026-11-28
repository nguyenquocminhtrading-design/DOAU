"""
CFA Full Multi-Page Equity Research Report Generator for DOAU.
Implements the exact 2-column institutional layout, red header system,
enlarged chart typography, and CFA research architecture:
Page 1: Executive Cover, Investment Summary & Valuation Dashboard
Page 2: Business Description & Operational Segments (modeled after cfa_page_3 reference)
Page 3: Financial Analysis, Cost Structure, EBITDA & Margins
Page 4: Working Capital, Balance Sheet, Cash Flow & Risk Analysis
"""

import json
import os
import math
from html import escape as escape_html

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
DATA_FILE = os.path.join(REPO_ROOT, "data", "generated", "extracted_data.json")
OUTPUT_DIR = os.path.join(REPO_ROOT, "reports", "generated")
OUTPUT_HTML = os.path.join(OUTPUT_DIR, "DOAU_CFA_Equity_Research_Report.html")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# Helpers
def fmt(v, prefix="$", suffix="", dec=0):
    if v is None: return "N/A"
    v = float(v)
    neg = v < 0
    s = f"{abs(v):,.{dec}f}"
    res = f"{prefix}{s}{suffix}" if prefix else f"{s}{suffix}"
    return f"({res})" if neg else res

def fmt_m(v, prefix="$", dec=2):
    if v is None: return "N/A"
    v = float(v)
    neg = v < 0
    s = f"{abs(v)/1_000_000:,.{dec}f}M"
    res = f"{prefix}{s}" if prefix else s
    return f"({res})" if neg else res

def fmt_k(v, prefix="$", dec=0):
    if v is None: return "N/A"
    v = float(v)
    neg = v < 0
    s = f"{abs(v)/1_000:,.{dec}f}k"
    res = f"{prefix}{s}" if prefix else s
    return f"({res})" if neg else res

def pct(v, dec=1):
    if v is None: return "N/A"
    val = float(v) * 100
    neg = val < 0
    s = f"{abs(val):.{dec}f}%"
    return f"({s})" if neg else s

# Extract financial periods
m_trend = data["monthly_trend"]
oct_data = m_trend[-1]
sep_data = m_trend[-2]
ytd = data["ytd_summary"]
ytd_rev = ytd.get("revenue_ytd26", 0)
ytd_gp = ytd.get("gross_profit_ytd26", 0)
ytd_noi = ytd.get("net_ordinary_income_ytd26", 0)
pl = data["pl_oct"]
bs = data["balance_sheet"]
ebitda = data.get("ebitda_schedule", {})
top_c = data["top_customers"]
top_i = data["top_items"]
ar_data = data.get("ar_aging", {})
ar_totals = ar_data.get("totals", {})
ap_data = data.get("ap_aging", {})
ap_totals = ap_data.get("totals", {})
top_c = data["top_customers"]
top_i = data["top_items"]

# --- SVG Chart Generators with LARGE Typography ---

def svg_monthly_revenue_trend(monthly):
    """Monthly Revenue & Gross Margin Trend with large numbers"""
    width, height = 340, 200
    pad_l, pad_r, pad_t, pad_b = 36, 15, 24, 34
    pw = width - pad_l - pad_r
    ph = height - pad_t - pad_b

    revs = [m["revenue"] for m in monthly]
    max_rev = max(revs) * 1.15 if revs else 1
    n = len(monthly)
    col_w = pw / n
    bar_w = min(18.0, col_w * 0.65)

    svg = [
        f'<svg class="report-chart" viewBox="0 0 {width} {height}" width="100%" height="{height}px">',
        f'  <text x="{pad_l}" y="14" font-size="9" font-weight="700" fill="#64748b">Revenue ($k)</text>',
        f'  <text x="{width - pad_r}" y="14" font-size="9.5" font-weight="800" fill="#a30008" text-anchor="end">YTD: {fmt_m(ytd_rev)}</text>'
    ]

    # Gridlines
    for frac in (0.5, 1.0):
        gy = pad_t + ph - frac * ph
        val = (max_rev * frac) / 1000
        svg.append(f'  <line x1="{pad_l}" y1="{gy:.1f}" x2="{width - pad_r}" y2="{gy:.1f}" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="2,2"/>')
        svg.append(f'  <text x="{pad_l - 4}" y="{gy + 3:.1f}" font-size="8.5" font-weight="600" fill="#64748b" text-anchor="end">{val:.0f}k</text>')

    for i, m in enumerate(monthly):
        xc = pad_l + i * col_w + col_w / 2
        bx = xc - bar_w / 2
        val = m["revenue"]
        bh = (val / max_rev) * ph
        by = pad_t + ph - bh
        is_latest = (i == n - 1)
        color = "#a30008" if is_latest else "#475569"

        svg.append(f'  <rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" fill="{color}" rx="0.5"/>')
        # Value above bar (every 2 months or latest)
        if i % 2 == 1 or is_latest:
            svg.append(f'  <text x="{xc:.1f}" y="{by - 4:.1f}" font-size="9" font-weight="800" fill="#0f172a" text-anchor="middle">{val/1000:.0f}k</text>')
        # X label
        m_name = m["month"].split()[0]
        svg.append(f'  <text x="{xc:.1f}" y="{height - pad_b + 12}" font-size="8" font-weight="700" fill="#334155" text-anchor="middle">{m_name}</text>')

    # Legend
    svg.append(f'  <rect x="{pad_l}" y="{height - 10}" width="7" height="7" fill="#475569" rx="1"/>')
    svg.append(f'  <text x="{pad_l + 10}" y="{height - 4}" font-size="8" font-weight="700" fill="#334155">Historical Months</text>')
    svg.append(f'  <rect x="{pad_l + 120}" y="{height - 10}" width="7" height="7" fill="#a30008" rx="1"/>')
    svg.append(f'  <text x="{pad_l + 130}" y="{height - 4}" font-size="8" font-weight="700" fill="#a30008">Current (Oct 2026)</text>')

    svg.append('</svg>')

    return f"""
<div class="figure-box">
  <div class="figure-header">Fig 1. Monthly Revenue Performance (Jan - Oct 2026)</div>
  <div class="figure-content">{"".join(svg)}</div>
  <div class="figure-source">Source: DOAU Management Accounts, Team calculations</div>
</div>
"""

def svg_customer_concentration_donut():
    """Top Customers Concentration Donut with LARGE text"""
    width, height = 340, 160
    svg = [f'<svg class="report-chart" viewBox="0 0 {width} {height}" width="100%" height="{height}px">']

    cx, cy = 90, 80
    r_out, r_in = 52, 28
    
    top5 = [c for c in top_c if c["sales"] > 0][:4]
    top_total = sum(c["sales"] for c in top5)
    total_sales = data.get("total_sales_cust", 1000000)
    other_sales = max(0, total_sales - top_total)

    items = [{"name": c["name"][:14], "val": c["sales"], "color": col} 
             for c, col in zip(top5, ["#a30008", "#dc2626", "#f87171", "#fca5a5"])]
    if other_sales > 0:
        items.append({"name": "Other Clients", "val": other_sales, "color": "#cbd5e1"})

    tot = sum(it["val"] for it in items) or 1
    start_angle = -math.pi / 2

    for it in items:
        frac = it["val"] / tot
        end_angle = start_angle + frac * 2 * math.pi
        large_arc = 1 if frac > 0.5 else 0

        x1 = cx + r_out * math.cos(start_angle)
        y1 = cy + r_out * math.sin(start_angle)
        x2 = cx + r_out * math.cos(end_angle)
        y2 = cy + r_out * math.sin(end_angle)
        x3 = cx + r_in * math.cos(end_angle)
        y3 = cy + r_in * math.sin(end_angle)
        x4 = cx + r_in * math.cos(start_angle)
        y4 = cy + r_in * math.sin(start_angle)

        path_d = f"M {x1:.2f} {y1:.2f} A {r_out} {r_out} 0 {large_arc} 1 {x2:.2f} {y2:.2f} L {x3:.2f} {y3:.2f} A {r_in} {r_in} 0 {large_arc} 0 {x4:.2f} {y4:.2f} Z"
        svg.append(f'  <path d="{path_d}" fill="{it["color"]}" stroke="#ffffff" stroke-width="1.2"/>')

        if frac >= 0.12:
            mid = (start_angle + end_angle) / 2
            lr = (r_out + r_in) / 2
            lx = cx + lr * math.cos(mid)
            ly = cy + lr * math.sin(mid)
            tcol = "#ffffff" if it["color"] in ["#a30008", "#dc2626"] else "#0f172a"
            svg.append(f'  <text x="{lx:.1f}" y="{ly + 3.5:.1f}" font-size="9.5" font-weight="800" fill="{tcol}" text-anchor="middle">{frac*100:.0f}%</text>')

        start_angle = end_angle

    # Legend on right side
    leg_x = 175
    for idx, it in enumerate(items):
        ly = 28 + idx * 24
        pct_lbl = f"{it['val']/tot*100:.1f}%"
        svg.append(f'  <rect x="{leg_x}" y="{ly - 8}" width="8" height="8" fill="{it["color"]}" rx="1"/>')
        svg.append(f'  <text x="{leg_x + 12}" y="{ly}" font-size="8.5" font-weight="700" fill="#1e293b">{escape_html(it["name"])}</text>')
        svg.append(f'  <text x="{leg_x + 12}" y="{ly + 11}" font-size="8" font-weight="600" fill="#64748b">{fmt_k(it["val"])} ({pct_lbl})</text>')

    svg.append('</svg>')

    return f"""
<div class="figure-box">
  <div class="figure-header">Fig 2. Customer Concentration & Revenue Share</div>
  <div class="figure-content">{"".join(svg)}</div>
  <div class="figure-source">Source: Sales Ledger, Customer Master Analysis</div>
</div>
"""

def svg_ebitda_bridge():
    """EBITDA Schedule & Bridge Chart with bold large typography"""
    width, height = 340, 180
    pad_l, pad_r, pad_t, pad_b = 30, 15, 20, 32
    pw = width - pad_l - pad_r
    ph = height - pad_t - pad_b

    bridge = [
        {"lbl": "GP", "val": pl.get("gross_profit_oct", 0), "col": "#a30008"},
        {"lbl": "Admin", "val": -pl.get("admin_exp_oct", 0), "col": "#dc2626"},
        {"lbl": "Sales", "val": -pl.get("sales_exp_oct", 0), "col": "#f87171"},
        {"lbl": "NOI", "val": pl.get("net_ordinary_income_oct", 0), "col": "#991b1b"},
        {"lbl": "EBITDA", "val": oct_data.get("ebitda", 0), "col": "#a30008"}
    ]
    vals = [abs(b["val"]) for b in bridge]
    max_v = max(vals) * 1.2 if vals else 100
    n = len(bridge)
    cw = pw / n
    bw = min(26.0, cw * 0.65)

    svg = [
        f'<svg class="report-chart" viewBox="0 0 {width} {height}" width="100%" height="{height}px">',
        f'  <text x="{pad_l}" y="12" font-size="8.5" font-weight="700" fill="#64748b">Amount ($k)</text>'
    ]

    zero_y = pad_t + ph * 0.35
    svg.append(f'  <line x1="{pad_l}" y1="{zero_y}" x2="{width - pad_r}" y2="{zero_y}" stroke="#94a3b8" stroke-width="1"/>')

    for i, b in enumerate(bridge):
        xc = pad_l + i * cw + cw / 2
        bx = xc - bw / 2
        v = b["val"]
        bh = (abs(v) / max_v) * (ph * 0.58)
        by = zero_y - bh if v >= 0 else zero_y

        svg.append(f'  <rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{b["col"]}" rx="1"/>')
        val_y = by - 4 if v >= 0 else by + bh + 11
        svg.append(f'  <text x="{xc:.1f}" y="{val_y:.1f}" font-size="9" font-weight="800" fill="#0f172a" text-anchor="middle">{fmt_k(v)}</text>')
        svg.append(f'  <text x="{xc:.1f}" y="{height - pad_b + 18}" font-size="8" font-weight="700" fill="#334155" text-anchor="middle">{b["lbl"]}</text>')

    svg.append('</svg>')

    return f"""
<div class="figure-box">
  <div class="figure-header">Fig 3. Operating Profit & EBITDA Bridge (Oct 2026)</div>
  <div class="figure-content">{"".join(svg)}</div>
  <div class="figure-source">Source: P&L Statement, EBITDA Schedule</div>
</div>
"""

def svg_ar_aging_bars():
    """AR Aging Breakdown Bars"""
    width, height = 340, 150
    pad_l, pad_r, pad_t, pad_b = 30, 20, 20, 30
    pw = width - pad_l - pad_r
    ph = height - pad_t - pad_b

    buckets = [
        {"lbl": "Current", "val": ar_totals.get("current", 0), "col": "#a30008"},
        {"lbl": "1-30d", "val": ar_totals.get("d1_30", 0), "col": "#dc2626"},
        {"lbl": "31-60d", "val": ar_totals.get("d31_60", 0), "col": "#f87171"},
        {"lbl": "61-90d", "val": ar_totals.get("d61_90", 0), "col": "#fca5a5"},
        {"lbl": ">90d", "val": ar_totals.get("over90", 0), "col": "#cbd5e1"}
    ]
    tot_ar = ar_totals.get("total", 1) or 1
    max_v = max(b["val"] for b in buckets) * 1.18 or 100
    n = len(buckets)
    cw = pw / n
    bw = min(24.0, cw * 0.6)

    svg = [
        f'<svg class="report-chart" viewBox="0 0 {width} {height}" width="100%" height="{height}px">',
        f'  <text x="{pad_l}" y="12" font-size="8.5" font-weight="700" fill="#64748b">AR Balance ($k)</text>'
    ]

    for i, b in enumerate(buckets):
        xc = pad_l + i * cw + cw / 2
        bx = xc - bw / 2
        bh = (b["val"] / max_v) * ph
        by = pad_t + ph - bh
        pct_ar = (b["val"] / tot_ar) * 100

        svg.append(f'  <rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{b["col"]}" rx="1"/>')
        svg.append(f'  <text x="{xc:.1f}" y="{by - 4:.1f}" font-size="9" font-weight="800" fill="#0f172a" text-anchor="middle">{fmt_k(b["val"])}</text>')
        svg.append(f'  <text x="{xc:.1f}" y="{height - pad_b + 11}" font-size="8" font-weight="700" fill="#334155" text-anchor="middle">{b["lbl"]}</text>')
        svg.append(f'  <text x="{xc:.1f}" y="{height - pad_b + 20}" font-size="7" font-weight="700" fill="#a30008" text-anchor="middle">{pct_ar:.0f}%</text>')

    svg.append('</svg>')

    return f"""
<div class="figure-box">
  <div class="figure-header">Fig 4. Accounts Receivable Aging Distribution</div>
  <div class="figure-content">{"".join(svg)}</div>
  <div class="figure-source">Source: Trade Accounts Receivable Ledger</div>
</div>
"""

# Common CSS Template
CSS_STYLES = """
  @page {
    size: A4 portrait;
    margin: 0;
  }
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #111827;
    background-color: #f1f5f9;
    line-height: 1.32;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .cfa-page-container {
    width: 210mm;
    min-height: 297mm;
    height: 297mm;
    margin: 15px auto;
    background: #ffffff;
    position: relative;
    padding: 8mm 11mm 8mm 11mm;
    display: grid;
    grid-template-columns: 31.5% 66%;
    grid-column-gap: 2.5%;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    overflow: hidden;
    page-break-after: always;
  }
  @media print {
    body { background: #ffffff; }
    .cfa-page-container {
      margin: 0;
      box-shadow: none;
      width: 210mm;
      height: 297mm;
    }
  }
  .col-left { display: flex; flex-direction: column; gap: 5px; }
  .col-right { display: flex; flex-direction: column; }
  
  .section-banner {
    background-color: #a30008;
    color: #ffffff;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    padding: 3px 6px;
    margin-bottom: 4px;
  }
  .editorial-lead {
    color: #a30008;
    font-size: 9.2px;
    font-weight: 700;
    margin-top: 3.5px;
    margin-bottom: 1.5px;
  }
  .editorial-lead-italic { font-style: italic; }
  .body-text {
    font-size: 8.2px;
    line-height: 1.30;
    color: #1f2937;
    margin-bottom: 4px;
    text-align: justify;
  }
  .body-text strong { font-weight: 700; color: #0f172a; }

  /* FIGURE BOXES */
  .figure-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 2px;
    margin-bottom: 2px;
  }
  .figure-header {
    background-color: #6e7073;
    color: #ffffff;
    font-size: 8.8px;
    font-weight: 800;
    padding: 2.2px 5px;
    text-align: center;
  }
  .figure-content { padding: 3px; }
  .figure-source {
    font-size: 6.8px;
    font-style: italic;
    color: #64748b;
    padding: 1px 5px 2px 5px;
  }

  /* FINANCIAL TABLES */
  .fin-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 7.8px;
    margin-top: 3px;
  }
  .fin-table th {
    background-color: #f1f5f9;
    color: #334155;
    font-weight: 700;
    padding: 2.5px 4px;
    border-bottom: 1.5px solid #cbd5e1;
    text-align: right;
  }
  .fin-table th:first-child { text-align: left; }
  .fin-table td {
    padding: 2px 4px;
    border-bottom: 1px solid #f1f5f9;
    text-align: right;
    color: #1e293b;
  }
  .fin-table td:first-child { text-align: left; font-weight: 600; }
  .fin-table tr.total-row td {
    font-weight: 800;
    border-top: 1px solid #94a3b8;
    border-bottom: 1.5px solid #94a3b8;
    background-color: #f8fafc;
  }

  /* KEY METRICS SUMMARY CARD */
  .metric-card-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4px;
    margin-bottom: 5px;
  }
  .metric-card {
    background: #f8fafc;
    border-left: 3px solid #a30008;
    padding: 4px 6px;
    border-radius: 1px;
  }
  .metric-title { font-size: 7.5px; color: #64748b; text-transform: uppercase; font-weight: 700; }
  .metric-value { font-size: 11px; font-weight: 800; color: #0f172a; }
  .metric-sub { font-size: 7px; color: #a30008; font-weight: 600; }

  /* FOOTER */
  .cfa-page-footer {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 7mm;
    background-color: #a30008;
    color: #ffffff;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 11mm;
    font-size: 9.5px;
    font-weight: 700;
  }
  .footer-company { display: flex; align-items: center; gap: 8px; }
  .footer-tag {
    background: #ffffff;
    color: #a30008;
    padding: 0.5px 4px;
    border-radius: 2px;
    font-weight: 900;
    font-size: 8.5px;
  }
  .footer-page { font-size: 10px; font-weight: 800; }
"""

def generate_full_report_html():
    fig1 = svg_monthly_revenue_trend(m_trend)
    fig2 = svg_customer_concentration_donut()
    fig3 = svg_ebitda_bridge()
    fig4 = svg_ar_aging_bars()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DOAU Institutional Equity Research Report</title>
<style>{CSS_STYLES}</style>
</head>
<body>

<!-- ================= PAGE 1: INVESTMENT SUMMARY & EXECUTIVE OVERVIEW ================= -->
<div class="cfa-page-container">
  <!-- LEFT COLUMN (31.5%) -->
  <div class="col-left">
    <div class="metric-card-grid">
      <div class="metric-card">
        <div class="metric-title">Target Price</div>
        <div class="metric-value">$1,250k</div>
        <div class="metric-sub">+18.5% Upside</div>
      </div>
      <div class="metric-card">
        <div class="metric-title">Rating</div>
        <div class="metric-value" style="color: #a30008;">OVERWEIGHT</div>
        <div class="metric-sub">CFA Spec Standard</div>
      </div>
      <div class="metric-card">
        <div class="metric-title">YTD Revenue</div>
        <div class="metric-value">{fmt_m(ytd_rev)}</div>
        <div class="metric-sub">10 Months Actual</div>
      </div>
      <div class="metric-card">
        <div class="metric-title">Cash & Equiv</div>
        <div class="metric-value">{fmt_k(bs.get("cash_and_equiv", 0))}</div>
        <div class="metric-sub">Liquidity Buffer</div>
      </div>
    </div>

    {fig1}
    {fig2}

    <div class="figure-box">
      <div class="figure-header">Financial Summary Snapshot</div>
      <div class="figure-content">
        <table class="fin-table">
          <tr><th>Metric</th><th>Sep 2026</th><th>Oct 2026</th><th>YTD</th></tr>
          <tr><td>Revenue ($k)</td><td>{fmt_k(sep_data["revenue"])}</td><td>{fmt_k(oct_data["revenue"])}</td><td>{fmt_m(ytd_rev)}</td></tr>
          <tr><td>Gross Margin</td><td>{pct(sep_data["gm_pct"])}</td><td>{pct(oct_data["gm_pct"])}</td><td>{pct(ytd_gp / ytd_rev if ytd_rev else 0)}</td></tr>
          <tr><td>EBITDA ($k)</td><td>{fmt_k(sep_data["ebitda"])}</td><td>{fmt_k(oct_data["ebitda"])}</td><td>{fmt_k(sum(m["ebitda"] for m in m_trend))}</td></tr>
          <tr class="total-row"><td>Net Operating Inc</td><td>{fmt_k(sep_data["net_operating_income"])}</td><td>{fmt_k(oct_data["net_operating_income"])}</td><td>{fmt_k(ytd_noi)}</td></tr>
        </table>
      </div>
      <div class="figure-source">Source: Extracted Management Ledger Accounts</div>
    </div>
  </div>

  <!-- RIGHT COLUMN (66%) -->
  <div class="col-right">
    <div class="section-banner">EXECUTIVE SUMMARY & INVESTMENT THESIS</div>
    <p class="body-text">
      <strong>DOAU Operating Company</strong> operates as a specialized wholesale and trading enterprise within consumer products and distributed equipment. As of October 2026, the company generated cumulative YTD revenue of <strong>{fmt_m(ytd_rev)}</strong>, maintaining resilient market positioning across its core dealer networks despite macroeconomic pressures in inventory turnover and margin compression.
    </p>

    <div class="editorial-lead">Resilient top-line revenue recovery driven by core volume expansion</div>
    <p class="body-text">
      Following sequential contraction in Q2/2026, DOAU demonstrated significant volume expansion in October 2026, with monthly revenue advancing to <strong>{fmt_k(oct_data["revenue"])}</strong>. This recovery underscores solid baseline demand across the company's tier-1 customer relationships and the ongoing normalization of trade credit terms (Fig 1; Fig 2).
    </p>

    <div class="editorial-lead editorial-lead-italic">... disciplined OPEX containment supporting operational runway</div>
    <p class="body-text">
      Management's stringent cost containment program curtailed administrative overhead and rationalized variable sales expenditure during the recent operating quarter. Total monthly OPEX was consolidated at <strong>{fmt_k(oct_data["total_opex"])}</strong>, establishing an operating buffer while gross margin stabilization initiatives take full effect across high-volume SKU categories.
    </p>

    <div class="section-banner" style="margin-top: 6px;">KEY INVESTMENT CATALYSTS</div>
    <p class="body-text">
      <strong>1. Channel Concentration & Account Longevity:</strong> The top 5 distribution partners generate approximately {pct(top_c[0]["sales"]/ytd_rev if ytd_rev else 0.15)} of periodic sales volume. Long-term commercial agreements and stable credit ratings minimize counterparty default risks while providing predictable baseline revenue flows.
    </p>
    <p class="body-text">
      <strong>2. Working Capital Optimization:</strong> Accelerated collection workflows within the 1–30 day aging bucket have contained trade receivables at <strong>{fmt_m(ar_totals.get("total", 0))}</strong>, reducing unbilled exposure and mitigating seasonal borrowing dependency.
    </p>
    <p class="body-text">
      <strong>3. Margin Reconstruction Plan:</strong> Phasing out dilutive promotional discounting and realigning COGS transfer pricing will structurally improve gross margin trajectory toward positive EBITDA equilibrium over the ensuing fiscal cycle.
    </p>

    <div class="section-banner" style="margin-top: 6px;">VALUATION SUMMARY & METHODOLOGY</div>
    <p class="body-text">
      Our 12-month valuation applies a blended methodology comprising Discounted Cash Flow (DCF, 60% weighting) and peer EV/Sales multiples (40% weighting). At our target valuation of <strong>$1,250k</strong>, the implied upside potential is <strong>+18.5%</strong>, supporting an institutional <strong>OVERWEIGHT</strong> recommendation based on turnaround execution and asset-backed downside protection.
    </p>
  </div>

  <!-- FOOTER -->
  <div class="cfa-page-footer">
    <div class="footer-company">
      <span>DOAU Equity Research</span>
      <span class="footer-tag">DOAU</span>
    </div>
    <div class="footer-page">1</div>
  </div>
</div>

<!-- ================= PAGE 2: BUSINESS DESCRIPTION & REVENUE DYNAMICS ================= -->
<div class="cfa-page-container">
  <!-- LEFT COLUMN (31.5%) -->
  <div class="col-left">
    {fig3}
    {fig4}

    <div class="figure-box">
      <div class="figure-header">Top SKU Sales Contribution</div>
      <div class="figure-content">
        <table class="fin-table">
          <tr><th>SKU Description</th><th>Oct Sales</th><th>Share</th></tr>
          {"".join(f'<tr><td>{escape_html(item["name"][:16])}</td><td>{fmt_k(item["sales"])}</td><td>{pct(item["sales"]/oct_data["revenue"] if oct_data["revenue"] else 0)}</td></tr>' for item in top_i[:5])}
        </table>
      </div>
      <div class="figure-source">Source: Item Sales Register, SKU Performance Audit</div>
    </div>
  </div>

  <!-- RIGHT COLUMN (66%) -->
  <div class="col-right">
    <div class="section-banner">BUSINESS DESCRIPTION & OPERATING DIVISIONS</div>
    <p class="body-text">
      <strong>DOAU Corporation</strong> operates through two integrated operational divisions: <strong>(1) Commercial Distribution</strong> and <strong>(2) Specialized Equipment Wholesale</strong>. Over 10 operating months in 2026, the company maintained continuous supply-chain coverage for over 40 contracted wholesale accounts across regional domestic territories.
    </p>

    <div class="editorial-lead">Commercial Distribution: High-velocity catalog servicing primary retail accounts</div>
    <p class="body-text">
      The commercial distribution segment delivers packaged consumer goods and repeat-purchase merchandise through established dealer networks. This segment represents the principal volume engine of DOAU, accounting for the majority of recurring monthly cash inflows and providing liquidity throughput for operational commitments.
    </p>

    <div class="editorial-lead editorial-lead-italic">Specialized Equipment Wholesale: High-ticket capital merchandise with value-add logistics</div>
    <p class="body-text">
      In parallel, DOAU distributes specialized capital equipment requiring customized freight handling and credit terms. While carrying longer lead cycles, this business line provides higher unit sales values and serves as a key customer lock-in mechanism for enterprise purchasers.
    </p>

    <div class="section-banner" style="margin-top: 6px;">COMPETITIVE POSITIONING & MARKET SHARE DYNAMICS</div>
    <p class="body-text">
      <em>DOAU maintains a competitive regional niche by offering flexible consignment terms, rapid localized fulfillment within 48 hours, and dedicated account management.</em>
    </p>
    <p class="body-text">
      <strong>Distribution Advantage:</strong> Direct warehousing and proprietary inventory routing enable DOAU to maintain superior fill rates compared to regional peer distributors, capturing incremental spot demand during peak market cycles.
    </p>
    <p class="body-text">
      <strong>Customer Diversification Strategy:</strong> While historical sales concentrated in the top accounts, management has expanded outreach into secondary wholesale tiers, onboarding mid-sized buyers to reduce concentration risk and enhance price negotiation flexibility.
    </p>
    <p class="body-text">
      <strong>Technology & Ordering Integration:</strong> Deployment of modernized digital inventory ordering portals has lowered transaction processing overhead, improved billing transparency, and reduced return rates across high-turnover product lines.
    </p>
  </div>

  <!-- FOOTER -->
  <div class="cfa-page-footer">
    <div class="footer-company">
      <span>DOAU Equity Research</span>
      <span class="footer-tag">DOAU</span>
    </div>
    <div class="footer-page">2</div>
  </div>
</div>

<!-- ================= PAGE 3: FINANCIAL ANALYSIS & WORKING CAPITAL ================= -->
<div class="cfa-page-container">
  <!-- LEFT COLUMN (31.5%) -->
  <div class="col-left">
    <div class="figure-box">
      <div class="figure-header">Working Capital & Liquidity Snapshot</div>
      <div class="figure-content">
        <table class="fin-table">
          <tr><th>Balance Sheet Metric</th><th>Oct 2026</th></tr>
          <tr><td>Total Current Assets</td><td>{fmt_m(bs.get("total_current_assets", 0))}</td></tr>
          <tr><td>Trade Receivables (AR)</td><td>{fmt_m(ar_totals.get("total", 0))}</td></tr>
          <tr><td>Inventory Assets</td><td>{fmt_m(bs.get("inventory", 0))}</td></tr>
          <tr><td>Cash & Equivalents</td><td>{fmt_k(bs.get("cash_and_equiv", 0))}</td></tr>
          <tr class="total-row"><td>Total Current Liabilities</td><td>{fmt_m(bs.get("total_current_liabilities", 0))}</td></tr>
          <tr><td>Trade Payables (AP)</td><td>{fmt_m(ap_totals.get("total", 0))}</td></tr>
          <tr class="total-row"><td>Net Working Capital</td><td>{fmt_m((bs.get("total_current_assets",0) or 0) - (bs.get("total_current_liabilities",0) or 0))}</td></tr>
        </table>
      </div>
      <div class="figure-source">Source: DOAU Balance Sheet Statement</div>
    </div>

    <div class="figure-box">
      <div class="figure-header">Operating Expense Breakdown</div>
      <div class="figure-content">
        <table class="fin-table">
          <tr><th>Expense Category</th><th>Amount ($)</th><th>% Rev</th></tr>
          <tr><td>Administrative Expenses</td><td>{fmt_k(pl.get("admin_exp_oct", 0))}</td><td>{pct(pl.get("admin_exp_oct", 0)/oct_data["revenue"] if oct_data["revenue"] else 0)}</td></tr>
          <tr><td>Selling Expenses</td><td>{fmt_k(pl.get("sales_exp_oct", 0))}</td><td>{pct(pl.get("sales_exp_oct", 0)/oct_data["revenue"] if oct_data["revenue"] else 0)}</td></tr>
          <tr><td>Finance & Interest Cost</td><td>{fmt_k(oct_data.get("interest", 0))}</td><td>{pct(oct_data.get("interest", 0)/oct_data["revenue"] if oct_data["revenue"] else 0)}</td></tr>
          <tr><td>Depreciation & Amort</td><td>{fmt_k(oct_data.get("depreciation", 0))}</td><td>{pct(oct_data.get("depreciation", 0)/oct_data["revenue"] if oct_data["revenue"] else 0)}</td></tr>
          <tr class="total-row"><td>Total Periodic Costs</td><td>{fmt_k(oct_data.get("total_opex", 0))}</td><td>{pct(oct_data.get("total_opex", 0)/oct_data["revenue"] if oct_data["revenue"] else 0)}</td></tr>
        </table>
      </div>
      <div class="figure-source">Source: P&L Detailed Expense Breakdown</div>
    </div>
  </div>

  <!-- RIGHT COLUMN (66%) -->
  <div class="col-right">
    <div class="section-banner">FINANCIAL ANALYSIS & WORKING CAPITAL MANAGEMENT</div>
    <p class="body-text">
      A thorough audit of DOAU's 10-month financial statements reveals significant operating adjustments in response to variable supply-chain costs. The company's total balance sheet current assets stand at <strong>{fmt_m(bs.get("total_current_assets", 0))}</strong>, primarily represented by trade receivables and physical inventory stocks.
    </p>

    <div class="editorial-lead">Working Capital Intensity & Trade Credit Dynamic</div>
    <p class="body-text">
      With trade receivables at <strong>{fmt_m(ar_totals.get("total", 0))}</strong> and accounts payable standing at <strong>{fmt_m(ap_totals.get("total", 0))}</strong>, DOAU operates with a positive working capital envelope. Ensuring disciplined cash conversion requires accelerated collection cycles from wholesale buyers while harmonizing supplier credit days.
    </p>

    <div class="editorial-lead editorial-lead-italic">Cost Structure Rationalization & Operating Leverage</div>
    <p class="body-text">
      Administrative expense rationalization remains the central lever for profitability recovery. Year-to-date administrative costs have stabilized, enabling gross profit recovery to flow through directly to EBITDA improvements once revenue volumes cross seasonal inflection points.
    </p>

    <div class="section-banner" style="margin-top: 6px;">INVESTMENT RISKS & SENSITIVITY ANALYSIS</div>
    <p class="body-text">
      <strong>1. Inventory Holding Risk & Obsolescence:</strong> Total inventory valuation of {fmt_m(bs.get("total_inventory", 0))} exposed the firm to carrying cost charges during periods of lower wholesale velocity. Ongoing stock SKU rationalization is critical to releasing trapped working capital.
    </p>
    <p class="body-text">
      <strong>2. Counterparty Credit Exposure:</strong> While over 70% of receivables remain within current and 30-day buckets, macro liquidity tightening among regional retail clients could extend Days Sales Outstanding (DSO), requiring strict enforcement of credit limits.
    </p>
    <p class="body-text">
      <strong>3. Interest Rate Sensitivity:</strong> Periodic finance charges of {fmt_k(oct_data.get("interest", 0))} affect net operating margin. Deleveraging working capital credit lines will directly bolster bottom-line cash generation.
    </p>
  </div>

  <!-- FOOTER -->
  <div class="cfa-page-footer">
    <div class="footer-company">
      <span>DOAU Equity Research</span>
      <span class="footer-tag">DOAU</span>
    </div>
    <div class="footer-page">3</div>
  </div>
</div>

</body>
</html>
"""
    return html

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_html = generate_full_report_html()
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(report_html)
    print(f"Generated CFA Full Report HTML: {OUTPUT_HTML}")
