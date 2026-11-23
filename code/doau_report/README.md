# DOAU Management Report

The report pipeline reads the DOAU workbooks, validates key reconciliations, extracts a JSON data file, and renders one HTML report for both browser viewing and A4 PDF output. Commentary is generated locally from workbook metrics and fixed rules; workbook or customer data is not sent to an external AI service.

## Requirements

- Python 3.8 or newer
- `openpyxl`
- Google Chrome at `C:\Program Files\Google\Chrome\Application\chrome.exe` for PDF generation
- Optionally set `CHROME_PATH` if Chrome is installed elsewhere

## Run

From this directory in PowerShell:

```powershell
python extract_data.py
python -m unittest -v
python generate_report.py
```

**Yes—the HTML is generated from `data/extracted_data.json`.** `extract_data.py` reads the main workbook and the separate indirect cash-flow workbook, checks required totals, and writes that JSON. `generate_report.py` reads the JSON and writes both:

- `output/DOAU_Management_Report_Oct2026.html`
- `output/DOAU_Management_Report_Oct2026.pdf`

The HTML contains a snapshot of the JSON values at generation time; it does not read the JSON live in the browser. After changing a workbook, run `extract_data.py` first, then `generate_report.py`.

The generated HTML includes an **Export Management Report to PDF** button that opens the browser print dialog. The PDF generator uses Chrome headless and the same HTML as its source.

## Workbook inputs

Keep both workbooks in the project root:

- `FS DOAU Oct 26_adjust.xlsm`
- `FS_DOAU_Oct_26_CF_Indirect_Fixed_v2.xlsm`

The company logo is read from `assets/doau_logo.png` and appears on the first report page.

## Report contents and charts

1. Executive Summary — YTD and monthly results, balance-sheet ratios, monthly sales trend
2. Sales — YTD comparison, customer concentration and sales-share chart, management review questions
3. Financial Performance — month-over-month and YTD P&L comparisons
4. Commercial Analysis — customer table and product sales/gross-profit charts
5. Inventory & P&L — inventory category and SKU charts, reconciliation, P&L, and adjusted EBITDA schedule
6. Balance Sheet & Working Capital — balance sheet and AR/AP aging schedules
7. CapEx & Cash Flow — fixed-asset balances and signed CFO/CFI/CFF/net cash change chart
8. Payroll Cost Analysis — payroll comparison and YTD payroll-mix chart

The report uses SVG charts and selectable HTML/PDF text. Source periods, calculation notes, and known limitations are called out with the relevant report content.

### Chart presentation

All existing SVG charts use larger plot areas and data labels. Pie-chart percentages appear inside slices large enough to remain readable; smaller slices retain their values and percentages in the legend. Bar-chart values appear inside bars when there is enough room and move just outside short bars. Cash-flow signs and the zero baseline are preserved, and payroll-mix percentages appear inside segments wide enough to fit.

The inventory page gives its chart column additional width. Print styling avoids splitting chart cards where possible while keeping the report on A4 pages.

### Analyze the real report data locally

```powershell
python analyze_report_locally.py
```

This script reads the actual `data/extracted_data.json` and writes an eight-section Markdown analysis to `output/DOAU_Page_Analysis_<period>.md`. It uses local calculations and rule-based observations for revenue, margin, customers, products, inventory, working capital, cash flow, and payroll. It makes no network requests and does not need or read a Gemini API key. Keep the generated analysis file local because it contains real financial and customer/SKU information.

### Gemini prompt demo (synthetic data only)

`gemini_demo.py` previews one shared page-analysis prompt or optionally sends a fixed synthetic example to Gemini. It does not import `extracted_data.json`, read either workbook, or run as part of report generation.

```powershell
# Preview a prompt locally; no network request and no API key required
python gemini_demo.py --page executive-summary

# Optional: send only that page's fabricated test metrics and curated public company context
$env:GEMINI_API_KEY = "<your key from an approved secret store>"
python gemini_demo.py --page executive-summary --send
Remove-Item Env:GEMINI_API_KEY
```

Replace the placeholder in the current PowerShell process only; never put a real key in source code, this README, HTML/JSON output, or a committed `.env` file. `GEMINI_API_KEY` is sent in an HTTP header, not in the prompt or URL. The demo requires an explicit `--send`; absent that flag it only prints the prompt.

The eight page IDs are `executive-summary`, `sales`, `financial-performance`, `commercial-analysis`, `inventory`, `working-capital`, `capex-cash-flow`, and `payroll`. Each has a fixed, fabricated fixture. Gemini output is schema-validated and is not included in the live DOAU HTML/PDF. Do not pass real report metrics, customer/SKU names, workbook text, or extracted JSON to this public API.

Company context is a curated subset of `assets/Dan_On_Foods_Company_Industry_Profile.md`; the complete profile is not sent. It distinguishes Dan On Foods Corporation (DOF), the Vietnamese name and short form, DAN-D FOODS Group, product brands, and the DOAU report code. The profile is preliminary, so unverified organizational/process/financial claims are excluded or explicitly qualified.

## Validation and limitations

- Required cash-flow subtotals and cash reconciliation are checked for YTD and each month.
- Monthly revenue is checked against YTD P&L revenue; YTD gross profit is checked against revenue less COGS; Balance Sheet assets are checked against liabilities and equity.
- AR aging ties to Balance Sheet net AR, and AP aging ties to Balance Sheet accounts payable.
- The monthly gross-profit sum from `007-DOAU data` differs from the YTD P&L gross-profit value. Both are retained and the difference is disclosed for follow-up, rather than silently forcing them to match.
- Inventory SKU details reconcile to the `INV` sheet. The difference between the INV total and Balance Sheet inventory is disclosed and is not allocated to SKUs.
- Headcount, turnover, tenure, labor hours, output, and HR project status are not present in the supplied workbooks and are not estimated.
- Figures are unaudited management accounts; locally generated observations require management review.

## Source mapping

| Report data | Workbook sheet |
|---|---|
| Monthly financial trend | `007-DOAU data` |
| YTD P&L comparison | `PL YTD Aug 26` |
| Monthly P&L | `PL` |
| Adjusted EBITDA schedule | Main workbook `CF` |
| Balance Sheet | `BS` |
| AR/AP aging | `AR` / `AP` |
| Customers / product margins | `Sales by cust` / `GP` |
| Inventory | `INV` |
| Indirect cash-flow statement | CF workbook `CF` |
