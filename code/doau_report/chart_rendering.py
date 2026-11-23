import math
from html import escape as escape_html


def compact_money(value):
    value = float(value)
    if abs(value) >= 1_000_000:
        rendered = f"${abs(value) / 1_000_000:.1f}M"
    else:
        rendered = f"${abs(value) / 1_000:.0f}k"
    return f"({rendered})" if value < 0 else rendered


def svg_line_chart(monthly, value_key):
    values = [float(item[value_key]) for item in monthly]
    if not values:
        raise ValueError("Cannot render a sales trend chart without monthly values")

    width, height = 760, 270
    left, right, top, bottom = 58, 742, 30, 184
    chart_max = max(values) * 1.15 or 1
    x_step = (right - left) / max(1, len(values) - 1)
    points = []
    for index, value in enumerate(values):
        x = left + index * x_step
        y = bottom - (value / chart_max) * (bottom - top)
        points.append((x, y))

    grid = []
    for fraction in (0.25, 0.5, 0.75, 1):
        y = bottom - fraction * (bottom - top)
        grid.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#e2e8f0"/>'
            f'<text x="{left - 8}" y="{y + 3:.1f}" text-anchor="end" font-size="10" fill="#64748b">'
            f'${chart_max * fraction / 1_000_000:.1f}M</text>'
        )

    point_markup = []
    for index, (item, (x, y), value) in enumerate(zip(monthly, points, values)):
        month = escape_html(str(item["month"]).split()[0])
        value_label = f"${value / 1_000_000:.2f}M"
        if index:
            change = (value - values[index - 1]) / values[index - 1] if values[index - 1] else 0
            change_label = f"{change:+.1%}"
        else:
            change_label = "—"
        point_markup.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#c9a84c" stroke="#0b2545" stroke-width="1.5"/>'
            f'<text class="data-label" x="{x:.1f}" y="{max(top - 5, y - 11):.1f}" text-anchor="middle" '
            f'font-size="10" font-weight="700" fill="#0b2545">{value_label}</text>'
            f'<text x="{x:.1f}" y="{bottom + 20}" text-anchor="middle" font-size="10" fill="#334155">{month}</text>'
            f'<text x="{x:.1f}" y="{bottom + 36}" text-anchor="middle" font-size="9" fill="#64748b">{change_label}</text>'
        )

    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return (
        f'<svg class="report-chart" viewBox="0 0 {width} {height}" role="img" aria-label="Monthly sales trend">'
        '<title>Monthly sales trend</title>'
        f'<text x="{left}" y="16" font-size="10" fill="#64748b">Sales (USD)</text>'
        f'{"".join(grid)}'
        f'<polyline points="{polyline}" fill="none" stroke="#0b2545" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
        f'{"".join(point_markup)}'
        f'<text x="{left}" y="{height - 3}" font-size="9" fill="#64748b">MoM change</text>'
        f'</svg>'
    )


def svg_pie_chart(
    items,
    aria_label,
    legend_font_size=9,
    show_slice_percentages=True,
    bold_legend_percentages=True,
):
    values = [max(0.0, float(item["value"])) for item in items]
    total = sum(values)
    if not total:
        raise ValueError(f"Cannot render {aria_label}: all pie-chart values are zero or negative")

    width, height = 480, 280
    center_x, center_y, radius = 122, 140, 108
    colors = ["#0b2545", "#c9a84c", "#8b0000", "#3b82a0", "#6b7280", "#94a3b8"]
    start_angle = -math.pi / 2
    slices = []
    legend = []
    for index, (item, value) in enumerate(zip(items, values)):
        if value <= 0:
            continue
        fraction = value / total
        end_angle = start_angle + fraction * 2 * math.pi
        x1 = center_x + radius * math.cos(start_angle)
        y1 = center_y + radius * math.sin(start_angle)
        x2 = center_x + radius * math.cos(end_angle)
        y2 = center_y + radius * math.sin(end_angle)
        large_arc = 1 if fraction > 0.5 else 0
        color = colors[index % len(colors)]
        slices.append(
            f'<path d="M {center_x} {center_y} L {x1:.2f} {y1:.2f} '
            f'A {radius} {radius} 0 {large_arc} 1 {x2:.2f} {y2:.2f} Z" '
            f'fill="{color}" stroke="#ffffff" stroke-width="2"/>'
        )
        label = escape_html(str(item["name"]))
        if len(label) > 24:
            label = escape_html(str(item["name"])[:22] + "...")
        percentage = value / total * 100
        if show_slice_percentages and percentage >= 6:
            middle_angle = (start_angle + end_angle) / 2
            label_radius = radius * 0.62
            label_x = center_x + label_radius * math.cos(middle_angle)
            label_y = center_y + label_radius * math.sin(middle_angle)
            slices.append(
                f'<text class="data-label" x="{label_x:.1f}" y="{label_y:.1f}" text-anchor="middle" '
                f'dominant-baseline="middle" font-size="12" font-weight="800" '
                f'fill="#ffffff" stroke="#0b2545" stroke-width="0.8" '
                f'paint-order="stroke">{percentage:.1f}%</text>'
            )
        legend_y = 26 + index * 38
        percentage_markup = (
            f'<tspan font-weight="800" fill="#0b2545">{percentage:.1f}%</tspan>'
            if bold_legend_percentages
            else f'{percentage:.1f}%'
        )
        legend.append(
            f'<rect x="250" y="{legend_y - 9}" width="10" height="10" rx="1" fill="{color}"/>'
            f'<text x="268" y="{legend_y}" font-size="{legend_font_size}" font-weight="700" fill="#1e293b">{label}</text>'
            f'<text x="268" y="{legend_y + 14}" font-size="{legend_font_size - 1}" fill="#64748b">'
            f'{compact_money(value)} · {percentage_markup}</text>'
        )
        start_angle = end_angle

    return (
        f'<svg class="report-chart" viewBox="0 0 {width} {height}" role="img" aria-label="{escape_html(aria_label)}">'
        f'<title>{escape_html(aria_label)}</title>'
        f'{"".join(slices)}{"".join(legend)}'
        f'<text x="{center_x}" y="{center_y + 5}" text-anchor="middle" font-size="10" font-weight="700" fill="#0b2545">{compact_money(total)}</text>'
        f'</svg>'
    )


def svg_product_bars(items, value_key, diverging=False):
    if not items:
        raise ValueError("Cannot render product chart without product rows")

    width, row_height = 460, 32
    height = 24 + len(items) * row_height
    label_x, bar_start, bar_end, value_x = 2, 142, 380, 456
    max_value = max(abs(float(item[value_key])) for item in items) or 1
    zero_x = (bar_start + bar_end) / 2 if diverging else bar_start
    plot_width = bar_end - bar_start
    rows = []
    for index, item in enumerate(items):
        value = float(item[value_key])
        y = 20 + index * row_height
        label = str(item["name"])
        if len(label) > 22:
            label = label[:19] + "..."
        label = escape_html(label)
        if diverging:
            bar_width = abs(value) / max_value * (plot_width / 2)
            x = zero_x - bar_width if value < 0 else zero_x
            color = "#991b1b" if value < 0 else "#166534"
        else:
            bar_width = max(0, value) / max_value * plot_width
            x = bar_start
            color = "#0b2545"

        value_label = compact_money(value)
        minimum_inside_width = max(46, len(value_label) * 6 + 12)
        if bar_width >= minimum_inside_width:
            if diverging and value < 0:
                label_x_value = x + 7
                label_anchor = "start"
            else:
                label_x_value = x + bar_width - 7
                label_anchor = "end"
            value_markup = (
                f'<text class="data-label data-label--inside" x="{label_x_value:.1f}" y="{y + 12}" '
                f'text-anchor="{label_anchor}" font-size="9" font-weight="700" fill="#ffffff">{value_label}</text>'
            )
        else:
            outside_x = x - 6 if diverging and value < 0 else x + bar_width + 6
            outside_anchor = "end" if diverging and value < 0 else "start"
            value_markup = (
                f'<text class="data-label data-label--outside" x="{outside_x:.1f}" y="{y + 12}" '
                f'text-anchor="{outside_anchor}" font-size="9" font-weight="700" fill="#1e293b">{value_label}</text>'
            )

        rows.append(
            f'<text x="{label_x}" y="{y + 12}" font-size="9" fill="#334155">{label}</text>'
            f'<rect x="{x:.1f}" y="{y}" width="{bar_width:.1f}" height="17" rx="1" fill="{color}"/>'
            f'{value_markup}'
        )

    baseline = (
        f'<line x1="{zero_x}" y1="8" x2="{zero_x}" y2="{height - 2}" stroke="#64748b" stroke-width="1"/>'
        if diverging else ""
    )
    chart_label = "Gross profit by product" if diverging else "Sales by product"
    return (
        f'<svg class="report-chart" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{escape_html(chart_label)}">'
        f'<title>{escape_html(chart_label)}</title>'
        f'{baseline}{"".join(rows)}</svg>'
    )
