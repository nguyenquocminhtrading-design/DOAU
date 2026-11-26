# DOAU Financial Reporting Repository

This repository contains source financial workbooks, Excel/VBA utilities, templates, and a Python pipeline that produces the DOAU management report.

## Repository map

| Folder | Contents |
|---|---|
| `inputs/workbooks/` | Source `.xlsx` and `.xlsm` financial workbooks |
| `src/report/` | Python extraction, report generation, local analysis, and tests |
| `src/report/assets/` | Logo and company-context reference material |
| `src/excel-vba/` | VBA modules and macros |
| `templates/` | Reference report and design templates |
| `data/generated/` | Extracted JSON used as the report pipeline's intermediate data |
| `reports/generated/` | Generated HTML, PDF, Markdown analyses, and page renders |

## Generate the management report

Run these commands from the repository root in PowerShell:

```powershell
python .\src\report\extract_data.py
python -m unittest discover -s .\src\report -p "test_*.py" -v
python .\src\report\generate_report.py
```

The report uses the adjusted main workbook and the dedicated indirect cash-flow workbook in `inputs/workbooks/`. Python paths are resolved relative to the repository, so cloning it to a different directory does not require editing a user's local absolute paths. PDF output requires Google Chrome; set `CHROME_PATH` if it is not installed at the default path.

For the detailed source-to-KPI guide, formulas, workbook sheet/cell mapping, validation checks, Gemini demo boundaries, and limitations, see [src/report/README.md](./src/report/README.md).

## Handling financial data

Generated JSON, reports, and analyses may include non-public financial, customer, and SKU information. Keep these files within approved storage and review them before sharing or pushing. The Gemini demo is for fabricated sample data only; never send live workbook or report data to the external API.
