import json
import os
import re

from report_metrics import build_report_metrics, safe_divide


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
DATA_FILE = os.path.join(REPO_ROOT, "data", "generated", "extracted_data.json")
OUTPUT_DIR = os.path.join(REPO_ROOT, "reports", "generated")


def _money(value):
    if value is None:
        return "N/A"
    value = float(value)
    rendered = f"${abs(value):,.0f}"
    return f"({rendered})" if value < 0 else rendered


def _percentage(value):
    return "N/A" if value is None else f"{float(value):.1%}"


def _ratio(value):
    return "N/A" if value is None else f"{float(value):.2f}x"


def _name(value):
    return re.sub(r"\s+", " ", str(value)).strip()


def _markdown_text(value):
    text = str(value)
    return re.sub(r"([\\`*_{}\[\]|#])", r"\\\1", text)


def _difference_note(label, difference):
    if difference is None or abs(float(difference)) <= 0.5:
        return None
    return f"{label} is {_money(difference)}; review the source reconciliation."


def build_page_analyses(data):
    metrics = build_report_metrics(data)
    ytd = data["ytd_summary"]
    monthly = metrics["latest_month"]
    cash_flow = data["cash_flow"]
    payroll = data["hr_payroll"]["ytd"]
    quality = data.get("data_quality", {})
    report_period = metrics["report_period"]

    executive_observations = [
        (
            f"YTD revenue was {_money(ytd['revenue_ytd26'])} versus "
            f"{_money(ytd['revenue_ytd25'])} in the comparable prior-year period, "
            f"a change of {_money(metrics['ytd_revenue_change'])} "
            f"({_percentage(metrics['ytd_revenue_change_pct'])})."
        ),
        (
            f"{report_period} revenue was {_money(monthly['revenue'])}; "
            f"month-over-month change was "
            f"{_percentage(metrics['monthly_revenue_change_pct'])}."
        ),
        (
            f"Reported YTD gross margin was "
            f"{_percentage(metrics['ytd_gross_margin'])}; YTD net income was "
            f"{_money(ytd['net_income_ytd26'])}."
        ),
    ]
    gross_profit_note = _difference_note(
        "Monthly gross-profit total versus YTD P&L gross profit",
        metrics["monthly_ytd_gross_profit_difference"],
    )
    executive_limitations = [
        "These observations describe reported workbook values; they do not establish causes or prescribe actions.",
        "Management-account figures are unaudited.",
    ]
    if gross_profit_note:
        executive_limitations.append(gross_profit_note)

    top_customer = metrics["top_customer"]
    sales_observations = [
        (
            f"The top three customers represent "
            f"{_percentage(metrics['top_three_customer_share'])} of positive "
            "sales in the extracted customer rows."
        ),
        (
            f"Highest sales in the extracted customer rows were "
            f"{_money(top_customer['sales'])} for {_name(top_customer['name'])}."
            if top_customer else "No customer sales rows were available."
        ),
    ]

    financial_observations = [
        (
            f"YTD gross profit was {_money(ytd['gross_profit_ytd26'])} versus "
            f"{_money(ytd['gross_profit_ytd25'])} in the prior-year period."
        ),
        (
            f"YTD operating expenses were {_money(ytd['total_opex_ytd26'])} "
            f"versus {_money(ytd['total_opex_ytd25'])}."
        ),
        (
            f"YTD net income was {_money(ytd['net_income_ytd26'])} versus "
            f"{_money(ytd['net_income_ytd25'])}."
        ),
    ]
    if gross_profit_note:
        financial_observations.append(gross_profit_note)

    highest_gp = metrics["highest_gp_item"]
    lowest_margin = metrics["lowest_margin_item"]
    commercial_observations = [
        (
            f"Highest reported gross profit among positive-sales product rows "
            f"was {_money(highest_gp['gp'])} for {_name(highest_gp['name'])}."
            if highest_gp else "No positive-sales product rows were available."
        ),
        (
            f"Lowest reported margin among positive-sales product rows was "
            f"{_percentage(lowest_margin['gm_pct'])} for "
            f"{_name(lowest_margin['name'])}."
            if lowest_margin else "No product margin comparison was available."
        ),
    ]

    inventory = data["inventory_breakdown"]
    inventory_difference = quality.get(
        "inventory_bs_difference",
        inventory["bs_total_inventory"] - data["inventory_sku_total"],
    )
    positive_skus = sorted(
        (item for item in data["inventory_skus"] if item["asset_value"] > 0),
        key=lambda item: item["asset_value"],
        reverse=True,
    )
    positive_sku_total = sum(item["asset_value"] for item in positive_skus)
    top_sku_share = safe_divide(
        sum(item["asset_value"] for item in positive_skus[:3]),
        positive_sku_total,
    )
    inventory_observations = [
        (
            f"Positive-value SKU detail totals {_money(data['inventory_sku_total'])}; "
            f"Balance Sheet inventory is {_money(inventory['bs_total_inventory'])} "
            f"(difference {_money(inventory_difference)})."
        ),
        (
            f"The top three positive-value SKUs account for "
            f"{_percentage(top_sku_share)} of positive SKU detail."
        ),
    ]
    if positive_skus:
        inventory_observations.append(
            "Largest positive-value SKUs: "
            + "; ".join(
                f"{_name(item['name'])} ({_money(item['asset_value'])})"
                for item in positive_skus[:3]
            )
            + "."
        )

    ar_difference = quality.get("ar_aging_bs_net_difference")
    ap_difference = quality.get("ap_aging_bs_difference")
    ap_total = data["ap_aging"]["totals"]["total"]
    ap_over90 = data["ap_aging"]["totals"]["over90"]
    working_capital_observations = [
        (
            f"Net working capital was {_money(metrics['net_working_capital'])}; "
            f"current ratio was {_ratio(metrics['current_ratio'])}."
        ),
        (
            f"AR over 90 days was "
            f"{_percentage(metrics['ar_over90_share'])} of reported AR aging."
        ),
        (
            f"Reported AP over-90 bucket was {_money(ap_over90)}. No percentage "
            f"is calculated against total AP ({_money(ap_total)}) because the "
            "aging includes advances/intercompany balances that can offset "
            "trade payables."
        ),
    ]
    for label, difference in (
        ("AR aging to Balance Sheet net AR difference", ar_difference),
        ("AP aging to Balance Sheet AP difference", ap_difference),
    ):
        note = _difference_note(label, difference)
        if note:
            working_capital_observations.append(note)

    cash_observations = [
        (
            f"YTD CFO was {_money(cash_flow['net_cfo'])}, CFI was "
            f"{_money(cash_flow['net_cfi'])}, and CFF was "
            f"{_money(cash_flow['net_cff'])}; net cash change was "
            f"{_money(cash_flow['net_change_cash'])}."
        ),
        (
            f"Opening cash {_money(cash_flow['opening_cash'])} plus net cash "
            f"change reconciles to closing cash "
            f"{_money(cash_flow['closing_cash'])}."
        ),
        f"Reported property and equipment purchases were {_money(cash_flow['net_cfi_capex'])}.",
    ]

    payroll_categories = [
        ("Direct labor", payroll["direct_labor"]),
        ("Production payroll", payroll["production_payroll"]),
        ("Administration payroll", payroll["admin_payroll"]),
        ("Payroll processing fees", payroll["payroll_processing_fees"]),
    ]
    payroll_total = sum(value for _, value in payroll_categories)
    payroll_mix = "; ".join(
        f"{label}: {_percentage(safe_divide(value, payroll_total))}"
        for label, value in payroll_categories
    ) if payroll_total > 0 else "Payroll mix is unavailable because the total is not positive."
    payroll_observations = [
        (
            f"Core payroll changed by {_money(metrics['ytd_labor_change'])} "
            f"({_percentage(metrics['ytd_labor_change_pct'])}) year over year."
        ),
        (
            f"Core payroll as a share of revenue was "
            f"{_percentage(metrics['labor_as_revenue_pct'])}, versus "
            f"{_percentage(metrics['prior_labor_as_revenue_pct'])} in the prior year."
        ),
        f"Reported payroll composition: {payroll_mix}.",
    ]

    common_limitations = [
        "Rule-based analysis of workbook data; management review is required.",
        "No external AI service or network request is used by this script.",
    ]
    return [
        {
            "page_id": "executive-summary",
            "title": "Executive Summary",
            "source": "007-DOAU data, YTD P&L, monthly P&L, Balance Sheet, and cash-flow workbook",
            "observations": executive_observations,
            "limitations": executive_limitations,
        },
        {
            "page_id": "sales",
            "title": "Sales",
            "source": "Sales by cust sheet",
            "observations": sales_observations,
            "limitations": common_limitations + [
                "Customer concentration uses positive sales in the extracted customer rows."
            ],
        },
        {
            "page_id": "financial-performance",
            "title": "Financial Performance",
            "source": "PL and PL YTD sheets",
            "observations": financial_observations,
            "limitations": common_limitations,
        },
        {
            "page_id": "commercial-analysis",
            "title": "Commercial Analysis",
            "source": "GP sheet",
            "observations": commercial_observations,
            "limitations": common_limitations + [
                "Product gross profit and margin depend on workbook cost allocations; these observations are not pricing recommendations."
            ],
        },
        {
            "page_id": "inventory",
            "title": "Inventory",
            "source": "INV sheet and Balance Sheet",
            "observations": inventory_observations,
            "limitations": common_limitations + [
                "The difference between SKU detail and Balance Sheet inventory is not allocated to individual SKUs."
            ],
        },
        {
            "page_id": "working-capital",
            "title": "Balance Sheet and Working Capital",
            "source": "Balance Sheet, AR, and AP sheets",
            "observations": working_capital_observations,
            "limitations": common_limitations + [
                "The net working-capital measure is not adjusted for intercompany balances."
            ],
        },
        {
            "page_id": "capex-cash-flow",
            "title": "CapEx and Cash Flow",
            "source": "Indirect cash-flow workbook and Balance Sheet",
            "observations": cash_observations,
            "limitations": common_limitations + [
                "Balance-sheet asset balances are not a monthly CapEx trend."
            ],
        },
        {
            "page_id": "payroll",
            "title": "Payroll Cost Analysis",
            "source": "PL and PL YTD sheets",
            "observations": payroll_observations,
            "limitations": common_limitations + [
                "Payroll as a share of revenue is not a productivity measure without hours and output data."
            ],
        },
    ]


def render_markdown(report_period, analyses):
    lines = [
        f"# DOAU Page Analysis — {report_period}",
        "",
        "Generated locally from `data/extracted_data.json`; no data is sent to an external AI service.",
        "",
    ]
    for page in analyses:
        lines.extend(
            [
                f"## {page['title']}",
                "",
                f"**Source:** {page['source']}",
                "",
                "### Observations",
                "",
            ]
        )
        lines.extend(f"- {_markdown_text(item)}" for item in page["observations"])
        lines.extend(["", "### Limitations", ""])
        lines.extend(f"- {_markdown_text(item)}" for item in page["limitations"])
        lines.append("")
    return "\n".join(lines)


def analyze_file(data_file=DATA_FILE, output_dir=OUTPUT_DIR):
    with open(data_file, "r", encoding="utf-8") as source:
        data = json.load(source)
    analyses = build_page_analyses(data)
    report_period = data["months"][-1]
    safe_period = re.sub(r"[^A-Za-z0-9_-]+", "_", report_period).strip("_")
    output_path = os.path.join(
        output_dir,
        f"DOAU_Page_Analysis_{safe_period}.md",
    )
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as output:
        output.write(render_markdown(report_period, analyses))
    return output_path


if __name__ == "__main__":
    print(f"Generated local page analysis: {analyze_file()}")
