# DOAU / Dan On Foods Group – Management & Equity Research Report Suite

## 1. Executive Overview

This suite produces the official, institutional **10-Page CFA-Style Management & Equity Research Report** for **DOAU (Dan On Foods / Dan-D-Pak)**, as of October 2026 (10M-2026).
The design strictly follows institutional CFA Institute visual standards:
- **Two-Column Grid**: Left 31.5% (Quantitative figures, charts, KPI cards, tables) & Right 66% (Executive narratives, strategic analyses).
- **Brand Palette**: Deep Corporate Red (`#a30008`), Slate Grey (`#6e7073`), high-contrast dark text (`#1e293b`), and white backgrounds.
- **Large Typography**: Enhanced font sizing across all pages (+2.5pt to +3pt) with 10–13.5pt bold chart and data labels.
- **Automated Chromium Pipeline**: Playwright Chromium renders pixel-perfect high-resolution PNGs and vector print-ready A4 PDFs.

---

## 2. Report Architecture & 10-Page Agenda Mapping

| Page | Title & Section | Visual Components (Left Column) | Analytical Content (Right Column) |
| :---: | :--- | :--- | :--- |
| **01** | **Company Introduction & Corporate Profile** | Dan On Foods MP3 aerial campus banner, Fresno & MP3 factory photo, corporate highlights card (\$6.33M assets). | Corporate mission, history (est. 1989), 487 SKUs, 40 wholesale accounts, and expanded Three-Pillar Transformation Strategy. |
| **02** | **Report Agenda & Navigation Index** | Dan-D-Pak logo, executive navigation index for Sections I to IV with page numbers. | Methodological note on data integrity and CFA standards compliance. |
| **03** | **Executive Summary & Action Plans** | 4 Key KPI cards (\$1,250k valuation, Overweight rating, \$10.08M rev, \$276k cash), core indicator table, strategic action priorities. | Executive synthesis, top-line recovery, OPEX containment, and 3 management action plans. |
| **04** | **Sales Report: YTD Performance Update** | Monthly revenue trend bar chart (Jan - Oct 2026), monthly growth summary table. | 3 operational phases (Q1 Baseline, Summer Trough, Q3/Q4 Resurgence) with structured bullet points and commercial commentary. |
| **05** | **Financial Report: Sep vs Oct Comparative** | MoM comparative statement table with variance column, YTD revenue run-rate vs 2025 table. | Variance analysis on revenue (-4.6%), COGS, OPEX discipline, and YTD performance. |
| **06** | **Margin Analysis, P&L & Adjusted EBITDA** | EBITDA & Operating Income bridge chart (GP -> Admin -> Sales -> NOI -> EBITDA), margin structure table. | Gross margin compression (-6.5%), factory overhead allocations, EBITDA normalization, and pathway to break-even. |
| **07** | **Top Customer & Top Items (SKU) Analysis** | Enlarged Customer Revenue Distribution donut chart with extra-bold % and values, Top 5 SKU contribution table. | Concentration across 4 primary clients (Falcon, DOF, Wal-Mart, Dollarama) and 80/20 Pareto SKU dynamics. |
| **08** | **Inventory Analysis & Warehouse Optimization** | Top 6 Inventory asset value SKUs table, inventory category breakdown table (\$3.61M total). | Carrying cost dynamics, DSI (95 days), SKU de-proliferation, and $500k liquidation plan. |
| **09** | **Balance Sheet Analysis (AR & AP Agings)** | Trade AR aging distribution bar chart (Current, 1-30d, 31-60d, 61-90d, >90d), balance sheet capital structure table. | Working capital surplus (\$3.52M), AR collectability analysis (\$1,738k in prime buckets), and supplier AP terms. |
| **10** | **Capex, Fixed Assets & Cash Flows** | Fixed assets and depreciation schedule table (\$834k net), indirect cash flow statement summary table. | Infrastructure capex (optical sorting, cold storage), CFO/CFI/CFF dynamics, closing cash (\$276k), and disclosures. |

---

## 3. Directory Layout & Core Modules

```
DOAU/
├── data/
│   └── generated/
│       └── extracted_data.json            # Master extracted JSON from financial workbooks
├── inputs/
│   └── workbooks/
│       └── FS DOAU Oct 26.xlsx            # Primary source Excel financial statements
├── reports/
│   └── generated/
│       ├── DOAU_Comprehensive_Management_Report.pdf  # Final 10-page vector PDF
│       ├── DOAU_Comprehensive_Management_Report.html # Final master HTML
│       └── rendered_pages/                           # Per-page high-resolution PNGs (page_01 to page_10)
├── src/
│   └── report/
│       ├── assets/                        # Official brand logos, MP3 factory photos, banners
│       ├── archive/                       # Archived legacy & interim generator scripts
│       ├── extract_data.py                # Extracts data from Excel workbooks to JSON
│       ├── generate_cfa_agenda_report.py  # Production generator for the 10-page HTML report
│       ├── render_playwright.py           # Production Chromium runner (PNG screenshots & vector PDF)
│       └── cfa_chart_components.py        # Reusable SVG chart components with large typography
└── README.md
```

---

## 4. Execution Workflow

To regenerate the entire 10-page report and verify page-by-page outputs:

```powershell
# 1. (Optional) Re-extract data from Excel workbooks if updated
.venv\Scripts\python.exe src/report/extract_data.py

# 2. Generate the full 10-page HTML report
.venv\Scripts\python.exe src/report/generate_cfa_agenda_report.py

# 3. Render pixel-perfect PNGs and vector PDF via Playwright Chromium
.venv\Scripts\python.exe src/report/render_playwright.py
```

Outputs will be saved in:
- `reports/generated/DOAU_Comprehensive_Management_Report.pdf`
- `reports/generated/rendered_pages/page_01.png` ... `page_10.png`
