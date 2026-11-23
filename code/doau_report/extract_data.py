import openpyxl
import json
import os
import re
from collections import defaultdict
from datetime import datetime

EXCEL_PATH = r"c:\Users\minhnq\Documents\A-Q_consol\DOAU\FS DOAU Oct 26_adjust.xlsm"
CF_EXCEL_PATH = r"c:\Users\minhnq\Documents\A-Q_consol\DOAU\FS_DOAU_Oct_26_CF_Indirect_Fixed_v2.xlsm"
DATA_OUTPUT_DIR = r"c:\Users\minhnq\Documents\A-Q_consol\DOAU\code\doau_report\data"
OUTPUT_FILE = os.path.join(DATA_OUTPUT_DIR, "extracted_data.json")


def normalize_label(value):
    return re.sub(r"\s+", " ", str(value).replace("\u2013", "-").replace("\u2014", "-")).strip().casefold()


def require_reconciles(label, calculated, reported, tolerance=0.05):
    difference = calculated - reported
    if abs(difference) > tolerance:
        raise ValueError(
            f"{label} does not reconcile: calculated {calculated:.2f}, "
            f"reported {reported:.2f}, difference {difference:.2f}"
        )
    return difference


def parse_cash_flow_statement(path, expected_months):
    wb_cf = openpyxl.load_workbook(path, data_only=True, read_only=True)
    if "CF" not in wb_cf.sheetnames:
        raise ValueError(f"Cash-flow sheet 'CF' not found in {path}")

    ws_cf = wb_cf["CF"]
    row_by_label = {}
    for row in range(1, ws_cf.max_row + 1):
        label = ws_cf.cell(row, 1).value
        if label:
            row_by_label[normalize_label(label)] = row

    fields = {
        "net_operating_loss": "Net Operating Income (Loss)",
        "depreciation_addback": "Add: Depreciation & Amortisation",
        "provision_doubtful_debts": "Add: Provision for Doubtful Debts",
        "interest_reclassified": "Add: Interest Expense (reclassified to CFF)",
        "wc_delta_ar": "(Increase)/Decrease in Accounts Receivable",
        "wc_delta_inventory": "(Increase)/Decrease in Inventory",
        "wc_delta_prepaid": "(Increase)/Decrease in Prepaid Expenses",
        "wc_delta_undeposited": "(Increase)/Decrease in Undeposited Funds",
        "wc_delta_employee_advances": "(Increase)/Decrease in Employee Advances",
        "wc_delta_ap": "Increase/(Decrease) in Accounts Payable",
        "wc_delta_credit_cards": "Increase/(Decrease) in Credit Cards Payable",
        "wc_delta_accrued_expenses": "Increase/(Decrease) in Accrued Expenses",
        "wc_delta_payroll_liabilities": "Increase/(Decrease) in Payroll Liabilities",
        "net_cfo": "Net Cash from Operating Activities (CFO)",
        "net_cfi_capex": "Purchase of Property, Plant & Equipment (CAPEX)",
        "wc_delta_security_deposits": "(Increase)/Decrease in Security Deposits",
        "net_cfi": "Net Cash from Investing Activities (CFI)",
        "interest_paid": "Interest Paid",
        "borrowings_net": "Net Proceeds / (Repayment) of Borrowings",
        "equity_proceeds": "Proceeds from Capital / Equity Contributions",
        "net_cff": "Net Cash from Financing Activities (CFF)",
        "net_change_cash": "NET INCREASE / (DECREASE) IN CASH & CASH EQUIVALENTS",
        "opening_cash": "Cash & Cash Equivalents – Opening Balance",
        "closing_cash": "Cash & Cash Equivalents – Closing Balance",
        "reconciliation_check": "Reconciliation Check (Closing – Opening – Net Change)",
    }

    row_by_field = {}
    for field, label in fields.items():
        row = row_by_label.get(normalize_label(label))
        if row is None:
            raise ValueError(f"Required cash-flow statement row not found: {label}")
        row_by_field[field] = row

    def numeric_value(row, column, description):
        value = ws_cf.cell(row, column).value
        if not isinstance(value, (int, float)):
            raise ValueError(
                f"Expected a numeric cash-flow value for {description} "
                f"at row {row}, column {column}: {value!r}"
            )
        return float(value)

    ytd = {
        field: numeric_value(row, 3, fields[field])
        for field, row in row_by_field.items()
    }

    available_month_columns = {}
    for column in range(4, ws_cf.max_column + 1):
        header = ws_cf.cell(4, column).value
        if isinstance(header, datetime):
            available_month_columns[header.strftime("%b %Y")] = column
    missing_months = [month for month in expected_months if month not in available_month_columns]
    if missing_months:
        raise ValueError(f"Cash-flow statement is missing monthly columns: {', '.join(missing_months)}")
    months = list(expected_months)
    month_columns = [available_month_columns[month] for month in months]

    monthly = {
        field: [
            numeric_value(row, column, f"{fields[field]} ({months[index]})")
            for index, column in enumerate(month_columns)
        ]
        for field, row in row_by_field.items()
    }

    operating_fields = [
        "net_operating_loss", "depreciation_addback", "provision_doubtful_debts",
        "interest_reclassified", "wc_delta_ar", "wc_delta_inventory",
        "wc_delta_prepaid", "wc_delta_undeposited", "wc_delta_employee_advances",
        "wc_delta_ap", "wc_delta_credit_cards", "wc_delta_accrued_expenses",
        "wc_delta_payroll_liabilities",
    ]
    investing_fields = ["net_cfi_capex", "wc_delta_security_deposits"]
    financing_fields = ["interest_paid", "borrowings_net", "equity_proceeds"]

    def validate_period(values, period):
        checks = [
            ("CFO", sum(values[field] for field in operating_fields), values["net_cfo"]),
            ("CFI", sum(values[field] for field in investing_fields), values["net_cfi"]),
            ("CFF", sum(values[field] for field in financing_fields), values["net_cff"]),
            ("Net cash change", values["net_cfo"] + values["net_cfi"] + values["net_cff"], values["net_change_cash"]),
            ("Cash reconciliation", values["opening_cash"] + values["net_change_cash"], values["closing_cash"]),
        ]
        for label, calculated, reported in checks:
            if abs(calculated - reported) > 0.05:
                raise ValueError(
                    f"Cash-flow {label} does not reconcile for {period}: "
                    f"calculated {calculated:.2f}, statement {reported:.2f}"
                )
        if abs(values["reconciliation_check"]) > 0.05:
            raise ValueError(
                f"Cash-flow statement reconciliation row is nonzero for {period}: "
                f"{values['reconciliation_check']:.2f}"
            )

    validate_period(ytd, "YTD")
    for index, month in enumerate(months):
        validate_period({field: values[index] for field, values in monthly.items()}, month)

    title = ws_cf.cell(1, 1).value
    wb_cf.close()
    result = {
        "title": str(title or "Statement of Cash Flows (Indirect Method)"),
        **ytd,
        "months": months,
        "monthly": monthly,
    }
    other_working_capital_fields = [
        "wc_delta_undeposited", "wc_delta_employee_advances",
        "wc_delta_credit_cards", "wc_delta_accrued_expenses",
        "wc_delta_payroll_liabilities",
    ]
    result["wc_delta_other"] = sum(ytd[field] for field in other_working_capital_fields)
    result["monthly"]["wc_delta_other"] = [
        sum(monthly[field][index] for field in other_working_capital_fields)
        for index in range(len(months))
    ]
    return result


def extract_all():
    print(f"Loading workbook: {EXCEL_PATH}")
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    
    data = {}

    # 1. 007-DOAU data (Monthly & General financial data)
    ws_data = wb["007-DOAU data"]
    
    # Months header from row 3 (Cols 7 to 16 for Jan to Oct 2026)
    months = []
    month_cols = {}
    for col in range(7, 17):
        val = ws_data.cell(3, col).value
        m_str = val.strftime("%b %Y") if hasattr(val, "strftime") else str(val)[:7]
        months.append(m_str)
        month_cols[m_str] = col
    
    data["months"] = months
    
    # Monthly financial progression
    # Revenue (Row 106), COGS (Row 159), Gross Profit (Row 160), Admin Exp (Row 207), 
    # Sales Exp (Row 219), Total Expense (Row 221), Net Operating Income (Row 234),
    # Interest Exp (Row 229), Depreciation (Row 129), EBITDA (Row 246)
    monthly_trend = []
    for idx, m in enumerate(months):
        c = month_cols[m]
        rev = float(ws_data.cell(106, c).value or 0)
        cogs = float(ws_data.cell(159, c).value or 0)
        gp = float(ws_data.cell(160, c).value or 0)
        admin = float(ws_data.cell(207, c).value or 0)
        sales = float(ws_data.cell(219, c).value or 0)
        opex = float(ws_data.cell(221, c).value or 0)
        net_op = float(ws_data.cell(234, c).value or 0)
        interest = float(ws_data.cell(229, c).value or 0)
        dep = float(ws_data.cell(129, c).value or 0)
        ebitda = float(ws_data.cell(246, c).value or 0)
        
        monthly_trend.append({
            "month": m,
            "revenue": rev,
            "cogs": cogs,
            "gross_profit": gp,
            "gm_pct": (gp / rev) if rev != 0 else 0,
            "admin_exp": admin,
            "sales_exp": sales,
            "total_opex": opex,
            "net_operating_income": net_op,
            "interest": interest,
            "depreciation": dep,
            "ebitda": ebitda
        })
    data["monthly_trend"] = monthly_trend

    # 2. September vs October Comparison
    c_sep = 15
    c_oct = 16
    data["sep_vs_oct"] = {
        "revenue": {"sep": float(ws_data.cell(106, c_sep).value or 0), "oct": float(ws_data.cell(106, c_oct).value or 0)},
        "cogs": {"sep": float(ws_data.cell(159, c_sep).value or 0), "oct": float(ws_data.cell(159, c_oct).value or 0)},
        "gross_profit": {"sep": float(ws_data.cell(160, c_sep).value or 0), "oct": float(ws_data.cell(160, c_oct).value or 0)},
        "admin_exp": {"sep": float(ws_data.cell(207, c_sep).value or 0), "oct": float(ws_data.cell(207, c_oct).value or 0)},
        "sales_exp": {"sep": float(ws_data.cell(219, c_sep).value or 0), "oct": float(ws_data.cell(219, c_oct).value or 0)},
        "total_opex": {"sep": float(ws_data.cell(221, c_sep).value or 0), "oct": float(ws_data.cell(221, c_oct).value or 0)},
        "net_operating_income": {"sep": float(ws_data.cell(234, c_sep).value or 0), "oct": float(ws_data.cell(234, c_oct).value or 0)},
        "other_income": {"sep": float(ws_data.cell(227, c_sep).value or 0), "oct": float(ws_data.cell(227, c_oct).value or 0)},
        "other_expense": {"sep": float(ws_data.cell(232, c_sep).value or 0), "oct": float(ws_data.cell(232, c_oct).value or 0)},
        "ebitda": {"sep": float(ws_data.cell(246, c_sep).value or 0), "oct": float(ws_data.cell(246, c_oct).value or 0)},
    }

    # 3. PL YTD Aug 26 sheet (P&L YTD Jan-Oct 26 vs Jan-Oct 25)
    ws_ytd = wb["PL YTD Aug 26"]
    data["ytd_summary"] = {
        "revenue_ytd26": float(ws_ytd.cell(14, 2).value or 0),
        "revenue_ytd25": float(ws_ytd.cell(14, 3).value or 0),
        "revenue_chg": float(ws_ytd.cell(14, 4).value or 0),
        "revenue_chg_pct": float(ws_ytd.cell(14, 5).value or 0),
        "sales_ytd26": float(ws_ytd.cell(12, 2).value or 0),
        "sales_ytd25": float(ws_ytd.cell(12, 3).value or 0),
        "custom_proc_ytd26": float(ws_ytd.cell(9, 2).value or 0),
        "custom_proc_ytd25": float(ws_ytd.cell(9, 3).value or 0),
        "discounts_ytd26": float(ws_ytd.cell(10, 2).value or 0),
        "discounts_ytd25": float(ws_ytd.cell(10, 3).value or 0),
        "cogs_ytd26": float(ws_ytd.cell(52, 2).value or 0),
        "cogs_ytd25": float(ws_ytd.cell(52, 3).value or 0),
        "gross_profit_ytd26": float(ws_ytd.cell(53, 2).value or 0),
        "gross_profit_ytd25": float(ws_ytd.cell(53, 3).value or 0),
        "direct_labor_ytd26": float(ws_ytd.cell(23, 2).value or 0),
        "direct_labor_ytd25": float(ws_ytd.cell(23, 3).value or 0),
        "factory_oh_ytd26": float(ws_ytd.cell(51, 2).value or 0),
        "factory_oh_ytd25": float(ws_ytd.cell(51, 3).value or 0),
        "admin_exp_ytd26": float(ws_ytd.cell(96, 2).value or 0),
        "admin_exp_ytd25": float(ws_ytd.cell(96, 3).value or 0),
        "sales_exp_ytd26": float(ws_ytd.cell(106, 2).value or 0),
        "sales_exp_ytd25": float(ws_ytd.cell(106, 3).value or 0),
        "total_opex_ytd26": float(ws_ytd.cell(107, 2).value or 0),
        "total_opex_ytd25": float(ws_ytd.cell(107, 3).value or 0),
        "net_ordinary_income_ytd26": float(ws_ytd.cell(108, 2).value or 0),
        "net_ordinary_income_ytd25": float(ws_ytd.cell(108, 3).value or 0),
        "interest_exp_ytd26": float(ws_ytd.cell(115, 2).value or 0),
        "interest_exp_ytd25": float(ws_ytd.cell(115, 3).value or 0),
        "net_income_ytd26": float(ws_ytd.cell(118, 2).value or 0),
        "net_income_ytd25": float(ws_ytd.cell(118, 3).value or 0),
    }

    # 4. PL Sheet (October 2026 detailed P&L - Col 12 'After')
    ws_pl = wb["PL"]
    data["pl_oct"] = {
        "revenue_oct": float(ws_pl.cell(14, 12).value or 0),
        "sales_oct": float(ws_pl.cell(12, 12).value or 0),
        "custom_proc_oct": float(ws_pl.cell(9, 12).value or 0),
        "cogs_oct": float(ws_pl.cell(44, 12).value or 0),
        "direct_labor_oct": float(ws_pl.cell(22, 12).value or 0),
        "factory_oh_oct": float(ws_pl.cell(43, 12).value or 0),
        "gross_profit_oct": float(ws_pl.cell(45, 12).value or 0),
        "admin_exp_oct": float(ws_pl.cell(77, 12).value or 0),
        "sales_exp_oct": float(ws_pl.cell(87, 12).value or 0),
        "total_opex_oct": float(ws_pl.cell(88, 12).value or 0),
        "net_ordinary_income_oct": float(ws_pl.cell(89, 12).value or 0),
        "interest_oct": float(ws_pl.cell(95, 12).value or 0),
        "net_other_income_oct": float(ws_pl.cell(97, 12).value or 0),
        "net_income_oct": float(ws_pl.cell(98, 12).value or 0),
    }

    # 5. Adjusted EBITDA Schedule (from sheet CF)
    ws_cf = wb["CF"]
    data["ebitda_schedule"] = {
        "title": "Adjusted EBITDA Management Schedule",
        "ytd": {
            "depreciation": float(ws_cf.cell(10, 3).value or 0),
            "interest": float(ws_cf.cell(12, 3).value or 0),
            "ebitda": float(ws_cf.cell(14, 3).value or 0),
            "consulting_fee": float(ws_cf.cell(17, 3).value or 0),
            "bonus_vinh": float(ws_cf.cell(18, 3).value or 0),
            "loyalty_victor": float(ws_cf.cell(19, 3).value or 0),
            "rent_cliveden": float(ws_cf.cell(20, 3).value or 0),
            "total_addbacks": float(ws_cf.cell(21, 3).value or 0),
            "adjusted_ebitda": float(ws_cf.cell(23, 3).value or 0)
        },
        "oct": {
            "depreciation": float(ws_cf.cell(10, 13).value or 0),
            "interest": float(ws_cf.cell(12, 13).value or 0),
            "ebitda": float(ws_cf.cell(14, 13).value or 0),
            "consulting_fee": 0,
            "bonus_vinh": 0,
            "loyalty_victor": float(ws_cf.cell(19, 13).value or 0),
            "rent_cliveden": float(ws_cf.cell(20, 13).value or 0),
            "total_addbacks": float(ws_cf.cell(21, 13).value or 0),
            "adjusted_ebitda": float(ws_cf.cell(23, 13).value or 0)
        },
        "operational_ebitda": {
            "oct": float(ws_data.cell(246, c_oct).value or 0),
            "ytd": sum(float(ws_data.cell(246, c).value or 0) for c in range(7, 17))
        }
    }

    # 6. BS Sheet (October 31, 2026 - Col 11 'After')
    ws_bs = wb["BS"]
    data["balance_sheet"] = {
        "as_of": "October 31, 2026",
        "cash_and_equiv": float(ws_bs.cell(10, 11).value or 0),
        "ar_gross": float(ws_bs.cell(14, 11).value or 0),
        "ar_allowance": float(ws_bs.cell(13, 11).value or 0),
        "ar_net": float(ws_bs.cell(15, 11).value or 0),
        "inventory": float(ws_bs.cell(22, 11).value or 0),
        "inventory_clearing": float(ws_bs.cell(19, 11).value or 0),
        "inventory_wip": float(ws_bs.cell(20, 11).value or 0),
        "inventory_other": float(ws_bs.cell(21, 11).value or 0),
        "prepaid": float(ws_bs.cell(25, 11).value or 0),
        "undeposited_funds": float(ws_bs.cell(24, 11).value or 0),
        "total_current_assets": float(ws_bs.cell(26, 11).value or 0),
        
        "fixed_assets_cip": float(ws_bs.cell(36, 11).value or 0),
        "fixed_assets_prod_equip": float(ws_bs.cell(39, 11).value or 0),
        "fixed_assets_automation": float(ws_bs.cell(32, 11).value or 0),
        "fixed_assets_building_imp": float(ws_bs.cell(34, 11).value or 0) + float(ws_bs.cell(33, 11).value or 0),
        "fixed_assets_auto": float(ws_bs.cell(31, 11).value or 0),
        "fixed_assets_furniture_equipment": float(ws_bs.cell(37, 11).value or 0),
        "fixed_assets_office_computer": float(ws_bs.cell(35, 11).value or 0) + float(ws_bs.cell(38, 11).value or 0),
        "accum_depreciation": float(ws_bs.cell(30, 11).value or 0) + float(ws_bs.cell(28, 11).value or 0) + float(ws_bs.cell(29, 11).value or 0),
        "total_fixed_assets": float(ws_bs.cell(40, 11).value or 0),
        "total_assets": float(ws_bs.cell(45, 11).value or 0),
        
        "accounts_payable": float(ws_bs.cell(51, 11).value or 0),
        "credit_cards": float(ws_bs.cell(57, 11).value or 0),
        "accrued_expenses": float(ws_bs.cell(59, 11).value or 0),
        "loan_dan_d_pistachio": float(ws_bs.cell(64, 11).value or 0),
        "payroll_liabilities": float(ws_bs.cell(67, 11).value or 0),
        "total_current_liabilities": float(ws_bs.cell(69, 11).value or 0),
        
        "lt_loans": {
            "east_west_1": float(ws_bs.cell(71, 11).value or 0),
            "east_west_2": float(ws_bs.cell(72, 11).value or 0),
            "dan_d_foods_ltd": float(ws_bs.cell(73, 11).value or 0),
            "danway": float(ws_bs.cell(74, 11).value or 0),
            "ddp_llc": float(ws_bs.cell(75, 11).value or 0),
            "horseshoe": float(ws_bs.cell(76, 11).value or 0),
        },
        "total_lt_liabilities": float(ws_bs.cell(77, 11).value or 0),
        "total_liabilities": float(ws_bs.cell(78, 11).value or 0),
        
        "capital_stock": float(ws_bs.cell(80, 11).value or 0),
        "members_equity": float(ws_bs.cell(81, 11).value or 0),
        "retained_earnings": float(ws_bs.cell(82, 11).value or 0),
        "net_income_bs": float(ws_bs.cell(83, 11).value or 0),
        "total_equity": float(ws_bs.cell(84, 11).value or 0),
        "total_liabilities_and_equity": float(ws_bs.cell(85, 11).value or 0)
    }

    # 7. AR Aging Sheet
    ws_ar = wb["AR"]
    ar_rows = []
    for r in range(2, 60):
        name = ws_ar.cell(r, 1).value
        if not name or "total" in str(name).lower(): continue
        curr = float(ws_ar.cell(r, 2).value or 0)
        d1_30 = float(ws_ar.cell(r, 3).value or 0)
        d31_60 = float(ws_ar.cell(r, 4).value or 0)
        d61_90 = float(ws_ar.cell(r, 5).value or 0)
        d_over90 = float(ws_ar.cell(r, 7).value or 0)
        tot = float(ws_ar.cell(r, 8).value or 0)
        nature = ws_ar.cell(r, 14).value or ("Interco" if "DOF" in str(name) or "Dan" in str(name) else "3rd Party")
        
        if tot != 0 or curr != 0 or d_over90 != 0:
            ar_rows.append({
                "name": str(name).strip(),
                "current": curr,
                "d1_30": d1_30,
                "d31_60": d31_60,
                "d61_90": d61_90,
                "over90": d_over90,
                "total": tot,
                "nature": nature
            })
    ar_rows.sort(key=lambda x: x["total"], reverse=True)
    data["ar_aging"] = {
        "rows": ar_rows,
        "totals": {
            "current": float(ws_ar.cell(60, 2).value or 0),
            "d1_30": float(ws_ar.cell(60, 3).value or 0),
            "d31_60": float(ws_ar.cell(60, 4).value or 0),
            "d61_90": float(ws_ar.cell(60, 5).value or 0),
            "over90": float(ws_ar.cell(60, 7).value or 0),
            "total": float(ws_ar.cell(60, 8).value or 0),
            "intercompany": float(ws_ar.cell(62, 8).value or 0),
            "third_party": float(ws_ar.cell(63, 8).value or 0),
        }
    }

    # 8. AP Aging Sheet
    ws_ap = wb["AP"]
    ap_rows = []
    for r in range(2, 89):
        name = ws_ap.cell(r, 1).value
        if not name or "total" in str(name).lower(): continue
        curr = float(ws_ap.cell(r, 2).value or 0)
        d1_30 = float(ws_ap.cell(r, 4).value or 0)
        d31_60 = float(ws_ap.cell(r, 6).value or 0)
        d61_90 = float(ws_ap.cell(r, 8).value or 0)
        d_over90 = float(ws_ap.cell(r, 10).value or 0)
        tot = float(ws_ap.cell(r, 12).value or 0)
        kind = ws_ap.cell(r, 13).value or "Advance to supplier" if tot < 0 else "3rd Party"
        
        if tot != 0 or curr != 0:
            ap_rows.append({
                "name": str(name).strip(),
                "current": curr,
                "d1_30": d1_30,
                "d31_60": d31_60,
                "d61_90": d61_90,
                "over90": d_over90,
                "total": tot,
                "kind": kind
            })
    ap_rows.sort(key=lambda x: x["total"], reverse=True)
    data["ap_aging"] = {
        "rows": ap_rows,
        "totals": {
            "current": float(ws_ap.cell(89, 2).value or 0),
            "d1_30": float(ws_ap.cell(89, 4).value or 0),
            "d31_60": float(ws_ap.cell(89, 6).value or 0),
            "d61_90": float(ws_ap.cell(89, 8).value or 0),
            "over90": float(ws_ap.cell(89, 10).value or 0),
            "total": float(ws_ap.cell(89, 12).value or 0),
            "advance_to_supplier": float(ws_ap.cell(93, 12).value or 0),
            "intercompany": float(ws_ap.cell(94, 12).value or 0),
            "payable_to_3rd": float(ws_ap.cell(95, 12).value or 0),
        }
    }

    # 9. Top Customers (from 'Sales by cust' sheet)
    ws_cust = wb["Sales by cust"]
    cust_dict = defaultdict(lambda: {"sales": 0.0, "cost": 0.0, "gp": 0.0})
    for r in range(2, ws_cust.max_row + 1):
        c_name = ws_cust.cell(r, 1).value
        if not c_name: continue
        amt = float(ws_cust.cell(r, 11).value or 0)
        cost = float(ws_cust.cell(r, 13).value or 0)
        gp = float(ws_cust.cell(r, 14).value or 0)
        cust_dict[str(c_name).strip()]["sales"] += amt
        cust_dict[str(c_name).strip()]["cost"] += cost
        cust_dict[str(c_name).strip()]["gp"] += gp

    top_customers = []
    total_sales_all_cust = sum(v["sales"] for v in cust_dict.values())
    for name, v in cust_dict.items():
        gm = (v["gp"] / v["sales"]) if v["sales"] != 0 else 0
        share = (v["sales"] / total_sales_all_cust) if total_sales_all_cust != 0 else 0
        top_customers.append({
            "name": name,
            "sales": v["sales"],
            "cost": v["cost"],
            "gp": v["gp"],
            "gm_pct": gm,
            "share_pct": share
        })
    top_customers.sort(key=lambda x: x["sales"], reverse=True)
    data["top_customers"] = top_customers
    data["total_sales_cust"] = total_sales_all_cust

    # 10. Top Items (from 'GP' and 'Sales by cust' sheet)
    ws_gp = wb["GP"]
    item_sales = defaultdict(lambda: {"sales": 0.0, "cogs": 0.0})
    for r in range(2, ws_gp.max_row + 1):
        item = ws_gp.cell(r, 5).value
        acct = ws_gp.cell(r, 6).value
        debit = float(ws_gp.cell(r, 8).value or 0)
        credit = float(ws_gp.cell(r, 9).value or 0)
        if not item: continue
        item_str = str(item).strip()
        if acct == "Sales":
            item_sales[item_str]["sales"] += (credit - debit)
        elif acct == "Cost of Goods Sold":
            item_sales[item_str]["cogs"] += (debit - credit)

    top_items = []
    total_item_sales = sum(v["sales"] for v in item_sales.values())
    for name, v in item_sales.items():
        gp = v["sales"] - v["cogs"]
        gm = (gp / v["sales"]) if v["sales"] != 0 else 0
        share = (v["sales"] / total_item_sales) if total_item_sales != 0 else 0
        top_items.append({
            "name": name,
            "sales": v["sales"],
            "cogs": v["cogs"],
            "gp": gp,
            "gm_pct": gm,
            "share_pct": share
        })
    top_items.sort(key=lambda x: x["sales"], reverse=True)
    data["top_items"] = top_items
    data["total_item_sales"] = total_item_sales

    # 11. Inventory Analysis (from 'INV' sheet)
    ws_inv = wb["INV"]
    inventory_skus = []
    sku_pattern = re.compile(r"^[A-Za-z0-9_-]+\s*\(")
    for r in range(2, ws_inv.max_row + 1):
        item = ws_inv.cell(r, 5).value
        asset_value = ws_inv.cell(r, 9).value
        if not item or not sku_pattern.match(str(item).strip()):
            continue
        if not isinstance(asset_value, (int, float)):
            raise ValueError(f"Inventory SKU at row {r} has a non-numeric asset value: {asset_value!r}")
        inventory_skus.append({
            "name": str(item).strip(),
            "asset_value": float(asset_value),
        })

    inventory_sku_total = sum(item["asset_value"] for item in inventory_skus)
    inventory_sheet_total = float(ws_inv.cell(538, 9).value or 0)
    if abs(inventory_sku_total - inventory_sheet_total) > 0.05:
        raise ValueError(
            f"Inventory SKU details do not reconcile to INV sheet total: "
            f"{inventory_sku_total:.2f} vs {inventory_sheet_total:.2f}"
        )

    data["inventory_skus"] = inventory_skus
    data["inventory_sku_total"] = inventory_sku_total

    # Section totals
    data["inventory_breakdown"] = {
        "raw_nuts": float(ws_inv.cell(462, 9).value or 0),
        "raw_ingredients": float(ws_inv.cell(425, 9).value or 0),
        "raw_fruits": float(ws_inv.cell(378, 9).value or 0),
        "packaging": sum(float(ws_inv.cell(r, 9).value or 0) for r in [64, 99, 210, 217, 274, 303, 339, 353, 362]),
        "total_inventory_raw": float(ws_inv.cell(473, 9).value or 0),
        "finished_goods_bulk": float(ws_inv.cell(506, 9).value or 0),
        "finished_goods_pack": float(ws_inv.cell(535, 9).value or 0),
        "total_assembly": float(ws_inv.cell(536, 9).value or 0),
        "total_inventory_asset_value": float(ws_inv.cell(538, 9).value or 0),
        "bs_total_inventory": float(ws_bs.cell(22, 11).value or 0)
    }

    # 12. Cash-flow Statement parsed from its dedicated workbook
    data["cash_flow"] = parse_cash_flow_statement(CF_EXCEL_PATH, months)

    # 13. HR Report & Payroll Data
    data["hr_payroll"] = {
        "monthly_oct": {
            "direct_labor": float(ws_pl.cell(22, 12).value or 0),
            "direct_labor_base": float(ws_pl.cell(21, 12).value or 0),
            "direct_labor_taxes": float(ws_pl.cell(19, 12).value or 0),
            "production_payroll": float(ws_pl.cell(35, 12).value or 0),
            "admin_payroll": float(ws_pl.cell(72, 12).value or 0),
            "payroll_processing_fees": float(ws_pl.cell(69, 12).value or 0),
            "total_labor_oct": float(ws_pl.cell(22, 12).value or 0) + float(ws_pl.cell(35, 12).value or 0) + float(ws_pl.cell(72, 12).value or 0)
        },
        "ytd": {
            "direct_labor": float(ws_ytd.cell(23, 2).value or 0),
            "direct_labor_prior": float(ws_ytd.cell(23, 3).value or 0),
            "production_payroll": float(ws_ytd.cell(41, 2).value or 0),
            "production_payroll_prior": float(ws_ytd.cell(41, 3).value or 0),
            "admin_payroll": float(ws_ytd.cell(87, 2).value or 0),
            "admin_payroll_prior": float(ws_ytd.cell(87, 3).value or 0),
            "payroll_processing_fees": float(ws_ytd.cell(83, 2).value or 0),
            "payroll_processing_fees_prior": float(ws_ytd.cell(83, 3).value or 0),
            "total_labor_ytd26": float(ws_ytd.cell(23, 2).value or 0) + float(ws_ytd.cell(41, 2).value or 0) + float(ws_ytd.cell(87, 2).value or 0),
            "total_labor_ytd25": float(ws_ytd.cell(23, 3).value or 0) + float(ws_ytd.cell(41, 3).value or 0) + float(ws_ytd.cell(87, 3).value or 0),
        }
    }

    monthly_revenue_total = sum(item["revenue"] for item in monthly_trend)
    require_reconciles(
        "Monthly revenue total vs YTD P&L revenue",
        monthly_revenue_total,
        data["ytd_summary"]["revenue_ytd26"],
    )
    require_reconciles(
        "YTD gross profit vs revenue less COGS",
        data["ytd_summary"]["revenue_ytd26"] - data["ytd_summary"]["cogs_ytd26"],
        data["ytd_summary"]["gross_profit_ytd26"],
    )
    require_reconciles(
        "Balance Sheet assets vs liabilities and equity",
        data["balance_sheet"]["total_assets"],
        data["balance_sheet"]["total_liabilities_and_equity"],
    )
    require_reconciles(
        "AR aging total vs Balance Sheet net AR",
        data["ar_aging"]["totals"]["total"],
        data["balance_sheet"]["ar_net"],
    )
    require_reconciles(
        "AP aging total vs Balance Sheet accounts payable",
        data["ap_aging"]["totals"]["total"],
        data["balance_sheet"]["accounts_payable"],
    )

    data["report_metadata"] = {
        "reporting_period": months[-1],
        "monthly_source": {
            "workbook": os.path.basename(EXCEL_PATH),
            "sheet": "007-DOAU data",
        },
        "ytd_source": {
            "workbook": os.path.basename(EXCEL_PATH),
            "sheet": "PL YTD Aug 26",
        },
        "balance_sheet_source": {
            "workbook": os.path.basename(EXCEL_PATH),
            "sheet": "BS",
        },
        "cash_flow_source": {
            "workbook": os.path.basename(CF_EXCEL_PATH),
            "sheet": "CF",
        },
    }
    data["data_quality"] = {
        "monthly_revenue_total": monthly_revenue_total,
        "monthly_revenue_ytd_difference": (
            monthly_revenue_total - data["ytd_summary"]["revenue_ytd26"]
        ),
        "monthly_gross_profit_total": sum(
            item["gross_profit"] for item in monthly_trend
        ),
        "ytd_gross_profit": data["ytd_summary"]["gross_profit_ytd26"],
        "monthly_ytd_gross_profit_difference": (
            sum(item["gross_profit"] for item in monthly_trend)
            - data["ytd_summary"]["gross_profit_ytd26"]
        ),
        "balance_sheet_difference": (
            data["balance_sheet"]["total_assets"]
            - data["balance_sheet"]["total_liabilities_and_equity"]
        ),
        "ar_aging_bs_net_difference": (
            data["ar_aging"]["totals"]["total"]
            - data["balance_sheet"]["ar_net"]
        ),
        "ap_aging_bs_difference": (
            data["ap_aging"]["totals"]["total"]
            - data["balance_sheet"]["accounts_payable"]
        ),
        "inventory_bs_difference": (
            data["inventory_breakdown"]["bs_total_inventory"]
            - data["inventory_sku_total"]
        ),
        "prior_year_monthly_comparison_available": False,
        "headcount_data_available": False,
    }

    wb.close()
    os.makedirs(DATA_OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully extracted all data to: {OUTPUT_FILE}")
    print(f"Extracted keys: {list(data.keys())}")

if __name__ == "__main__":
    extract_all()
