from html import escape as escape_html


def safe_divide(numerator, denominator):
    if denominator in (None, 0):
        return None
    return numerator / denominator


def percent_change(current, prior):
    if prior in (None, 0):
        return None
    return (current - prior) / abs(prior)


def _cash_flow_svg(cash_flow):
    items = [
        ("Operating (CFO)", cash_flow["net_cfo"]),
        ("Investing (CFI)", cash_flow["net_cfi"]),
        ("Financing (CFF)", cash_flow["net_cff"]),
        ("Net cash change", cash_flow["net_change_cash"]),
    ]
    width, height = 560, 166
    label_x, zero_x = 4, 280
    half_bar_width = 160
    max_value = max(abs(value) for _, value in items) or 1
    rows = []

    for index, (label, value) in enumerate(items):
        y = 20 + index * 32
        bar_width = abs(value) / max_value * half_bar_width
        x = zero_x - bar_width if value < 0 else zero_x
        color = "#991b1b" if value < 0 else "#166534"
        value_label = f"${abs(value):,.0f}"
        if value < 0:
            value_label = f"({value_label})"
        if bar_width >= max(64, len(value_label) * 6 + 12):
            value_x = x + 7 if value < 0 else x + bar_width - 7
            text_anchor = "start" if value < 0 else "end"
            text_class = "data-label data-label--inside"
            text_color = "#ffffff"
        else:
            value_x = x - 7 if value < 0 else x + bar_width + 7
            text_anchor = "end" if value < 0 else "start"
            text_class = "data-label data-label--outside"
            text_color = "#1e293b"
        rows.append(
            f'<text x="{label_x}" y="{y + 13}" font-size="10" fill="#334155">'
            f'{escape_html(label)}</text>'
            f'<rect x="{x:.1f}" y="{y}" width="{bar_width:.1f}" height="18" '
            f'rx="1" fill="{color}"/>'
            f'<text class="{text_class}" x="{value_x:.1f}" y="{y + 13}" '
            f'text-anchor="{text_anchor}" font-size="10" font-weight="700" '
            f'fill="{text_color}">{value_label}</text>'
        )

    return (
        f'<svg class="report-chart" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Year-to-date cash flow components in US dollars">'
        '<title>Year-to-date cash flow components in US dollars</title>'
        f'<line x1="{zero_x}" y1="8" x2="{zero_x}" y2="{height - 5}" '
        f'stroke="#94a3b8" stroke-width="1"/>'
        f'{"".join(rows)}'
        f'</svg>'
    )


def _payroll_mix_svg(payroll):
    categories = [
        ("Direct labor", payroll["direct_labor"], "#0b2545"),
        ("Production payroll", payroll["production_payroll"], "#3b82a0"),
        ("Administration payroll", payroll["admin_payroll"], "#c9a84c"),
        ("Payroll processing fees", payroll["payroll_processing_fees"], "#94a3b8"),
    ]
    total = sum(max(0.0, value) for _, value, _ in categories)
    if total <= 0:
        raise ValueError("Cannot render payroll composition without positive payroll values")

    width, height = 560, 170
    bar_x, bar_y, bar_width, bar_height = 8, 28, 544, 28
    segments = []
    legend = []
    cursor = bar_x
    for index, (label, value, color) in enumerate(categories):
        segment_width = bar_width * max(0.0, value) / total
        segments.append(
            f'<rect x="{cursor:.2f}" y="{bar_y}" width="{segment_width:.2f}" '
            f'height="{bar_height}" fill="{color}"/>'
        )
        if segment_width >= 48:
            label_color = "#0b2545" if color in ("#c9a84c", "#94a3b8") else "#ffffff"
            segments.append(
                f'<text class="data-label data-label--inside" x="{cursor + segment_width / 2:.2f}" '
                f'y="{bar_y + 18}" text-anchor="middle" font-size="10" font-weight="700" '
                f'fill="{label_color}">{value / total:.1%}</text>'
            )
        legend_x = 8 + (index % 2) * 274
        legend_y = 84 + (index // 2) * 34
        legend.append(
            f'<rect x="{legend_x}" y="{legend_y - 9}" width="10" height="10" '
            f'rx="1" fill="{color}"/>'
            f'<text x="{legend_x + 15}" y="{legend_y}" font-size="9" '
            f'fill="#334155">{escape_html(label)} — ${value:,.0f} '
            f'({value / total:.1%})</text>'
        )
        cursor += segment_width

    return (
        f'<svg class="report-chart" viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Year-to-date payroll composition in US dollars">'
        '<title>Year-to-date payroll composition in US dollars</title>'
        f'{"".join(segments)}'
        '<text x="8" y="17" font-size="9" fill="#64748b">YTD payroll mix · USD</text>'
        f'{"".join(legend)}'
        '</svg>'
    )


def build_report_metrics(data):
    months = data["months"]
    monthly = data["monthly_trend"]
    ytd = data["ytd_summary"]
    pl = data["pl_oct"]
    bs = data["balance_sheet"]
    ar = data["ar_aging"]["totals"]
    ap = data["ap_aging"]["totals"]
    labor = data["hr_payroll"]["ytd"]
    latest = monthly[-1]
    prior_month = monthly[-2] if len(monthly) > 1 else None
    top_customers = data["top_customers"]
    positive_customer_sales = sum(
        max(0.0, customer["sales"]) for customer in top_customers
    )
    positive_sales_items = [
        item for item in data["top_items"] if item["sales"] > 0
    ]

    return {
        "report_period": months[-1],
        "prior_period": months[-2] if len(months) > 1 else None,
        "latest_month": latest,
        "prior_month": prior_month,
        "monthly_revenue_change_pct": (
            percent_change(latest["revenue"], prior_month["revenue"])
            if prior_month else None
        ),
        "ytd_revenue_change": ytd["revenue_ytd26"] - ytd["revenue_ytd25"],
        "ytd_revenue_change_pct": percent_change(
            ytd["revenue_ytd26"], ytd["revenue_ytd25"]
        ),
        "ytd_gross_margin": safe_divide(
            ytd["gross_profit_ytd26"], ytd["revenue_ytd26"]
        ),
        "monthly_ytd_gross_profit_difference": (
            sum(item["gross_profit"] for item in monthly)
            - ytd["gross_profit_ytd26"]
        ),
        "monthly_gross_profit_total": sum(
            item["gross_profit"] for item in monthly
        ),
        "prior_ytd_gross_margin": safe_divide(
            ytd["gross_profit_ytd25"], ytd["revenue_ytd25"]
        ),
        "month_gross_margin": safe_divide(
            pl["gross_profit_oct"], pl["revenue_oct"]
        ),
        "current_ratio": safe_divide(
            bs["total_current_assets"], bs["total_current_liabilities"]
        ),
        "debt_equity_ratio": safe_divide(
            bs["total_liabilities"], bs["total_equity"]
        ),
        "net_working_capital": (
            bs["total_current_assets"] - bs["total_current_liabilities"]
        ),
        "top_three_customer_share": safe_divide(
            sum(max(0.0, customer["sales"]) for customer in top_customers[:3]),
            positive_customer_sales,
        ),
        "top_five_customer_share": safe_divide(
            sum(max(0.0, customer["sales"]) for customer in top_customers[:5]),
            positive_customer_sales,
        ),
        "positive_customer_sales_total": positive_customer_sales,
        "ar_over90_share": safe_divide(ar["over90"], ar["total"]),
        "ap_over90_share": safe_divide(ap["over90"], ap["total"]),
        "ytd_labor_change": (
            labor["total_labor_ytd26"] - labor["total_labor_ytd25"]
        ),
        "ytd_labor_change_pct": percent_change(
            labor["total_labor_ytd26"], labor["total_labor_ytd25"]
        ),
        "labor_as_revenue_pct": safe_divide(
            labor["total_labor_ytd26"], ytd["revenue_ytd26"]
        ),
        "prior_labor_as_revenue_pct": safe_divide(
            labor["total_labor_ytd25"], ytd["revenue_ytd25"]
        ),
        "top_customer": top_customers[0] if top_customers else None,
        "highest_gp_item": (
            max(positive_sales_items, key=lambda item: item["gp"])
            if positive_sales_items else None
        ),
        "lowest_margin_item": (
            min(positive_sales_items, key=lambda item: item["gm_pct"])
            if positive_sales_items else None
        ),
        "cash_flow_svg": _cash_flow_svg(data["cash_flow"]),
        "payroll_mix_svg": _payroll_mix_svg(labor),
    }
