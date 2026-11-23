import json
import os
import subprocess
from html import escape as escape_html
from chart_rendering import compact_money, svg_line_chart, svg_pie_chart, svg_product_bars
from report_metrics import build_report_metrics, percent_change, safe_divide

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(CURRENT_DIR, "data", "extracted_data.json")
OUTPUT_HTML = os.path.join(CURRENT_DIR, "output", "DOAU_Management_Report_Oct2026.html")
OUTPUT_PDF = os.path.join(CURRENT_DIR, "output", "DOAU_Management_Report_Oct2026.pdf")
LOGO_FILE = os.path.join(CURRENT_DIR, "assets", "doau_logo.png")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    d = json.load(f)

# Helper formatting functions
def fmt(v, prefix="$", suffix="", dec=0):
    if v is None: return "N/A"
    v = float(v)
    neg = v < 0
    s = f"{abs(v):,.{dec}f}"
    result = f"{prefix}{s}{suffix}" if prefix else f"{s}{suffix}"
    return f"({result})" if neg else result

def fmt_k(v, prefix="$"):
    if v is None: return "N/A"
    v = float(v)
    neg = v < 0
    s = f"{abs(v)/1000:,.1f}k"
    result = f"{prefix}{s}" if prefix else s
    return f"({result})" if neg else result

def pct(v, dec=1):
    if v is None: return "N/A"
    val = float(v) * 100
    neg = val < 0
    s = f"{abs(val):.{dec}f}%"
    return f"({s})" if neg else s

def chg_cls(v):
    if v is None:
        return ""
    return "pos" if float(v) >= 0 else "neg"

# Data unpack
m_trend = d["monthly_trend"]
sep_oct = d["sep_vs_oct"]
ytd = d["ytd_summary"]
pl = d["pl_oct"]
bs = d["balance_sheet"]
ebitda_sch = d["ebitda_schedule"]
ar = d["ar_aging"]
ap = d["ap_aging"]
top_c = d["top_customers"]
top_i = d["top_items"]
inv = d["inventory_breakdown"]
cf = d["cash_flow"]
hr = d["hr_payroll"]
metrics = build_report_metrics(d)
report_period = metrics["report_period"]
prior_period = metrics["prior_period"]
report_year = report_period.split()[-1]

sales_trend_svg = svg_line_chart(m_trend, "revenue")

customer_pie_items = [
    {"name": customer["name"], "value": customer["sales"]}
    for customer in [item for item in top_c if item["sales"] > 0][:5]
]
customer_other_sales = metrics["positive_customer_sales_total"] - sum(item["value"] for item in customer_pie_items)
if customer_other_sales > 0:
    customer_pie_items.append({"name": "Other customers", "value": customer_other_sales})
customer_pie_svg = svg_pie_chart(
    customer_pie_items,
    f"{report_period} customer sales share",
    show_slice_percentages=True,
    bold_legend_percentages=True,
)
customer_top5_share = metrics["top_five_customer_share"]

inventory_pie_items = [
    {"name": item["name"], "value": item["asset_value"]}
    for item in sorted(
        (item for item in d["inventory_skus"] if item["asset_value"] > 0),
        key=lambda item: item["asset_value"],
        reverse=True,
    )[:5]
]
inventory_positive_total = sum(
    max(0.0, item["asset_value"]) for item in d["inventory_skus"]
)
inventory_other_value = inventory_positive_total - sum(item["value"] for item in inventory_pie_items)
if inventory_other_value > 0:
    inventory_pie_items.append({"name": "Other inventory SKUs", "value": inventory_other_value})
inventory_pie_svg = svg_pie_chart(
    inventory_pie_items,
    "Inventory share by SKU",
    legend_font_size=10,
    show_slice_percentages=True,
    bold_legend_percentages=True,
)
inventory_bs_difference = inv["bs_total_inventory"] - d["inventory_sku_total"]
inventory_reconciliation_note = (
    f"SKU detail total: {compact_money(d['inventory_sku_total'])}; "
    f"Balance Sheet inventory: {compact_money(inv['bs_total_inventory'])} "
    f"(difference {compact_money(inventory_bs_difference)}; not allocated to individual SKUs)."
)
negative_inventory_skus = sum(1 for item in d["inventory_skus"] if item["asset_value"] < 0)
if negative_inventory_skus:
    inventory_reconciliation_note += f" Other nets {negative_inventory_skus} negative-value SKU lines."

product_chart_items = top_i[:10]
product_sales_svg = svg_product_bars(product_chart_items, "sales")
product_profit_svg = svg_product_bars(product_chart_items, "gp", diverging=True)

# Generate HTML
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DOAU - Management Business Review ({escape_html(report_period)})</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 0;
  }}
  * {{
    box-sizing: border-box;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  body {{
    margin: 0;
    padding: 0;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    font-size: 8.5pt;
    line-height: 1.4;
    color: #1e293b;
    background: #f1f5f9;
  }}
  
  .page {{
    width: 210mm;
    height: 297mm;
    margin: 0 auto 10mm;
    background: #ffffff;
    padding: 12mm 14mm 10mm 14mm;
    position: relative;
    page-break-after: always;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  @media print {{
    body {{ background: transparent; }}
    .page {{ margin: 0; box-shadow: none; width: 210mm; height: 297mm; }}
    .export-controls {{ display: none !important; }}
    .chart-box {{ break-inside: avoid; page-break-inside: avoid; }}
  }}
  @media screen and (max-width: 900px) {{
    .page {{
      width: 100%;
      height: auto;
      min-height: 0;
      margin: 0 auto 12px;
      padding: 18px;
      overflow: visible;
    }}
    .two-col, .equal-two-col, .three-col {{
      display: block;
      height: auto;
    }}
    .inventory-two-col {{ display: block; }}
    .two-col > *, .equal-two-col > *, .three-col > * {{
      margin-bottom: 12px;
    }}
    .product-chart-grid {{ grid-template-columns: 1fr; }}
    .cfa-footer {{ flex-wrap: wrap; gap: 4px 12px; }}
    table.cfa-table {{ font-size: 7pt; }}
  }}
  .export-controls {{
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    justify-content: center;
    padding: 8px;
    background: #0b2545;
  }}
  .export-controls button {{
    border: 0;
    border-radius: 3px;
    padding: 8px 14px;
    background: #c9a84c;
    color: #0b2545;
    font: inherit;
    font-weight: 700;
    cursor: pointer;
  }}
  
  /* CFA Header Standard */
  .cfa-header {{
    border-bottom: 2px solid #0b2545;
    padding-bottom: 5px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }}
  .cfa-header .brand-title {{
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 13pt;
    font-weight: 800;
    color: #0b2545;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }}
  .cfa-header .brand-sub {{
    font-size: 7.5pt;
    font-weight: 600;
    color: #8b0000;
    text-transform: uppercase;
    letter-spacing: 0.8px;
  }}
  .cfa-header .doc-meta {{
    text-align: right;
    font-size: 7pt;
    color: #64748b;
    font-weight: 600;
    line-height: 1.3;
  }}
  
  /* CFA Footer Standard */
  .cfa-footer {{
    border-top: 1px solid #cbd5e1;
    padding-top: 4px;
    margin-top: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 6.8pt;
    color: #64748b;
  }}
  .cfa-footer .confidential {{
    font-weight: 700;
    color: #8b0000;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}

  /* Layout Columns */
  .content-body {{
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}
  .two-col {{
    display: grid;
    grid-template-columns: minmax(0, 32%) minmax(0, 66%);
    gap: 12px;
    height: 100%;
  }}
  .inventory-two-col {{
    grid-template-columns: minmax(0, 0.85fr) minmax(0, 1.15fr);
  }}
  .cash-flow-two-col {{
    grid-template-columns: minmax(0, 0.48fr) minmax(0, 0.52fr);
    height: auto;
  }}
  .equal-two-col {{
    display: grid;
    grid-template-columns: minmax(0, 48.5%) minmax(0, 48.5%);
    gap: 14px;
  }}
  .three-col {{
    display: grid;
    grid-template-columns: minmax(0, 31.5%) minmax(0, 31.5%) minmax(0, 33%);
    gap: 10px;
  }}
  
  /* Editorial Sidebars & Cards */
  .sidebar {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-top: 3px solid #0b2545;
    padding: 8px 10px;
    border-radius: 2px;
  }}
  .sidebar-crimson {{
    background: #fffafa;
    border: 1px solid #fecaca;
    border-top: 3px solid #8b0000;
    padding: 8px 10px;
    border-radius: 2px;
  }}
  
  /* Typography & Section Titles */
  .section-tag {{
    font-size: 6.8pt;
    font-weight: 800;
    color: #8b0000;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 2px;
  }}
  .section-title {{
    font-size: 11pt;
    font-weight: 800;
    color: #0b2545;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin: 0 0 6px 0;
    padding-bottom: 3px;
    border-bottom: 1.5px solid #0b2545;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }}
  .sub-title {{
    font-size: 8.5pt;
    font-weight: 700;
    color: #1e293b;
    margin: 6px 0 3px 0;
    border-left: 3px solid #0b2545;
    padding-left: 5px;
  }}
  .narrative-p {{
    font-size: 7.8pt;
    color: #334155;
    text-align: justify;
    margin: 0 0 6px 0;
    line-height: 1.42;
  }}
  
  /* Tables Standard */
  table.cfa-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 7.2pt;
    margin-bottom: 6px;
  }}
  table.cfa-table th {{
    background: #0b2545;
    color: #ffffff;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    font-size: 6.8pt;
    padding: 4px 5px;
    border: 1px solid #0b2545;
  }}
  table.cfa-table td {{
    padding: 3.5px 5px;
    border-bottom: 1px solid #e2e8f0;
    color: #1e293b;
  }}
  table.cfa-table tr:nth-child(even) td {{
    background: #f8fafc;
  }}
  table.cfa-table tr.total-row td {{
    background: #edf2f7;
    font-weight: 700;
    border-top: 1.5px solid #0b2545;
    border-bottom: 2px solid #0b2545;
    color: #0b2545;
  }}
  table.cfa-table tr.sub-total td {{
    background: #f1f5f9;
    font-weight: 700;
    border-top: 1px solid #94a3b8;
  }}
  td.num, th.num {{
    text-align: right;
    font-variant-numeric: tabular-nums;
  }}
  td.center, th.center {{
    text-align: center;
  }}
  
  /* KPI Blocks */
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
    margin-bottom: 8px;
  }}
  .kpi-card {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 3px solid #0b2545;
    padding: 5px 7px;
  }}
  .kpi-card.alert {{
    border-left-color: #8b0000;
    background: #fffafa;
  }}
  .kpi-card .kpi-label {{
    font-size: 6.5pt;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
  }}
  .kpi-card .kpi-val {{
    font-size: 11pt;
    font-weight: 800;
    color: #0b2545;
    line-height: 1.2;
    margin: 2px 0;
  }}
  .kpi-card.alert .kpi-val {{
    color: #8b0000;
  }}
  .kpi-card .kpi-sub {{
    font-size: 6.5pt;
    color: #64748b;
  }}

  /* Colors and Statuses */
  .pos {{ color: #166534; font-weight: 600; }}
  .neg {{ color: #991b1b; font-weight: 600; }}
  .badge-tag {{
    display: inline-block;
    padding: 1px 4px;
    font-size: 6.2pt;
    font-weight: 700;
    border-radius: 2px;
    text-transform: uppercase;
  }}
  .badge-interco {{ background: #e0e7ff; color: #3730a3; }}
  .badge-3rd {{ background: #f1f5f9; color: #475569; }}
  .badge-adv {{ background: #fee2e2; color: #991b1b; }}

  /* Bars for SVG/Visuals */
  .chart-box {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    min-width: 0;
    padding: 8px;
    margin-bottom: 8px;
    border-radius: 2px;
  }}
  .chart-title {{
    font-size: 8pt;
    font-weight: 700;
    color: #0b2545;
    margin-bottom: 6px;
    text-transform: uppercase;
  }}
  .report-chart {{
    display: block;
    width: 100%;
    height: auto;
    max-width: 100%;
  }}
  .product-chart-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }}
  .commercial-two-col {{
    grid-template-columns: 44% 1fr;
    gap: 10px;
    height: auto;
  }}
  .chart-note {{
    font-size: 7pt;
    color: #64748b;
    line-height: 1.3;
    margin-top: 3px;
  }}
</style>
</head>
<body>
<div class="export-controls">
  <button type="button" onclick="window.print()">Export Management Report to PDF</button>
</div>
"""

# ============================================================
# PAGE 1: COVER & EXECUTIVE SUMMARY
# ============================================================
gm_oct_pct = metrics["month_gross_margin"]
gm_ytd_pct = metrics["ytd_gross_margin"]
cur_ratio = metrics["current_ratio"]
de_ratio = metrics["debt_equity_ratio"]

html += f"""
<!-- PAGE 1: EXECUTIVE SUMMARY -->
<div class="page">
  <div>
    <div class="cfa-header">
      <div>
        <div class="brand-title">Dan-D Foods, LLC (DOAU)</div>
        <div class="brand-sub">Management Business Review | Executive Summary</div>
      </div>
      <div class="doc-meta">
        <div>Reporting Period: <strong>{escape_html(report_period)}</strong></div>
        <div>Standard: <strong>A4 Portrait Financial Briefing</strong></div>
        <div>Currency: <strong>USD ($)</strong></div>
      </div>
    </div>

    <div class="content-body">
      <div class="two-col">
        <!-- Left Sidebar: Key Executive Metrics -->
        <div class="sidebar">
          <div class="section-tag">Corporate Profile</div>
          <div style="font-size:8pt; font-weight:700; color:#0b2545; margin-bottom:6px;">Dan-D Foods (USA) Operations</div>
          
          <div class="kpi-grid">
            <div class="kpi-card">
              <div class="kpi-label">YTD {escape_html(report_year)} Rev</div>
              <div class="kpi-val">{fmt_k(ytd['revenue_ytd26'])}</div>
              <div class="kpi-sub">YoY: {pct(ytd['revenue_chg_pct'])}</div>
            </div>
            <div class="kpi-card alert">
              <div class="kpi-label">YTD Gross Margin</div>
              <div class="kpi-val">{pct(gm_ytd_pct)}</div>
              <div class="kpi-sub">GP: {fmt_k(ytd['gross_profit_ytd26'])}</div>
            </div>
            <div class="kpi-card alert">
              <div class="kpi-label">{escape_html(report_period)} Rev</div>
              <div class="kpi-val">{fmt_k(pl['revenue_oct'])}</div>
              <div class="kpi-sub">MoM: {pct(metrics['monthly_revenue_change_pct'])} vs {escape_html(prior_period or 'prior month')}</div>
            </div>
            <div class="kpi-card alert">
              <div class="kpi-label">{escape_html(report_period)} Gross Margin</div>
              <div class="kpi-val">{pct(gm_oct_pct)}</div>
              <div class="kpi-sub">GP: {fmt_k(pl['gross_profit_oct'])}</div>
            </div>
          </div>

          <div class="section-tag" style="margin-top:8px;">Balance Sheet & Solvency</div>
          <table class="cfa-table" style="margin-top:4px;">
            <tr><td>Total Assets</td><td class="num font-bold">{fmt_k(bs['total_assets'])}</td></tr>
            <tr><td>Cash & Equivalents</td><td class="num">{fmt_k(bs['cash_and_equiv'])}</td></tr>
            <tr><td>AR (Net of Bad Debt)</td><td class="num">{fmt_k(bs['ar_net'])}</td></tr>
            <tr><td>Inventory Asset</td><td class="num">{fmt_k(bs['inventory'])}</td></tr>
            <tr><td>Total Liabilities</td><td class="num">{fmt_k(bs['total_liabilities'])}</td></tr>
            <tr><td>Total Equity</td><td class="num">{fmt_k(bs['total_equity'])}</td></tr>
            <tr><td>Current Ratio</td><td class="num font-bold">{f'{cur_ratio:.2f}x' if cur_ratio is not None else 'N/A'}</td></tr>
            <tr><td>Debt / Equity</td><td class="num font-bold">{f'{de_ratio:.2f}x' if de_ratio is not None else 'N/A'}</td></tr>
          </table>

          <div class="sidebar-crimson" style="margin-top:6px;">
            <div class="section-tag" style="color:#8b0000;">Margin Snapshot</div>
            <div style="font-size:7pt; color:#7f1d1d; line-height:1.35;">
              Gross margin is {pct(gm_ytd_pct)} YTD and {pct(gm_oct_pct)} for {escape_html(report_period)}. Direct labor and factory overhead are reported cost components; this comparison does not establish a single cause for the margin result.
            </div>
          </div>
        </div>

        <!-- Right Main Body: Executive Commentary & Agenda -->
        <div>
          <div class="section-title">
            <span>Executive Business Review</span>
            <span style="font-size:7pt; color:#64748b; font-weight:600;">Analysis: local workbook metrics and rules; management review required</span>
          </div>

          <p class="narrative-p">
            <strong>1. Revenue Performance:</strong> YTD net revenue through {escape_html(report_period)} was <strong>{fmt(ytd['revenue_ytd26'])}</strong> versus {fmt(ytd['revenue_ytd25'])} in the comparable prior-year period, a change of <strong>{fmt(metrics['ytd_revenue_change'])} ({pct(metrics['ytd_revenue_change_pct'])})</strong>. Revenue for {escape_html(report_period)} was {fmt(pl['revenue_oct'])}, with a month-over-month change of {pct(metrics['monthly_revenue_change_pct'])}.
          </p>

          <p class="narrative-p">
            <strong>2. Margin:</strong> {escape_html(report_period)} gross profit was <strong>{fmt(pl['gross_profit_oct'])}</strong> ({pct(gm_oct_pct)} gross margin). YTD gross profit was {fmt(ytd['gross_profit_ytd26'])}; the comparable prior-year amount was {fmt(ytd['gross_profit_ytd25'])}. These figures describe reported outcomes and do not assign causality.
          </p>

          <p class="narrative-p">
            <strong>3. EBITDA Measures:</strong> Operational EBITDA from the monthly data is {fmt(ebitda_sch['operational_ebitda']['oct'])} for {escape_html(report_period)} and {fmt(ebitda_sch['operational_ebitda']['ytd'])} YTD. The separate management adjustment schedule reports adjusted EBITDA of {fmt(ebitda_sch['oct']['adjusted_ebitda'])} for the month and {fmt(ebitda_sch['ytd']['adjusted_ebitda'])} YTD. These are distinct measures; review the schedule's add-backs before relying on the adjusted figure.
          </p>

          <div class="chart-box" style="margin-top:6px;">
            <div class="chart-title">Monthly Sales Trend — {escape_html(m_trend[0]['month'])} to {escape_html(report_period)}</div>
            {sales_trend_svg}
            <div class="chart-note">USD; MoM changes are calculated from monthly net revenue. Source: 007-DOAU data sheet.</div>
          </div>

          <div class="sub-title">Review Agenda & Meeting Sequence</div>
          <table class="cfa-table">
            <thead>
              <tr>
                <th style="width:25%;">Section</th>
                <th style="width:50%;">Analytical Scope & Key Inclusions</th>
                <th style="width:25%;" class="num">Page Ref</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><strong>1. Executive Summary</strong></td><td>Comprehensive snapshot, key ratios, performance scorecard</td><td class="num">Page 1</td></tr>
              <tr><td><strong>2. Sales Report</strong></td><td>YTD sales variance and management review questions</td><td class="num">Page 2</td></tr>
              <tr><td><strong>3. Performance Variance</strong></td><td>Prior-period comparison and YTD financial review</td><td class="num">Page 3</td></tr>
              <tr><td><strong>4. Commercial Analysis</strong></td><td>Customer and product sales, gross profit and margin</td><td class="num">Page 4</td></tr>
              <tr><td><strong>5. Operations & P&L</strong></td><td>Inventory reconciliation, monthly P&L and EBITDA schedule</td><td class="num">Page 5</td></tr>
              <tr><td><strong>6. Balance Sheet & WC</strong></td><td>Balance sheet and AR/AP aging schedules</td><td class="num">Page 6</td></tr>
              <tr><td><strong>7. Capex & Cash Flows</strong></td><td>Fixed-asset balances and parsed cash-flow statement</td><td class="num">Page 7</td></tr>
              <tr><td><strong>8. HR Cost Analysis</strong></td><td>Payroll amounts and mix; no headcount data in source</td><td class="num">Page 8</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <div class="cfa-footer">
    <div>Dan-D Foods, LLC | Management Business Review</div>
    <div class="confidential">CONFIDENTIAL — FOR MANAGEMENT USE ONLY</div>
    <div>Page 1 of 8</div>
  </div>
</div>
"""

# ============================================================
# PAGE 2: SALES REPORT (YTD Sales Update & Action Plans)
# ============================================================
html += f"""
<!-- PAGE 2: SALES REPORT -->
<div class="page">
  <div>
    <div class="cfa-header">
      <div>
        <div class="brand-title">Dan-D Foods, LLC (DOAU)</div>
        <div class="brand-sub">Sales Report | YTD Sales Performance & Action Plans</div>
      </div>
      <div class="doc-meta">
        <div>Reporting Period: <strong>{escape_html(report_period)}</strong></div>
        <div>Agenda Item: <strong>Sale Report (1/2)</strong></div>
      </div>
    </div>

    <div class="content-body">
      <div class="two-col">
        <!-- Left: Sales Scorecard -->
        <div class="sidebar">
          <div class="section-tag">Sales Highlights</div>
          <div class="kpi-grid">
            <div class="kpi-card">
              <div class="kpi-label">YTD 26 Sales</div>
              <div class="kpi-val">{fmt_k(ytd['sales_ytd26'])}</div>
              <div class="kpi-sub">vs {fmt_k(ytd['sales_ytd25'])} YTD prior year</div>
            </div>
            <div class="kpi-card alert">
              <div class="kpi-label">Sales Variance</div>
              <div class="kpi-val">{fmt_k(ytd['sales_ytd26'] - ytd['sales_ytd25'])}</div>
              <div class="kpi-sub">{pct(percent_change(ytd['sales_ytd26'], ytd['sales_ytd25']))} vs prior year</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-label">Custom Proc.</div>
              <div class="kpi-val">{fmt(ytd['custom_proc_ytd26'])}</div>
              <div class="kpi-sub">Prior: {fmt(ytd['custom_proc_ytd25'])}</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-label">Discounts Given</div>
              <div class="kpi-val">{fmt(ytd['discounts_ytd26'])}</div>
              <div class="kpi-sub">Prior: {fmt(ytd['discounts_ytd25'])}</div>
            </div>
          </div>

          <div class="sub-title">10-Month Sales Trajectory</div>
          <table class="cfa-table">
            <thead>
              <tr><th>Month</th><th class="num">Revenue</th><th class="num">MoM</th></tr>
            </thead>
            <tbody>
              {''.join([f'''<tr>
                <td>{m['month']}</td>
                <td class="num">{fmt_k(m['revenue'])}</td>
                <td class="num {chg_cls((m['revenue'] - m_trend[i-1]['revenue']) if i > 0 else 0)}">
                  {pct(percent_change(m['revenue'], m_trend[i-1]['revenue'])) if i > 0 else '-'}
                </td>
              </tr>''' for i, m in enumerate(m_trend)])}
            </tbody>
          </table>

          <div class="sidebar-crimson" style="margin-top:6px;">
            <div class="section-tag" style="color:#8b0000;">Customer Concentration Risk</div>
            <div style="font-size:7pt; color:#7f1d1d; line-height:1.35;">
              The top three customers represent <strong>{pct(metrics['top_three_customer_share'])} of positive customer sales</strong>. This is a concentration measure, not a forecast of future sales.
            </div>
          </div>
        </div>

        <!-- Right: Analytical Narrative & Action Plans -->
        <div>
          <div class="section-title">
            <span>YTD Sales Performance Analysis</span>
            <span style="font-size:7pt; color:#64748b;">YTD through {escape_html(report_period)} vs prior year</span>
          </div>

          <p class="narrative-p">
            <strong>YTD Revenue Comparison:</strong> Net revenue was {fmt(ytd['revenue_ytd26'])} versus {fmt(ytd['revenue_ytd25'])} in the comparable prior-year period, a change of <strong>{fmt(metrics['ytd_revenue_change'])} ({pct(metrics['ytd_revenue_change_pct'])})</strong>. Product sales changed by {fmt(ytd['sales_ytd26'] - ytd['sales_ytd25'])}; custom processing changed by {fmt(ytd['custom_proc_ytd26'] - ytd['custom_proc_ytd25'])}. The workbook reports totals but does not attribute the change to price, volume or mix.
          </p>

          <p class="narrative-p">
            <strong>Monthly Trend:</strong> {escape_html(report_period)} net revenue was {fmt(pl['revenue_oct'])} ({pct(metrics['monthly_revenue_change_pct'])} versus {escape_html(prior_period or 'the prior month')}). Discount amounts are shown in the P&amp;L comparison; no pricing or freight cause is inferred from those figures alone.
          </p>

          <div class="section-title" style="margin-top:10px;">
            <span>Management Review Questions</span>
            <span style="font-size:7pt; color:#8b0000;">Based on reported workbook metrics</span>
          </div>

          <table class="cfa-table">
            <thead>
              <tr>
                <th style="width:24%;">Review Area</th>
                <th style="width:58%;">Data Observation & Follow-up Question</th>
                <th style="width:18%;">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>YTD Revenue</strong></td>
                <td>Revenue changed {fmt(metrics['ytd_revenue_change'])} ({pct(metrics['ytd_revenue_change_pct'])}) year over year. Confirm price, volume and mix drivers with commercial owners.</td>
                <td>Review</td>
              </tr>
              <tr>
                <td><strong>Customer Mix</strong></td>
                <td>The top three customers account for {pct(metrics['top_three_customer_share'])} of positive customer sales. Review account concentration and contingency planning.</td>
                <td>Review</td>
              </tr>
              <tr>
                <td><strong>Product Margin</strong></td>
                <td>Validate product costing and pricing for low-margin items before deciding corrective actions. Product-level results are from the GP sheet.</td>
                <td>Validate</td>
              </tr>
              <tr>
                <td><strong>Inventory</strong></td>
                <td>INV SKU detail and the Balance Sheet inventory total do not match; review the reported reconciliation difference on page 5.</td>
                <td>Reconcile</td>
              </tr>
              <tr>
                <td><strong>Cash Conversion</strong></td>
                <td>YTD operating cash flow is {fmt(cf['net_cfo'])}; review the cash-flow components and working-capital movements on page 7.</td>
                <td>Review</td>
              </tr>
            </tbody>
          </table>

          <div class="chart-box" style="margin-top:8px;">
            <div class="chart-title">Customer Sales Share — Top 5 + Other</div>
            {customer_pie_svg}
            <div class="chart-note">Top five are {pct(customer_top5_share)} of positive customer sales. Negative customer balances are excluded from the share calculation; source: Sales by cust sheet.</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="cfa-footer">
    <div>Dan-D Foods, LLC | Management Business Review</div>
    <div class="confidential">CONFIDENTIAL — FOR MANAGEMENT USE ONLY</div>
    <div>Page 2 of 8</div>
  </div>
</div>
"""

# ============================================================
# PAGE 3: FINANCIAL REPORT — Sep Performance & YTD Performance
# ============================================================
sep_rev = sep_oct["revenue"]["sep"]
oct_rev = sep_oct["revenue"]["oct"]
sep_gp = sep_oct["gross_profit"]["sep"]
oct_gp = sep_oct["gross_profit"]["oct"]
sep_cogs = sep_oct["cogs"]["sep"]
oct_cogs = sep_oct["cogs"]["oct"]
sep_opex = sep_oct["total_opex"]["sep"]
oct_opex = sep_oct["total_opex"]["oct"]
sep_netop = sep_oct["net_operating_income"]["sep"]
oct_netop = sep_oct["net_operating_income"]["oct"]
sep_ebitda = sep_oct["ebitda"]["sep"]
oct_ebitda = sep_oct["ebitda"]["oct"]

html += f"""
<!-- PAGE 3: FINANCIAL REPORT (Sep vs Oct & YTD) -->
<div class="page">
  <div>
    <div class="cfa-header">
      <div>
        <div class="brand-title">Dan-D Foods, LLC (DOAU)</div>
        <div class="brand-sub">Financial Report | {escape_html(prior_period or 'Prior Period')} Performance & YTD Statement Analysis</div>
      </div>
      <div class="doc-meta">
        <div>Reporting Period: <strong>{escape_html(report_period)}</strong></div>
        <div>Agenda Item: <strong>Financial Report (1/5)</strong></div>
      </div>
    </div>

    <div class="content-body">
      <div class="two-col">
        <!-- Left: MoM Summary Column -->
        <div class="sidebar">
          <div class="section-tag">Month-over-Month Variance</div>
          <div style="font-size:8pt; font-weight:700; color:#0b2545; margin-bottom:6px;">{escape_html(prior_period or 'Prior Period')} vs {escape_html(report_period)}</div>

          <table class="cfa-table">
            <thead>
              <tr><th>Metric</th><th class="num">{escape_html(prior_period or 'Prior')}</th><th class="num">{escape_html(report_period)}</th><th class="num">MoM $</th></tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Revenue</strong></td>
                <td class="num">{fmt_k(sep_rev)}</td>
                <td class="num">{fmt_k(oct_rev)}</td>
                <td class="num {chg_cls(oct_rev - sep_rev)}">{fmt_k(oct_rev - sep_rev)}</td>
              </tr>
              <tr>
                <td><strong>COGS</strong></td>
                <td class="num">{fmt_k(sep_cogs)}</td>
                <td class="num">{fmt_k(oct_cogs)}</td>
                <td class="num pos">{fmt_k(oct_cogs - sep_cogs)}</td>
              </tr>
              <tr>
                <td><strong>Gross Profit</strong></td>
                <td class="num {chg_cls(sep_gp)}">{fmt_k(sep_gp)}</td>
                <td class="num {chg_cls(oct_gp)}">{fmt_k(oct_gp)}</td>
                <td class="num neg">{fmt_k(oct_gp - sep_gp)}</td>
              </tr>
              <tr>
                <td>Gross Margin %</td>
                <td class="num {chg_cls(sep_gp)}">{pct(safe_divide(sep_gp, sep_rev))}</td>
                <td class="num {chg_cls(oct_gp)}">{pct(safe_divide(oct_gp, oct_rev))}</td>
                <td class="num">{pct((safe_divide(oct_gp, oct_rev) - safe_divide(sep_gp, sep_rev)) if safe_divide(oct_gp, oct_rev) is not None and safe_divide(sep_gp, sep_rev) is not None else None)}</td>
              </tr>
              <tr>
                <td>Admin Exp</td>
                <td class="num">{fmt_k(sep_oct['admin_exp']['sep'])}</td>
                <td class="num">{fmt_k(sep_oct['admin_exp']['oct'])}</td>
                <td class="num pos">{fmt_k(sep_oct['admin_exp']['oct'] - sep_oct['admin_exp']['sep'])}</td>
              </tr>
              <tr>
                <td>Sales Exp</td>
                <td class="num">{fmt_k(sep_oct['sales_exp']['sep'])}</td>
                <td class="num">{fmt_k(oct_oct := sep_oct['sales_exp']['oct'])}</td>
                <td class="num pos">{fmt_k(oct_oct - sep_oct['sales_exp']['sep'])}</td>
              </tr>
              <tr class="sub-total">
                <td><strong>Total Opex</strong></td>
                <td class="num">{fmt_k(sep_opex)}</td>
                <td class="num">{fmt_k(oct_opex)}</td>
                <td class="num pos">{fmt_k(oct_opex - sep_opex)}</td>
              </tr>
              <tr class="total-row">
                <td><strong>Operating Loss</strong></td>
                <td class="num {chg_cls(sep_netop)}">{fmt_k(sep_netop)}</td>
                <td class="num {chg_cls(oct_netop)}">{fmt_k(oct_netop)}</td>
                <td class="num neg">{fmt_k(oct_netop - sep_netop)}</td>
              </tr>
              <tr>
                <td><strong>EBITDA (Op)</strong></td>
                <td class="num {chg_cls(sep_ebitda)}">{fmt_k(sep_ebitda)}</td>
                <td class="num {chg_cls(oct_ebitda)}">{fmt_k(oct_ebitda)}</td>
                <td class="num neg">{fmt_k(oct_ebitda - sep_ebitda)}</td>
              </tr>
            </tbody>
          </table>

          <div class="sidebar-crimson" style="margin-top:6px;">
            <div class="section-tag" style="color:#8b0000;">Month-over-Month Observation</div>
            <div style="font-size:7pt; color:#7f1d1d; line-height:1.35;">
              Revenue changed {fmt(oct_rev - sep_rev)} ({pct(percent_change(oct_rev, sep_rev))}) from {escape_html(prior_period or 'the prior month')} to {escape_html(report_period)}. Gross profit changed {fmt(oct_gp - sep_gp)}. These comparisons do not identify the operational drivers.
            </div>
          </div>
        </div>

        <!-- Right: YTD Comprehensive Financial Statement -->
        <div>
          <div class="section-title">
            <span>YTD Performance through {escape_html(report_period)} vs prior year</span>
            <span style="font-size:7pt; color:#64748b;">Source: PL YTD Aug 26 Sheet</span>
          </div>

          <table class="cfa-table">
            <thead>
              <tr>
                <th style="width:36%;">Financial Line Item ($)</th>
                <th style="width:16%;" class="num">YTD {escape_html(report_year)}</th>
                <th style="width:16%;" class="num">YTD {int(report_year) - 1}</th>
                <th style="width:16%;" class="num">Variance ($)</th>
                <th style="width:16%;" class="num">% Change</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Product Sales</td>
                <td class="num">{fmt(ytd['sales_ytd26'])}</td>
                <td class="num">{fmt(ytd['sales_ytd25'])}</td>
                <td class="num neg">{fmt(ytd['sales_ytd26'] - ytd['sales_ytd25'])}</td>
                <td class="num">{pct(percent_change(ytd['sales_ytd26'], ytd['sales_ytd25']))}</td>
              </tr>
              <tr>
                <td>Custom Processing Fees</td>
                <td class="num">{fmt(ytd['custom_proc_ytd26'])}</td>
                <td class="num">{fmt(ytd['custom_proc_ytd25'])}</td>
                <td class="num neg">{fmt(ytd['custom_proc_ytd26'] - ytd['custom_proc_ytd25'])}</td>
                <td class="num">{pct(percent_change(ytd['custom_proc_ytd26'], ytd['custom_proc_ytd25']))}</td>
              </tr>
              <tr>
                <td>Discounts Allowed</td>
                <td class="num">{fmt(ytd['discounts_ytd26'])}</td>
                <td class="num">{fmt(ytd['discounts_ytd25'])}</td>
                <td class="num pos">{fmt(ytd['discounts_ytd26'] - ytd['discounts_ytd25'])}</td>
                <td class="num">{pct(percent_change(ytd['discounts_ytd26'], ytd['discounts_ytd25']))}</td>
              </tr>
              <tr class="sub-total">
                <td><strong>TOTAL REVENUE</strong></td>
                <td class="num font-bold">{fmt(ytd['revenue_ytd26'])}</td>
                <td class="num font-bold">{fmt(ytd['revenue_ytd25'])}</td>
                <td class="num font-bold neg">{fmt(ytd['revenue_chg'])}</td>
                <td class="num font-bold neg">{pct(ytd['revenue_chg_pct'])}</td>
              </tr>
              <tr>
                <td>Direct Labor</td>
                <td class="num">{fmt(ytd['direct_labor_ytd26'])}</td>
                <td class="num">{fmt(ytd['direct_labor_ytd25'])}</td>
                <td class="num pos">{fmt(ytd['direct_labor_ytd26'] - ytd['direct_labor_ytd25'])}</td>
                <td class="num">{pct(percent_change(ytd['direct_labor_ytd26'], ytd['direct_labor_ytd25']))}</td>
              </tr>
              <tr>
                <td>Factory Overhead</td>
                <td class="num">{fmt(ytd['factory_oh_ytd26'])}</td>
                <td class="num">{fmt(ytd['factory_oh_ytd25'])}</td>
                <td class="num pos">{fmt(ytd['factory_oh_ytd26'] - ytd['factory_oh_ytd25'])}</td>
                <td class="num">{pct(percent_change(ytd['factory_oh_ytd26'], ytd['factory_oh_ytd25']))}</td>
              </tr>
              <tr class="sub-total">
                <td><strong>COST OF GOODS SOLD</strong></td>
                <td class="num font-bold">{fmt(ytd['cogs_ytd26'])}</td>
                <td class="num font-bold">{fmt(ytd['cogs_ytd25'])}</td>
                <td class="num font-bold pos">{fmt(ytd['cogs_ytd26'] - ytd['cogs_ytd25'])}</td>
                <td class="num font-bold">{pct(percent_change(ytd['cogs_ytd26'], ytd['cogs_ytd25']))}</td>
              </tr>
              <tr class="total-row">
                <td><strong>GROSS PROFIT / (LOSS)</strong></td>
                <td class="num font-bold {chg_cls(ytd['gross_profit_ytd26'])}">{fmt(ytd['gross_profit_ytd26'])}</td>
                <td class="num font-bold {chg_cls(ytd['gross_profit_ytd25'])}">{fmt(ytd['gross_profit_ytd25'])}</td>
                <td class="num font-bold neg">{fmt(ytd['gross_profit_ytd26'] - ytd['gross_profit_ytd25'])}</td>
                <td class="num font-bold">{pct(percent_change(ytd['gross_profit_ytd26'], ytd['gross_profit_ytd25']))}</td>
              </tr>
              <tr>
                <td>Gross Margin %</td>
                <td class="num font-bold {chg_cls(ytd['gross_profit_ytd26'])}">{pct(gm_ytd_pct)}</td>
                <td class="num font-bold pos">{pct(metrics['prior_ytd_gross_margin'])}</td>
                <td class="num font-bold">{pct((gm_ytd_pct - metrics['prior_ytd_gross_margin']) if gm_ytd_pct is not None and metrics['prior_ytd_gross_margin'] is not None else None)} pts</td>
                <td class="num font-bold neg">-</td>
              </tr>
              <tr>
                <td>Administration Expenses</td>
                <td class="num">{fmt(ytd['admin_exp_ytd26'])}</td>
                <td class="num">{fmt(ytd['admin_exp_ytd25'])}</td>
                <td class="num pos">{fmt(ytd['admin_exp_ytd26'] - ytd['admin_exp_ytd25'])}</td>
                <td class="num">{pct(percent_change(ytd['admin_exp_ytd26'], ytd['admin_exp_ytd25']))}</td>
              </tr>
              <tr>
                <td>Sales & Distribution Expenses</td>
                <td class="num">{fmt(ytd['sales_exp_ytd26'])}</td>
                <td class="num">{fmt(ytd['sales_exp_ytd25'])}</td>
                <td class="num pos">{fmt(ytd['sales_exp_ytd26'] - ytd['sales_exp_ytd25'])}</td>
                <td class="num">{pct(percent_change(ytd['sales_exp_ytd26'], ytd['sales_exp_ytd25']))}</td>
              </tr>
              <tr class="sub-total">
                <td><strong>TOTAL OPERATING EXPENSES</strong></td>
                <td class="num font-bold">{fmt(ytd['total_opex_ytd26'])}</td>
                <td class="num font-bold">{fmt(ytd['total_opex_ytd25'])}</td>
                <td class="num font-bold pos">{fmt(ytd['total_opex_ytd26'] - ytd['total_opex_ytd25'])}</td>
                <td class="num font-bold">{pct(percent_change(ytd['total_opex_ytd26'], ytd['total_opex_ytd25']))}</td>
              </tr>
              <tr class="total-row">
                <td><strong>NET ORDINARY INCOME / (LOSS)</strong></td>
                <td class="num font-bold {chg_cls(ytd['net_ordinary_income_ytd26'])}">{fmt(ytd['net_ordinary_income_ytd26'])}</td>
                <td class="num font-bold {chg_cls(ytd['net_ordinary_income_ytd25'])}">{fmt(ytd['net_ordinary_income_ytd25'])}</td>
                <td class="num font-bold neg">{fmt(ytd['net_ordinary_income_ytd26'] - ytd['net_ordinary_income_ytd25'])}</td>
                <td class="num font-bold neg">-</td>
              </tr>
              <tr>
                <td>Interest Expense</td>
                <td class="num">{fmt(ytd['interest_exp_ytd26'])}</td>
                <td class="num">{fmt(ytd['interest_exp_ytd25'])}</td>
                <td class="num pos">{fmt(ytd['interest_exp_ytd26'] - ytd['interest_exp_ytd25'])}</td>
                <td class="num">{pct(percent_change(ytd['interest_exp_ytd26'], ytd['interest_exp_ytd25']))}</td>
              </tr>
              <tr class="total-row" style="background:#0b2545; color:white;">
                <td style="color:white;"><strong>NET INCOME / (LOSS)</strong></td>
                <td class="num font-bold" style="color:white;">{fmt(ytd['net_income_ytd26'])}</td>
                <td class="num font-bold" style="color:white;">{fmt(ytd['net_income_ytd25'])}</td>
                <td class="num font-bold" style="color:#fca5a5;">{fmt(ytd['net_income_ytd26'] - ytd['net_income_ytd25'])}</td>
                <td class="num font-bold" style="color:#fca5a5;">-</td>
              </tr>
            </tbody>
          </table>

          <p class="narrative-p" style="margin-top:6px;">
            <strong>Analytical Commentary:</strong> YTD net income changed {fmt(ytd['net_income_ytd26'] - ytd['net_income_ytd25'])} versus the prior year. Gross profit changed {fmt(ytd['gross_profit_ytd26'] - ytd['gross_profit_ytd25'])}, while total operating expenses changed {fmt(ytd['total_opex_ytd26'] - ytd['total_opex_ytd25'])}. Monthly gross profit summed from 007-DOAU data is {fmt(metrics['monthly_gross_profit_total'])}; the YTD P&amp;L reports {fmt(ytd['gross_profit_ytd26'])}, a difference of {fmt(metrics['monthly_ytd_gross_profit_difference'])} that requires reconciliation. The commentary does not infer a single cause or prescribe a target.
          </p>
        </div>
      </div>
    </div>
  </div>

  <div class="cfa-footer">
    <div>Dan-D Foods, LLC | Management Business Review</div>
    <div class="confidential">CONFIDENTIAL — FOR MANAGEMENT USE ONLY</div>
    <div>Page 3 of 8</div>
  </div>
</div>
"""

# ============================================================
# PAGE 4: COMMERCIAL REPORT — Margin, Top Customers & Top Items
# ============================================================
html += f"""
<!-- PAGE 4: COMMERCIAL ANALYSIS -->
<div class="page">
  <div>
    <div class="cfa-header">
      <div>
        <div class="brand-title">Dan-D Foods, LLC (DOAU)</div>
        <div class="brand-sub">Commercial Analysis | Margins, Top Customers & Product Performance</div>
      </div>
      <div class="doc-meta">
        <div>Reporting Period: <strong>{escape_html(report_period)}</strong></div>
        <div>Agenda Item: <strong>Financial Report (2/5)</strong></div>
      </div>
    </div>

    <div class="content-body">
      <div class="two-col commercial-two-col">
        <!-- Left: Top Customers Ranking -->
        <div>
          <div class="section-title">
            <span>Top Customer Analysis</span>
            <span style="font-size:7pt; color:#64748b;">{escape_html(report_period)}</span>
          </div>

          <table class="cfa-table">
            <thead>
              <tr>
                <th style="width:38%;">Customer Name</th>
                <th style="width:22%;" class="num">Sales ($)</th>
                <th style="width:22%;" class="num">GP ($)</th>
                <th style="width:18%;" class="num">GM %</th>
              </tr>
            </thead>
            <tbody>
              {''.join([f'''<tr>
                <td>{escape_html(c['name'][:24])}</td>
                <td class="num">{fmt(c['sales'])}</td>
                <td class="num {chg_cls(c['gp'])}">{fmt(c['gp'])}</td>
                <td class="num {chg_cls(c['gm_pct'])}">{pct(c['gm_pct'])}</td>
              </tr>''' for c in top_c[:10]])}
              <tr class="total-row">
                <td><strong>Top 10 Total</strong></td>
                <td class="num"><strong>{fmt(sum(c['sales'] for c in top_c[:10]))}</strong></td>
                <td class="num {chg_cls(sum(c['gp'] for c in top_c[:10]))}"><strong>{fmt(sum(c['gp'] for c in top_c[:10]))}</strong></td>
                <td class="num"><strong>{pct(safe_divide(sum(c['gp'] for c in top_c[:10]), sum(c['sales'] for c in top_c[:10])))}</strong></td>
              </tr>
            </tbody>
          </table>

          <div class="sidebar-crimson" style="margin-top:6px;">
            <div class="section-tag" style="color:#8b0000;">Customer Sales Observation</div>
            <div style="font-size:7pt; color:#7f1d1d; line-height:1.35;">
              {f"Highest reported customer sales were {fmt(metrics['top_customer']['sales'])} for {escape_html(metrics['top_customer']['name'])}." if metrics['top_customer'] else "No customer sales rows were available."} Customer gross profit and margin are reported values; confirm cost allocation before acting on individual account results.
            </div>
          </div>
        </div>

        <!-- Right: Margin Analysis & Top Items -->
        <div>
          <div class="section-title">
            <span>Top Product Items Analysis</span>
            <span style="font-size:7pt; color:#64748b;">{escape_html(report_period)} (Sheet: GP)</span>
          </div>

          <div class="chart-box">
            <div class="chart-title">Product Sales — Top 10 by USD</div>
            {product_sales_svg}
            <div class="chart-note">Source: GP sheet, {escape_html(report_period)}; the top 10 are ranked by reported sales.</div>
          </div>
          <div class="chart-box">
            <div class="chart-title">Gross Profit — Same Top 10 Products</div>
            {product_profit_svg}
            <div class="chart-note">Source: GP sheet, {escape_html(report_period)}; gross profit uses the same product set as the sales chart.</div>
          </div>

          <div class="section-title" style="margin-top:8px;">
            <span>Margin & Pricing Diagnostics</span>
            <span style="font-size:7pt; color:#64748b;">Operational Variance Factors</span>
          </div>

          <p class="narrative-p">
            <strong>Highest Gross Profit:</strong> {f"{escape_html(metrics['highest_gp_item']['name'])} recorded {fmt(metrics['highest_gp_item']['gp'])} gross profit ({pct(metrics['highest_gp_item']['gm_pct'])} margin)." if metrics['highest_gp_item'] else "No positive-sales item was available for comparison."} Source: GP sheet; reported gross profit is not a pricing recommendation.
          </p>

          <p class="narrative-p">
            <strong>Lowest Recorded Margin:</strong> {f"{escape_html(metrics['lowest_margin_item']['name'])} recorded {pct(metrics['lowest_margin_item']['gm_pct'])} gross margin on {fmt(metrics['lowest_margin_item']['sales'])} sales." if metrics['lowest_margin_item'] else "No positive-sales item was available for comparison."} Confirm item-level cost and allocation assumptions before interpreting this result.
          </p>
        </div>
      </div>
    </div>
  </div>

  <div class="cfa-footer">
    <div>Dan-D Foods, LLC | Management Business Review</div>
    <div class="confidential">CONFIDENTIAL — FOR MANAGEMENT USE ONLY</div>
    <div>Page 4 of 8</div>
  </div>
</div>
"""

# ============================================================
# PAGE 5: FINANCIAL REPORT — Inventory, P&L Detail & Adjusted EBITDA
# ============================================================
html += f"""
<!-- PAGE 5: INVENTORY, P&L & ADJUSTED EBITDA -->
<div class="page">
  <div>
    <div class="cfa-header">
      <div>
        <div class="brand-title">Dan-D Foods, LLC (DOAU)</div>
        <div class="brand-sub">Financial Report | Inventory Analysis, P&L & Adjusted EBITDA Schedule</div>
      </div>
      <div class="doc-meta">
        <div>Reporting Period: <strong>{escape_html(report_period)}</strong></div>
        <div>Agenda Item: <strong>Financial Report (3/5)</strong></div>
      </div>
    </div>

    <div class="content-body">
      <div class="two-col inventory-two-col">
        <!-- Left: Inventory Breakdown -->
        <div>
          <div class="section-title">
            <span>Inventory Valuation Analysis</span>
            <span style="font-size:7pt; color:#64748b;">As of {escape_html(report_period)}</span>
          </div>

          <table class="cfa-table">
            <thead>
              <tr><th>Inventory Category</th><th class="num">Asset Value ($)</th><th class="num">% Total</th></tr>
            </thead>
            <tbody>
              <tr>
                <td>Raw Nuts (RMNUT)</td>
                <td class="num">{fmt(inv['raw_nuts'])}</td>
                <td class="num">{pct(safe_divide(inv['raw_nuts'], inv['total_inventory_asset_value']))}</td>
              </tr>
              <tr>
                <td>Raw Ingredients (RMINGREDIENT)</td>
                <td class="num">{fmt(inv['raw_ingredients'])}</td>
                <td class="num">{pct(safe_divide(inv['raw_ingredients'], inv['total_inventory_asset_value']))}</td>
              </tr>
              <tr>
                <td>Raw Dried Fruits (RMFRUIT)</td>
                <td class="num">{fmt(inv['raw_fruits'])}</td>
                <td class="num">{pct(safe_divide(inv['raw_fruits'], inv['total_inventory_asset_value']))}</td>
              </tr>
              <tr>
                <td>Packaging Material (Film/Box/Bag)</td>
                <td class="num">{fmt(inv['packaging'])}</td>
                <td class="num">{pct(safe_divide(inv['packaging'], inv['total_inventory_asset_value']))}</td>
              </tr>
              <tr class="sub-total">
                <td><strong>Total Raw & Packaging</strong></td>
                <td class="num font-bold">{fmt(inv['total_inventory_raw'])}</td>
                <td class="num font-bold">{pct(safe_divide(inv['total_inventory_raw'], inv['total_inventory_asset_value']))}</td>
              </tr>
              <tr>
                <td>Finished Bulk Nuts (FGBNUT)</td>
                <td class="num">{fmt(inv['finished_goods_bulk'])}</td>
                <td class="num">{pct(safe_divide(inv['finished_goods_bulk'], inv['total_inventory_asset_value']))}</td>
              </tr>
              <tr>
                <td>Finished Pack Nuts (FGPNUT)</td>
                <td class="num">{fmt(inv['finished_goods_pack'])}</td>
                <td class="num">{pct(safe_divide(inv['finished_goods_pack'], inv['total_inventory_asset_value']))}</td>
              </tr>
              <tr class="sub-total">
                <td><strong>Total Finished Assembly</strong></td>
                <td class="num font-bold">{fmt(inv['total_assembly'])}</td>
                <td class="num font-bold">{pct(safe_divide(inv['total_assembly'], inv['total_inventory_asset_value']))}</td>
              </tr>
              <tr class="total-row">
                <td><strong>INV Sheet Total Value</strong></td>
                <td class="num font-bold">{fmt(inv['total_inventory_asset_value'])}</td>
                <td class="num font-bold">100.0%</td>
              </tr>
              <tr>
                <td>BS Total Inventory Asset (Adj)</td>
                <td class="num font-bold pos">{fmt(inv['bs_total_inventory'])}</td>
                <td class="num font-bold">-</td>
              </tr>
            </tbody>
          </table>

          <div class="chart-box" style="margin-top:6px;">
            <div class="chart-title">Inventory Share by SKU — Top 5 + Other</div>
            {inventory_pie_svg}
            <div class="chart-note">Source: INV sheet; composition uses positive-value SKUs only. {inventory_reconciliation_note}</div>
          </div>
        </div>

        <!-- Right: Monthly P&L and Adjusted EBITDA Bridge -->
        <div>
          <div class="section-title">
            <span>{escape_html(report_period)} P&amp;L Statement ('After' column)</span>
            <span style="font-size:7pt; color:#64748b;">Source: Sheet PL</span>
          </div>

          <table class="cfa-table">
            <thead>
              <tr><th>P&L Component</th><th class="num">{escape_html(report_period)} ($)</th><th class="num">% Rev</th></tr>
            </thead>
            <tbody>
              <tr><td>Product Sales & Store Sales</td><td class="num">{fmt(pl['sales_oct'])}</td><td class="num">{pct(safe_divide(pl['sales_oct'], pl['revenue_oct']))}</td></tr>
              <tr><td>Custom Processing Fees</td><td class="num">{fmt(pl['custom_proc_oct'])}</td><td class="num">{pct(safe_divide(pl['custom_proc_oct'], pl['revenue_oct']))}</td></tr>
              <tr class="sub-total"><td><strong>TOTAL NET REVENUE</strong></td><td class="num font-bold">{fmt(pl['revenue_oct'])}</td><td class="num font-bold">100.0%</td></tr>
              <tr><td>Material & Production COGS</td><td class="num">{fmt(pl['cogs_oct'] - pl['direct_labor_oct'] - pl['factory_oh_oct'])}</td><td class="num">{pct(safe_divide(pl['cogs_oct'] - pl['direct_labor_oct'] - pl['factory_oh_oct'], pl['revenue_oct']))}</td></tr>
              <tr><td>Direct Labor</td><td class="num">{fmt(pl['direct_labor_oct'])}</td><td class="num">{pct(safe_divide(pl['direct_labor_oct'], pl['revenue_oct']))}</td></tr>
              <tr><td>Factory Overhead</td><td class="num">{fmt(pl['factory_oh_oct'])}</td><td class="num">{pct(safe_divide(pl['factory_oh_oct'], pl['revenue_oct']))}</td></tr>
              <tr class="sub-total"><td><strong>TOTAL COGS</strong></td><td class="num font-bold">{fmt(pl['cogs_oct'])}</td><td class="num font-bold">{pct(safe_divide(pl['cogs_oct'], pl['revenue_oct']))}</td></tr>
              <tr class="total-row"><td><strong>GROSS PROFIT / (LOSS)</strong></td><td class="num font-bold {chg_cls(pl['gross_profit_oct'])}">{fmt(pl['gross_profit_oct'])}</td><td class="num font-bold {chg_cls(pl['gross_profit_oct'])}">{pct(safe_divide(pl['gross_profit_oct'], pl['revenue_oct']))}</td></tr>
              <tr><td>Admin Expenses</td><td class="num">{fmt(pl['admin_exp_oct'])}</td><td class="num">{pct(safe_divide(pl['admin_exp_oct'], pl['revenue_oct']))}</td></tr>
              <tr><td>Sales Expenses</td><td class="num">{fmt(pl['sales_exp_oct'])}</td><td class="num">{pct(safe_divide(pl['sales_exp_oct'], pl['revenue_oct']))}</td></tr>
              <tr class="total-row"><td><strong>OPERATING INCOME / (LOSS)</strong></td><td class="num font-bold {chg_cls(pl['net_ordinary_income_oct'])}">{fmt(pl['net_ordinary_income_oct'])}</td><td class="num font-bold {chg_cls(pl['net_ordinary_income_oct'])}">{pct(safe_divide(pl['net_ordinary_income_oct'], pl['revenue_oct']))}</td></tr>
              <tr><td>Interest Expense</td><td class="num">{fmt(pl['interest_oct'])}</td><td class="num">{pct(safe_divide(pl['interest_oct'], pl['revenue_oct']))}</td></tr>
              <tr class="total-row" style="background:#0b2545; color:white;"><td style="color:white;"><strong>NET INCOME / (LOSS)</strong></td><td class="num font-bold" style="color:white;">{fmt(pl['net_income_oct'])}</td><td class="num font-bold" style="color:#fca5a5;">{pct(safe_divide(pl['net_income_oct'], pl['revenue_oct']))}</td></tr>
            </tbody>
          </table>

          <div class="section-title" style="margin-top:6px;">
            <span>EBITDA Bridge & Management Adjustments</span>
            <span style="font-size:7pt; color:#8b0000;">Source: Sheet CF</span>
          </div>

          <table class="cfa-table">
            <thead>
              <tr><th>Schedule Line Item</th><th class="num">{escape_html(report_period)}</th><th class="num">YTD {escape_html(report_year)}</th></tr>
            </thead>
            <tbody>
              <tr class="sub-total"><td><strong>Operational EBITDA (007-DOAU Data)</strong></td><td class="num font-bold neg">{fmt(ebitda_sch['operational_ebitda']['oct'])}</td><td class="num font-bold neg">{fmt(ebitda_sch['operational_ebitda']['ytd'])}</td></tr>
              <tr><td>CF Sheet Baseline EBITDA</td><td class="num">{fmt(ebitda_sch['oct']['ebitda'])}</td><td class="num">{fmt(ebitda_sch['ytd']['ebitda'])}</td></tr>
              <tr><td>Addback: FY2025 Don's Consulting Fee</td><td class="num">-</td><td class="num pos">{fmt(ebitda_sch['ytd']['consulting_fee'])}</td></tr>
              <tr><td>Addback: Bonus to Vinh Le</td><td class="num">-</td><td class="num pos">{fmt(ebitda_sch['ytd']['bonus_vinh'])}</td></tr>
              <tr><td>Addback: Employee Loyalty to Victor</td><td class="num pos">{fmt(ebitda_sch['oct']['loyalty_victor'])}</td><td class="num pos">{fmt(ebitda_sch['ytd']['loyalty_victor'])}</td></tr>
              <tr><td>Addback: Rent to 1565 Cliveden Ave (Pre-ops)</td><td class="num pos">{fmt(ebitda_sch['oct']['rent_cliveden'])}</td><td class="num pos">{fmt(ebitda_sch['ytd']['rent_cliveden'])}</td></tr>
              <tr class="sub-total"><td><strong>Total Extraordinary Addbacks</strong></td><td class="num font-bold pos">{fmt(ebitda_sch['oct']['total_addbacks'])}</td><td class="num font-bold pos">{fmt(ebitda_sch['ytd']['total_addbacks'])}</td></tr>
              <tr class="total-row" style="background:#0b2545; color:white;"><td style="color:white;"><strong>MANAGEMENT ADJUSTED EBITDA</strong></td><td class="num font-bold" style="color:#86efac;">{fmt(ebitda_sch['oct']['adjusted_ebitda'])}</td><td class="num font-bold" style="color:#86efac;">{fmt(ebitda_sch['ytd']['adjusted_ebitda'])}</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <div class="cfa-footer">
    <div>Dan-D Foods, LLC | Management Business Review</div>
    <div class="confidential">CONFIDENTIAL — FOR MANAGEMENT USE ONLY</div>
    <div>Page 5 of 8</div>
  </div>
</div>
"""

# ============================================================
# PAGE 6: FINANCIAL REPORT — Balance Sheet & Working Capital (AR/AP)
# ============================================================
html += f"""
<!-- PAGE 6: BALANCE SHEET & WORKING CAPITAL -->
<div class="page">
  <div>
    <div class="cfa-header">
      <div>
        <div class="brand-title">Dan-D Foods, LLC (DOAU)</div>
        <div class="brand-sub">Financial Report | Balance Sheet & Working Capital (AR / AP Aging)</div>
      </div>
      <div class="doc-meta">
        <div>Reporting Period: <strong>As of {escape_html(report_period)}</strong></div>
        <div>Agenda Item: <strong>Financial Report (4/5)</strong></div>
      </div>
    </div>

    <div class="content-body">
      <div class="two-col">
        <!-- Left: Full Balance Sheet Statement -->
        <div>
          <div class="section-title">
            <span>Balance Sheet (Statement of Financial Position)</span>
            <span style="font-size:7pt; color:#64748b;">As of {escape_html(report_period)}</span>
          </div>

          <table class="cfa-table">
            <thead>
              <tr><th>Balance Sheet Line Item</th><th class="num">Amount ($)</th></tr>
            </thead>
            <tbody>
              <tr class="sub-total"><td colspan="2"><strong>CURRENT ASSETS</strong></td></tr>
              <tr><td>Cash & Equivalents</td><td class="num">{fmt(bs['cash_and_equiv'])}</td></tr>
              <tr><td>Accounts Receivable - Gross</td><td class="num">{fmt(bs['ar_gross'])}</td></tr>
              <tr><td>Allowance for Doubtful Accounts</td><td class="num neg">{fmt(bs['ar_allowance'])}</td></tr>
              <tr><td>Accounts Receivable - Net</td><td class="num font-bold">{fmt(bs['ar_net'])}</td></tr>
              <tr><td>Inventory Asset (Total)</td><td class="num">{fmt(bs['inventory'])}</td></tr>
              <tr><td>Prepaid Expenses & Undeposited</td><td class="num">{fmt(bs['prepaid'] + bs['undeposited_funds'])}</td></tr>
              <tr class="total-row"><td><strong>TOTAL CURRENT ASSETS</strong></td><td class="num font-bold">{fmt(bs['total_current_assets'])}</td></tr>
              <tr class="sub-total"><td colspan="2"><strong>NON-CURRENT ASSETS</strong></td></tr>
              <tr><td>Production & Automation Equipment</td><td class="num">{fmt(bs['fixed_assets_prod_equip'] + bs['fixed_assets_automation'])}</td></tr>
              <tr><td>Construction in Progress (CIP)</td><td class="num">{fmt(bs['fixed_assets_cip'])}</td></tr>
              <tr><td>Building Improvements & Auto</td><td class="num">{fmt(bs['fixed_assets_building_imp'] + bs['fixed_assets_auto'])}</td></tr>
              <tr><td>Accumulated Depreciation</td><td class="num neg">{fmt(bs['accum_depreciation'])}</td></tr>
              <tr class="total-row"><td><strong>TOTAL FIXED ASSETS</strong></td><td class="num font-bold">{fmt(bs['total_fixed_assets'])}</td></tr>
              <tr class="total-row" style="background:#0b2545; color:white;"><td style="color:white;"><strong>TOTAL ASSETS</strong></td><td class="num font-bold" style="color:white;">{fmt(bs['total_assets'])}</td></tr>
              
              <tr class="sub-total"><td colspan="2"><strong>CURRENT LIABILITIES</strong></td></tr>
              <tr><td>Accounts Payable</td><td class="num">{fmt(bs['accounts_payable'])}</td></tr>
              <tr><td>Accrued Expenses & Credit Cards</td><td class="num">{fmt(bs['accrued_expenses'] + bs['credit_cards'])}</td></tr>
              <tr><td>Loan Payable - Dan D Pistachio</td><td class="num">{fmt(bs['loan_dan_d_pistachio'])}</td></tr>
              <tr><td>Payroll Liabilities</td><td class="num">{fmt(bs['payroll_liabilities'])}</td></tr>
              <tr class="total-row"><td><strong>TOTAL CURRENT LIABILITIES</strong></td><td class="num font-bold">{fmt(bs['total_current_liabilities'])}</td></tr>

              <tr class="sub-total"><td colspan="2"><strong>LONG-TERM LIABILITIES</strong></td></tr>
              <tr><td>East West Bank Loans (Term Loans)</td><td class="num">{fmt(bs['lt_loans']['east_west_1'] + bs['lt_loans']['east_west_2'])}</td></tr>
              <tr><td>Loan Payable - Danway</td><td class="num">{fmt(bs['lt_loans']['danway'])}</td></tr>
              <tr><td>Loan Payable - Dan-D-Foods Ltd</td><td class="num">{fmt(bs['lt_loans']['dan_d_foods_ltd'])}</td></tr>
              <tr><td>Loan Payable - Horseshoe & DDP</td><td class="num">{fmt(bs['lt_loans']['horseshoe'] + bs['lt_loans']['ddp_llc'])}</td></tr>
              <tr class="total-row"><td><strong>TOTAL LONG-TERM LIABILITIES</strong></td><td class="num font-bold">{fmt(bs['total_lt_liabilities'])}</td></tr>
              <tr class="sub-total"><td><strong>TOTAL LIABILITIES</strong></td><td class="num font-bold">{fmt(bs['total_liabilities'])}</td></tr>

              <tr class="sub-total"><td colspan="2"><strong>MEMBERS' EQUITY</strong></td></tr>
              <tr><td>Capital Stock & Members Equity</td><td class="num">{fmt(bs['capital_stock'] + bs['members_equity'])}</td></tr>
              <tr><td>Retained Earnings</td><td class="num">{fmt(bs['retained_earnings'])}</td></tr>
              <tr><td>Net Income (YTD Loss)</td><td class="num neg">{fmt(bs['net_income_bs'])}</td></tr>
              <tr class="total-row"><td><strong>TOTAL EQUITY</strong></td><td class="num font-bold">{fmt(bs['total_equity'])}</td></tr>
              <tr class="total-row" style="background:#0b2545; color:white;"><td style="color:white;"><strong>TOTAL LIABILITIES & EQUITY</strong></td><td class="num font-bold" style="color:white;">{fmt(bs['total_liabilities_and_equity'])}</td></tr>
            </tbody>
          </table>
        </div>

        <!-- Right: AR & AP Aging Breakdown -->
        <div>
          <div class="section-title">
            <span>Accounts Receivable Aging Analysis</span>
            <span style="font-size:7pt; color:#64748b;">Total: {fmt(ar['totals']['total'])}</span>
          </div>

          <table class="cfa-table">
            <thead>
              <tr>
                <th>Bucket</th>
                <th class="num">Amount ($)</th>
                <th class="num">% Total</th>
                <th>Status / Key Exposure</th>
              </tr>
            </thead>
            <tbody>
              <tr><td>Current</td><td class="num">{fmt(ar['totals']['current'])}</td><td class="num">{pct(safe_divide(ar['totals']['current'], ar['totals']['total']))}</td><td>Per AR aging sheet</td></tr>
              <tr><td>1 – 30 Days</td><td class="num">{fmt(ar['totals']['d1_30'])}</td><td class="num">{pct(safe_divide(ar['totals']['d1_30'], ar['totals']['total']))}</td><td>Per AR aging sheet</td></tr>
              <tr><td>31 – 60 Days</td><td class="num">{fmt(ar['totals']['d31_60'])}</td><td class="num">{pct(safe_divide(ar['totals']['d31_60'], ar['totals']['total']))}</td><td>Per AR aging sheet</td></tr>
              <tr><td>61 – 90 Days</td><td class="num">{fmt(ar['totals']['d61_90'])}</td><td class="num">{pct(safe_divide(ar['totals']['d61_90'], ar['totals']['total']))}</td><td>Per AR aging sheet</td></tr>
              <tr class="sub-total"><td>&gt; 90 Days</td><td class="num font-bold {chg_cls(ar['totals']['over90'])}">{fmt(ar['totals']['over90'])}</td><td class="num">{pct(safe_divide(ar['totals']['over90'], ar['totals']['total']))}</td><td>Review aged balances with owners</td></tr>
              <tr class="total-row"><td><strong>Total AR Outstanding</strong></td><td class="num font-bold">{fmt(ar['totals']['total'])}</td><td class="num font-bold">100.0%</td><td>Ties to Balance Sheet net AR</td></tr>
              <tr><td>Intercompany AR</td><td class="num font-bold">{fmt(ar['totals']['intercompany'])}</td><td class="num">-</td><td>Per workbook classification</td></tr>
              <tr><td>Third-Party AR</td><td class="num font-bold">{fmt(ar['totals']['third_party'])}</td><td class="num">-</td><td>Per workbook classification</td></tr>
            </tbody>
          </table>

          <div class="section-title" style="margin-top:8px;">
            <span>Accounts Payable Aging Analysis</span>
            <span style="font-size:7pt; color:#64748b;">Total: {fmt(ap['totals']['total'])}</span>
          </div>

          <table class="cfa-table">
            <thead>
              <tr>
                <th>AP Category / Bucket</th>
                <th class="num">Amount ($)</th>
                <th class="num">% Total</th>
                <th>Commentary</th>
              </tr>
            </thead>
            <tbody>
              <tr><td>Current</td><td class="num">{fmt(ap['totals']['current'])}</td><td class="num">{pct(safe_divide(ap['totals']['current'], ap['totals']['total']))}</td><td>Per AP aging sheet</td></tr>
              <tr><td>1 – 30 Days</td><td class="num">{fmt(ap['totals']['d1_30'])}</td><td class="num">{pct(safe_divide(ap['totals']['d1_30'], ap['totals']['total']))}</td><td>Per AP aging sheet</td></tr>
              <tr><td>31 – 60 Days</td><td class="num">{fmt(ap['totals']['d31_60'])}</td><td class="num">{pct(safe_divide(ap['totals']['d31_60'], ap['totals']['total']))}</td><td>Per AP aging sheet</td></tr>
              <tr><td>61 – 90 Days</td><td class="num">{fmt(ap['totals']['d61_90'])}</td><td class="num">{pct(safe_divide(ap['totals']['d61_90'], ap['totals']['total']))}</td><td>Per AP aging sheet</td></tr>
              <tr><td>&gt; 90 Days (per aging sheet)</td><td class="num font-bold {chg_cls(ap['totals']['over90'])}">{fmt(ap['totals']['over90'])}</td><td class="num">{pct(safe_divide(ap['totals']['over90'], ap['totals']['total']))}</td><td>Includes bucket balances; review debit balances separately</td></tr>
              <tr class="total-row"><td><strong>Total Accounts Payable</strong></td><td class="num font-bold">{fmt(ap['totals']['total'])}</td><td class="num font-bold">100.0%</td><td>Ties to Balance Sheet AP</td></tr>
              <tr><td>Advance to Suppliers</td><td class="num font-bold {chg_cls(ap['totals']['advance_to_supplier'])}">{fmt(ap['totals']['advance_to_supplier'])}</td><td class="num">-</td><td>Shown separately from trade aging</td></tr>
              <tr><td>Intercompany AP</td><td class="num font-bold">{fmt(ap['totals']['intercompany'])}</td><td class="num">-</td><td>Per workbook classification</td></tr>
              <tr><td>Payable to 3rd Parties</td><td class="num font-bold">{fmt(ap['totals']['payable_to_3rd'])}</td><td class="num">-</td><td>Per workbook classification</td></tr>
            </tbody>
          </table>

          <div class="sidebar" style="margin-top:4px;">
            <div class="section-tag">Working Capital Rebalance</div>
            <div style="font-size:7pt; color:#334155; line-height:1.35;">
              Balance-sheet working capital is <strong>{fmt(metrics['net_working_capital'])}</strong> (current assets less current liabilities). This measure is not adjusted for intercompany balances; review those separately.
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="cfa-footer">
    <div>Dan-D Foods, LLC | Management Business Review</div>
    <div class="confidential">CONFIDENTIAL — FOR MANAGEMENT USE ONLY</div>
    <div>Page 6 of 8</div>
  </div>
</div>
"""

# ============================================================
# PAGE 7: FINANCIAL REPORT — Capex & Cash Flows
# ============================================================
html += f"""
<!-- PAGE 7: CAPEX & CASH FLOWS -->
<div class="page">
  <div>
    <div class="cfa-header">
      <div>
        <div class="brand-title">Dan-D Foods, LLC (DOAU)</div>
        <div class="brand-sub">Financial Report | Capital Expenditures (Capex) & Statement of Cash Flows</div>
      </div>
      <div class="doc-meta">
        <div>Reporting Period: <strong>{escape_html(report_period)}</strong></div>
        <div>Agenda Item: <strong>Financial Report (5/5)</strong></div>
      </div>
    </div>

    <div class="content-body">
      <div class="two-col cash-flow-two-col">
        <!-- Left: Capex & Fixed Assets -->
        <div>
          <div class="section-title">
            <span>Capital Expenditures & Fixed Assets</span>
            <span style="font-size:7pt; color:#64748b;">Schedule of Property, Plant & Equipment</span>
          </div>

          <table class="cfa-table">
            <thead>
              <tr><th>Fixed Asset Line Item</th><th class="num">Book Value ($)</th><th class="num">% Gross</th></tr>
            </thead>
            <tbody>
              <tr><td>Production Equipment</td><td class="num">{fmt(bs['fixed_assets_prod_equip'])}</td><td class="num">{pct(safe_divide(bs['fixed_assets_prod_equip'], bs['total_fixed_assets'] - bs['accum_depreciation']))}</td></tr>
              <tr><td>Construction in Progress (CIP)</td><td class="num">{fmt(bs['fixed_assets_cip'])}</td><td class="num">{pct(safe_divide(bs['fixed_assets_cip'], bs['total_fixed_assets'] - bs['accum_depreciation']))}</td></tr>
              <tr><td>Building Improvements</td><td class="num">{fmt(bs['fixed_assets_building_imp'])}</td><td class="num">{pct(safe_divide(bs['fixed_assets_building_imp'], bs['total_fixed_assets'] - bs['accum_depreciation']))}</td></tr>
              <tr><td>Automation Systems</td><td class="num">{fmt(bs['fixed_assets_automation'])}</td><td class="num">{pct(safe_divide(bs['fixed_assets_automation'], bs['total_fixed_assets'] - bs['accum_depreciation']))}</td></tr>
              <tr><td>Automotive Vehicles</td><td class="num">{fmt(bs['fixed_assets_auto'])}</td><td class="num">{pct(safe_divide(bs['fixed_assets_auto'], bs['total_fixed_assets'] - bs['accum_depreciation']))}</td></tr>
              <tr><td>Furniture & Equipment</td><td class="num">{fmt(bs['fixed_assets_furniture_equipment'])}</td><td class="num">{pct(safe_divide(bs['fixed_assets_furniture_equipment'], bs['total_fixed_assets'] - bs['accum_depreciation']))}</td></tr>
              <tr><td>Office & Computer Equipment</td><td class="num">{fmt(bs['fixed_assets_office_computer'])}</td><td class="num">{pct(safe_divide(bs['fixed_assets_office_computer'], bs['total_fixed_assets'] - bs['accum_depreciation']))}</td></tr>
              <tr class="sub-total">
                <td><strong>Total Gross Fixed Assets</strong></td>
                <td class="num font-bold">{fmt(bs['total_fixed_assets'] - bs['accum_depreciation'])}</td>
                <td class="num font-bold">100.0%</td>
              </tr>
              <tr>
                <td>Accumulated Depreciation</td>
                <td class="num neg">{fmt(bs['accum_depreciation'])}</td>
                <td class="num">{pct(safe_divide(bs['accum_depreciation'], bs['total_fixed_assets'] - bs['accum_depreciation']))}</td>
              </tr>
              <tr class="total-row">
                <td><strong>NET PROPERTY, PLANT & EQUIP</strong></td>
                <td class="num font-bold">{fmt(bs['total_fixed_assets'])}</td>
                <td class="num font-bold">{pct(safe_divide(bs['total_fixed_assets'], bs['total_fixed_assets'] - bs['accum_depreciation']))}</td>
              </tr>
            </tbody>
          </table>

          <div class="sidebar" style="margin-top:6px;">
            <div class="section-tag">Asset Interpretation</div>
            <div style="font-size:7pt; color:#334155; line-height:1.35;">
              Balance-sheet asset values are not a monthly CapEx trend or a project-status report. The CF statement's property and equipment purchase row reports {fmt(cf['net_cfi_capex'])}; review that cash-flow line separately from book balances.
            </div>
          </div>
        </div>

        <!-- Right: Statement of Cash Flows -->
        <div>
          <div class="section-title">
            <span>Statement of Cash Flows (Indirect Method)</span>
            <span style="font-size:7pt; color:#64748b;">{cf['months'][0]} to {cf['months'][-1]}</span>
          </div>

          <table class="cfa-table">
            <thead>
              <tr><th>Cash Flow Component ($)</th><th class="num">YTD through {escape_html(report_period)} ($)</th></tr>
            </thead>
            <tbody>
              <tr class="sub-total"><td colspan="2"><strong>A. CASH FLOWS FROM OPERATING ACTIVITIES (CFO)</strong></td></tr>
              <tr><td>Net Operating Income / (Loss)</td><td class="num {chg_cls(cf['net_operating_loss'])}">{fmt(cf['net_operating_loss'])}</td></tr>
              <tr><td>Add: Depreciation & Amortisation</td><td class="num {chg_cls(cf['depreciation_addback'])}">{fmt(cf['depreciation_addback'])}</td></tr>
              <tr><td>Add: Interest Expense (Reclassified to CFF)</td><td class="num {chg_cls(cf['interest_reclassified'])}">{fmt(cf['interest_reclassified'])}</td></tr>
              <tr><td>(Increase)/Decrease in Accounts Receivable</td><td class="num {chg_cls(cf['wc_delta_ar'])}">{fmt(cf['wc_delta_ar'])}</td></tr>
              <tr><td>(Increase)/Decrease in Inventory Asset</td><td class="num {chg_cls(cf['wc_delta_inventory'])}">{fmt(cf['wc_delta_inventory'])}</td></tr>
              <tr><td>Increase/(Decrease) in Accounts Payable</td><td class="num {chg_cls(cf['wc_delta_ap'])}">{fmt(cf['wc_delta_ap'])}</td></tr>
              <tr><td>Other Working Capital Movements (Prepaids, Advances, Accruals)</td><td class="num {chg_cls(cf['wc_delta_prepaid'] + cf['wc_delta_other'])}">{fmt(cf['wc_delta_prepaid'] + cf['wc_delta_other'])}</td></tr>
              <tr class="total-row"><td><strong>Net Cash from Operating Activities (CFO)</strong></td><td class="num font-bold {chg_cls(cf['net_cfo'])}">{fmt(cf['net_cfo'])}</td></tr>

              <tr class="sub-total"><td colspan="2"><strong>B. CASH FLOWS FROM INVESTING ACTIVITIES (CFI)</strong></td></tr>
              <tr><td>Purchase of Property, Plant & Equipment (Capex)</td><td class="num {chg_cls(cf['net_cfi_capex'])}">{fmt(cf['net_cfi_capex'])}</td></tr>
              <tr><td>Increase/(Decrease) in Security Deposits</td><td class="num {chg_cls(cf['wc_delta_security_deposits'])}">{fmt(cf['wc_delta_security_deposits'])}</td></tr>
              <tr class="total-row"><td><strong>Net Cash from Investing Activities (CFI)</strong></td><td class="num font-bold {chg_cls(cf['net_cfi'])}">{fmt(cf['net_cfi'])}</td></tr>

              <tr class="sub-total"><td colspan="2"><strong>C. CASH FLOWS FROM FINANCING ACTIVITIES (CFF)</strong></td></tr>
              <tr><td>Net Proceeds of Long-Term & Related Party Borrowings</td><td class="num {chg_cls(cf['borrowings_net'])}">{fmt(cf['borrowings_net'])}</td></tr>
              <tr><td>Interest Paid (Reclassified Operating Financing)</td><td class="num {chg_cls(cf['interest_paid'])}">{fmt(cf['interest_paid'])}</td></tr>
              <tr><td>Capital & Members Equity Contributions</td><td class="num {chg_cls(cf['equity_proceeds'])}">{fmt(cf['equity_proceeds'])}</td></tr>
              <tr class="total-row"><td><strong>Net Cash from Financing Activities (CFF)</strong></td><td class="num font-bold {chg_cls(cf['net_cff'])}">{fmt(cf['net_cff'])}</td></tr>

              <tr class="total-row" style="background:#0b2545; color:white;">
                <td style="color:white;"><strong>NET INCREASE / (DECREASE) IN CASH & CASH EQUIVALENTS</strong></td>
                <td class="num font-bold" style="color:#86efac;">{fmt(cf['net_change_cash'])}</td>
              </tr>
              <tr><td>Cash & Cash Equivalents — Opening Balance ({cf['months'][0]})</td><td class="num">{fmt(cf['opening_cash'])}</td></tr>
              <tr class="total-row"><td><strong>Cash & Cash Equivalents — Closing Balance ({cf['months'][-1]})</strong></td><td class="num font-bold">{fmt(cf['closing_cash'])}</td></tr>
            </tbody>
          </table>

          <p class="narrative-p" style="margin-top:6px;">
            <strong>Cash Flow Summary:</strong> CFO was {fmt(cf['net_cfo'])}, CFI was {fmt(cf['net_cfi'])} and CFF was {fmt(cf['net_cff'])}, resulting in a net cash change of {fmt(cf['net_change_cash'])}. Opening cash of {fmt(cf['opening_cash'])} reconciles to closing cash of {fmt(cf['closing_cash'])}. Source: parsed CF statement; subtotals are validated during extraction.
          </p>
        </div>
      </div>
      <div class="chart-box">
        <div class="chart-title">YTD Cash Flow Components — USD</div>
        {metrics['cash_flow_svg']}
        <div class="chart-note">Source: indirect cash-flow statement, {escape_html(cf['months'][0])} to {escape_html(cf['months'][-1])}. Bars are signed; totals reconcile to net cash change.</div>
      </div>
    </div>
  </div>

  <div class="cfa-footer">
    <div>Dan-D Foods, LLC | Management Business Review</div>
    <div class="confidential">CONFIDENTIAL — FOR MANAGEMENT USE ONLY</div>
    <div>Page 7 of 8</div>
  </div>
</div>
"""

# ============================================================
# PAGE 8: HR REPORT (Headcount Structure & HR Project Updates)
# ============================================================
html += f"""
<!-- PAGE 8: HR REPORT -->
<div class="page">
  <div>
    <div class="cfa-header">
      <div>
        <div class="brand-title">Dan-D Foods, LLC (DOAU)</div>
        <div class="brand-sub">Payroll Cost Report | YTD and Monthly P&amp;L Analysis</div>
      </div>
      <div class="doc-meta">
        <div>Reporting Period: <strong>{escape_html(report_period)}</strong></div>
        <div>Agenda Item: <strong>HR Report</strong></div>
      </div>
    </div>

    <div class="content-body">
      <div class="two-col">
        <!-- Left: Labor Cost Audit -->
        <div>
          <div class="section-title">
            <span>Payroll Cost Analysis</span>
            <span style="font-size:7pt; color:#64748b;">P&amp;L payroll allocations (YTD &amp; {escape_html(report_period)})</span>
          </div>

          <table class="cfa-table">
            <thead>
              <tr><th>Payroll Cost Category ($)</th><th class="num">{escape_html(report_period)} ($)</th><th class="num">YTD {escape_html(report_year)} ($)</th><th class="num">YTD {int(report_year) - 1} ($)</th></tr>
            </thead>
            <tbody>
              <tr><td>Direct Labor</td><td class="num">{fmt(hr['monthly_oct']['direct_labor'])}</td><td class="num">{fmt(hr['ytd']['direct_labor'])}</td><td class="num">{fmt(hr['ytd']['direct_labor_prior'])}</td></tr>
              <tr><td>Production Payroll</td><td class="num">{fmt(hr['monthly_oct']['production_payroll'])}</td><td class="num">{fmt(hr['ytd']['production_payroll'])}</td><td class="num">{fmt(hr['ytd']['production_payroll_prior'])}</td></tr>
              <tr><td>Administration Payroll</td><td class="num">{fmt(hr['monthly_oct']['admin_payroll'])}</td><td class="num">{fmt(hr['ytd']['admin_payroll'])}</td><td class="num">{fmt(hr['ytd']['admin_payroll_prior'])}</td></tr>
              <tr><td>Payroll Processing Fees</td><td class="num">{fmt(hr['monthly_oct']['payroll_processing_fees'])}</td><td class="num">{fmt(hr['ytd']['payroll_processing_fees'])}</td><td class="num">{fmt(hr['ytd']['payroll_processing_fees_prior'])}</td></tr>
              <tr class="total-row">
                <td><strong>Core Payroll (excludes processing fees)</strong></td>
                <td class="num font-bold">{fmt(hr['monthly_oct']['total_labor_oct'])}</td>
                <td class="num font-bold">{fmt(hr['ytd']['total_labor_ytd26'])}</td>
                <td class="num font-bold">{fmt(hr['ytd']['total_labor_ytd25'])}</td>
              </tr>
              <tr><td>YoY Core Payroll Change</td><td class="num">-</td><td class="num {chg_cls(hr['ytd']['total_labor_ytd26'] - hr['ytd']['total_labor_ytd25'])}">{fmt(hr['ytd']['total_labor_ytd26'] - hr['ytd']['total_labor_ytd25'])}</td><td class="num">{pct(metrics['ytd_labor_change_pct'])}</td></tr>
              <tr><td>Core Payroll as % of Revenue</td><td class="num font-bold">{pct(safe_divide(hr['monthly_oct']['total_labor_oct'], pl['revenue_oct']))}</td><td class="num font-bold">{pct(metrics['labor_as_revenue_pct'])}</td><td class="num font-bold">{pct(metrics['prior_labor_as_revenue_pct'])}</td></tr>
            </tbody>
          </table>

          <div class="sidebar" style="margin-top:6px;">
            <div class="section-tag">Payroll Observation</div>
            <div style="font-size:7pt; color:#334155; line-height:1.35;">
              Core payroll changed by <strong>{fmt(metrics['ytd_labor_change'])} ({pct(metrics['ytd_labor_change_pct'])})</strong> year over year. Payroll as a share of revenue changed from {pct(metrics['prior_labor_as_revenue_pct'])} to {pct(metrics['labor_as_revenue_pct'])}; this ratio is not a productivity measure without hours and output data.
            </div>
          </div>
        </div>

        <!-- Right: Payroll mix and source limitations -->
        <div>
          <div class="section-title">
            <span>Payroll Composition</span>
            <span style="font-size:7pt; color:#64748b;">YTD through {escape_html(report_period)}</span>
          </div>
          <div class="chart-box">
            {metrics['payroll_mix_svg']}
            <div class="chart-note">Source: PL and PL YTD sheets. Payroll processing fees are included in this composition chart but excluded from the core-payroll totals at left.</div>
          </div>
          <div class="sidebar-crimson" style="margin-top:6px;">
            <div class="section-tag" style="color:#8b0000;">Data Availability</div>
            <div style="font-size:7pt; color:#7f1d1d; line-height:1.35;">
              The supplied workbooks contain payroll amounts but no headcount, turnover, tenure, labor hours, output or HR project-status data. Those measures are not estimated here. Payroll amounts are unaudited management-account allocations.
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="cfa-footer">
    <div>Dan-D Foods, LLC | Management Business Review</div>
    <div class="confidential">CONFIDENTIAL — FOR MANAGEMENT USE ONLY</div>
    <div>Page 8 of 8</div>
  </div>
</div>
</body>
</html>
"""

if os.path.isfile(LOGO_FILE):
    logo_html = '<img src="../assets/doau_logo.png" alt="Dan-D Pak company logo" style="max-width:68px; max-height:44px; object-fit:contain;">'
    html = html.replace(
        '<div class="brand-title">Dan-D Foods, LLC (DOAU)',
        f'<div class="brand-title">{logo_html}Dan-D Foods, LLC (DOAU)',
        1,
    )
else:
    print(f"Logo asset not found; add the official DOAU logo at: {LOGO_FILE}")

os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Successfully generated HTML report at: {OUTPUT_HTML}")
print(f"File size: {len(html):,} characters")

# PDF Generation via Chrome Headless
chrome_executable = os.environ.get(
    "CHROME_PATH",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
)
if not os.path.isfile(chrome_executable):
    raise FileNotFoundError(
        f"Chrome was not found at {chrome_executable!r}; set CHROME_PATH to its executable."
    )
chrome_cmd = [
    chrome_executable,
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={OUTPUT_PDF}",
    f"file:///{OUTPUT_HTML.replace(os.sep, '/')}"
]
print(f"Rendering PDF with Chrome Headless: {OUTPUT_PDF}")
subprocess.run(chrome_cmd, check=True)
print(f"PDF generated successfully: {OUTPUT_PDF}")
print(f"PDF Size: {os.path.getsize(OUTPUT_PDF):,} bytes")
