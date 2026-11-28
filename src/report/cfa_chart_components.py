"""
CFA Research Report Chart Renderer with Enhanced Typography.
Ensures larger, crisp, bold chart typography suited for institutional equity reports.
"""

import math
from html import escape as escape_html


def compact_currency(value, prefix="$"):
    val = float(value)
    if abs(val) >= 1_000_000:
        s = f"{abs(val) / 1_000_000:.1f}M"
    elif abs(val) >= 1_000:
        s = f"{abs(val) / 1_000:.0f}k"
    else:
        s = f"{abs(val):.0f}"
    res = f"{prefix}{s}" if prefix else s
    return f"({res})" if val < 0 else res


def render_fig_badge_cards(cards, title="Fig 4. SSI holistic investment solutions"):
    html = [
        f'<div class="figure-box">',
        f'  <div class="figure-header">{escape_html(title)}</div>',
        f'  <div class="figure-content badge-cards-container">'
    ]
    for card in cards:
        html.append(f'    <div class="badge-card-row">')
        html.append(f'      <div class="badge-label">{escape_html(card["label"])}</div>')
        html.append(f'      <div class="badge-pills">')
        for pill in card.get("pills", []):
            bg = pill.get("bg", "#a30008")
            color = pill.get("color", "#ffffff")
            html.append(f'        <span class="badge-pill" style="background-color: {bg}; color: {color};">{escape_html(pill["text"])}</span>')
        html.append(f'      </div>')
        html.append(f'    </div>')
    
    html.append(f'  </div>')
    # Mini legend matching original: General, Retail, Institutional
    html.append(f'  <div class="badge-mini-legend">')
    html.append(f'    <span class="legend-chip" style="background:#cbd5e1;"></span><span class="legend-lbl">General</span>')
    html.append(f'    <span class="legend-chip" style="background:#f87171;"></span><span class="legend-lbl">Retail</span>')
    html.append(f'    <span class="legend-chip" style="background:#a30008;"></span><span class="legend-lbl">Institutional</span>')
    html.append(f'  </div>')
    html.append(f'  <div class="figure-source">Source: SSI, Team analysis</div>')
    html.append(f'</div>')
    return "\n".join(html)


def render_stacked_bar_chart(series_list, categories, title="Fig 5. SSI revenue segments breakdown", unit="(bn VND)", cagr="21.96%"):
    width, height = 340, 205
    pad_left, pad_right, pad_top, pad_bottom = 26, 46, 32, 34
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    num_cats = len(categories)
    cat_totals = [sum(s["values"][i] for s in series_list) for i in range(num_cats)]
    max_total = max(cat_totals) * 1.15 if cat_totals else 100

    svg = [
        f'<svg class="report-chart" viewBox="0 0 {width} {height}" width="100%" height="{height}px" xmlns="http://www.w3.org/2000/svg">',
        f'  <text x="{pad_left}" y="14" font-size="9" font-weight="700" fill="#64748b">{unit}</text>',
        f'  <text x="{width/2}" y="14" font-size="10.5" font-weight="800" fill="#a30008" text-anchor="middle">{cagr} CAGR</text>'
    ]

    # Red CAGR badge on right side
    svg.append(f'  <rect x="{width - pad_right + 4}" y="12" width="38" height="12" fill="#a30008" rx="2"/>')
    svg.append(f'  <text x="{width - pad_right + 23}" y="21" font-size="7.5" font-weight="800" fill="#ffffff" text-anchor="middle">\'19-\'23 CAGR</text>')
    cagr_values = ["26.75%", "23.33%", "19.75%", "21.59%"]
    for idx, c_val in enumerate(cagr_values):
        cy = 28 + idx * 13
        svg.append(f'  <rect x="{width - pad_right + 4}" y="{cy}" width="38" height="11" fill="#f87171" rx="1.5"/>')
        svg.append(f'  <text x="{width - pad_right + 23}" y="{cy + 8.5}" font-size="8" font-weight="800" fill="#ffffff" text-anchor="middle">{c_val}</text>')

    col_w = plot_w / num_cats
    bar_w = min(28.0, col_w * 0.62)

    for i, cat in enumerate(categories):
        x_center = pad_left + i * col_w + col_w / 2
        bx = x_center - bar_w / 2
        curr_y = pad_top + plot_h

        # Stack from bottom to top
        for s in series_list:
            val = s["values"][i]
            bar_h = (val / max_total) * plot_h
            by = curr_y - bar_h
            color = s.get("color", "#a30008")
            svg.append(f'  <rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" fill="{color}" rx="0.5"/>')
            # Text inside segment
            if bar_h >= 13:
                svg.append(f'  <text x="{x_center:.1f}" y="{by + bar_h/2 + 3.5:.1f}" font-size="8.5" font-weight="700" fill="#ffffff" text-anchor="middle">{val:.0f}</text>')
            curr_y = by

        # Total on top with LARGE font
        tot = cat_totals[i]
        svg.append(f'  <text x="{x_center:.1f}" y="{curr_y - 4:.1f}" font-size="10" font-weight="800" fill="#0f172a" text-anchor="middle">{tot:.0f}</text>')
        # X-axis label
        svg.append(f'  <text x="{x_center:.1f}" y="{height - pad_bottom + 13}" font-size="9.5" font-weight="700" fill="#334155" text-anchor="middle">{escape_html(cat)}</text>')

    # Legend at bottom (2x2)
    leg_rows = [
        [series_list[0], series_list[1]],
        [series_list[2], series_list[3]]
    ]
    for r_idx, row in enumerate(leg_rows):
        ly = height - 16 + r_idx * 11
        for c_idx, s in enumerate(row):
            lx = pad_left + c_idx * 110
            svg.append(f'  <rect x="{lx}" y="{ly - 7}" width="7.5" height="7.5" fill="{s["color"]}" rx="1"/>')
            svg.append(f'  <text x="{lx + 10}" y="{ly}" font-size="8" font-weight="700" fill="#334155">{escape_html(s["name"])}</text>')

    svg.append('</svg>')

    return f"""
<div class="figure-box">
  <div class="figure-header">{escape_html(title)}</div>
  <div class="figure-content">
    {"".join(svg)}
  </div>
  <div class="figure-source">Source: SSI, Team analysis</div>
</div>
"""


def render_dual_donuts(donut_left, donut_right, title="Fig 6. Brokerage market share in H1/2024"):
    width, height = 340, 155
    svg = [f'<svg class="report-chart" viewBox="0 0 {width} {height}" width="100%" height="{height}px" xmlns="http://www.w3.org/2000/svg">']

    donuts = [
        {"data": donut_left, "cx": 85, "cy": 60, "title": donut_left.get("title", "Overall market share")},
        {"data": donut_right, "cx": 255, "cy": 60, "title": donut_right.get("title", "Foreign institutional market share")}
    ]

    r_outer = 40
    r_inner = 21

    for d in donuts:
        cx, cy = d["cx"], d["cy"]
        items = d["data"]["items"]
        total = sum(item["value"] for item in items) or 1
        start_angle = -math.pi / 2

        # Subtitle above donut
        svg.append(f'  <text x="{cx}" y="14" font-size="9" font-weight="700" fill="#1e293b" text-anchor="middle">{escape_html(d["title"])}</text>')

        for item in items:
            frac = item["value"] / total
            end_angle = start_angle + frac * 2 * math.pi
            color = item.get("color", "#a30008")

            x1 = cx + r_outer * math.cos(start_angle)
            y1 = cy + r_outer * math.sin(start_angle)
            x2 = cx + r_outer * math.cos(end_angle)
            y2 = cy + r_outer * math.sin(end_angle)
            x3 = cx + r_inner * math.cos(end_angle)
            y3 = cy + r_inner * math.sin(end_angle)
            x4 = cx + r_inner * math.cos(start_angle)
            y4 = cy + r_inner * math.sin(start_angle)

            large_arc = 1 if frac > 0.5 else 0
            path_d = (
                f"M {x1:.2f} {y1:.2f} "
                f"A {r_outer} {r_outer} 0 {large_arc} 1 {x2:.2f} {y2:.2f} "
                f"L {x3:.2f} {y3:.2f} "
                f"A {r_inner} {r_inner} 0 {large_arc} 0 {x4:.2f} {y4:.2f} Z"
            )
            svg.append(f'  <path d="{path_d}" fill="{color}" stroke="#ffffff" stroke-width="1.2"/>')

            # Percentage label inside slice
            if frac >= 0.08:
                mid_angle = (start_angle + end_angle) / 2
                lbl_r = (r_outer + r_inner) / 2
                lx = cx + lbl_r * math.cos(mid_angle)
                ly = cy + lbl_r * math.sin(mid_angle)
                txt_color = "#ffffff" if color in ["#a30008", "#991b1b", "#dc2626", "#ef4444", "#f87171"] else "#1e293b"
                svg.append(f'  <text x="{lx:.1f}" y="{ly + 3.5:.1f}" font-size="9" font-weight="800" fill="{txt_color}" text-anchor="middle">{frac*100:.0f}%</text>')

            start_angle = end_angle

    # Two distinct legends for Left & Right
    # Left legend
    l_items = donut_left.get("items", [])
    for idx, item in enumerate(l_items):
        col = idx % 2
        row = idx // 2
        lx = 25 + col * 60
        ly = 125 + row * 12
        svg.append(f'  <rect x="{lx}" y="{ly - 7}" width="7" height="7" fill="{item["color"]}" rx="1"/>')
        svg.append(f'  <text x="{lx + 10}" y="{ly}" font-size="8" font-weight="700" fill="#334155">{escape_html(item["name"])}</text>')

    # Right legend
    r_items = donut_right.get("items", [])
    for idx, item in enumerate(r_items):
        col = idx % 2
        row = idx // 2
        lx = 195 + col * 65
        ly = 125 + row * 12
        svg.append(f'  <rect x="{lx}" y="{ly - 7}" width="7" height="7" fill="{item["color"]}" rx="1"/>')
        svg.append(f'  <text x="{lx + 10}" y="{ly}" font-size="8" font-weight="700" fill="#334155">{escape_html(item["name"])}</text>')

    svg.append('</svg>')

    return f"""
<div class="figure-box">
  <div class="figure-header">{escape_html(title)}</div>
  <div class="figure-content">
    {"".join(svg)}
  </div>
  <div class="figure-source">Source: FiinPro, Team analysis</div>
</div>
"""


def render_fig_customer_expansion(title="Fig 7. SSI's strategy of customer base expansion"):
    """
    Renders the trajectory curve diagram for Customer Base Expansion matching Figure 7.
    """
    width, height = 340, 150
    svg = f"""
    <svg class="report-chart" viewBox="0 0 {width} {height}" width="100%" height="{height}px" xmlns="http://www.w3.org/2000/svg">
      <!-- Axes -->
      <line x1="30" y1="125" x2="320" y2="125" stroke="#94a3b8" stroke-width="1.5"/>
      <line x1="30" y1="125" x2="30" y2="15" stroke="#94a3b8" stroke-width="1.5"/>
      <text x="30" y="10" font-size="8" font-weight="700" fill="#64748b">Assets</text>
      <text x="320" y="138" font-size="8" font-weight="700" fill="#64748b" text-anchor="end">Age</text>
      
      <!-- Growth curves -->
      <path d="M 35 120 Q 120 115 170 85 T 300 35" fill="none" stroke="#cbd5e1" stroke-width="8" stroke-linecap="round"/>
      <path d="M 35 120 Q 120 110 170 75 T 280 25" fill="none" stroke="#f1f5f9" stroke-width="22" stroke-linecap="round"/>

      <!-- Milestone Circles -->
      <!-- 1. Young customer -->
      <circle cx="65" cy="108" r="16" fill="#fca5a5"/>
      <text x="65" y="106" font-size="7.5" font-weight="800" fill="#ffffff" text-anchor="middle">Young</text>
      <text x="65" y="115" font-size="7.5" font-weight="800" fill="#ffffff" text-anchor="middle">customer</text>

      <!-- 2. Affluent-class -->
      <circle cx="125" cy="85" r="19" fill="#dc2626"/>
      <text x="125" y="83" font-size="8" font-weight="800" fill="#ffffff" text-anchor="middle">Affluent-</text>
      <text x="125" y="92" font-size="8" font-weight="800" fill="#ffffff" text-anchor="middle">class</text>

      <!-- 3. Wealthy customer -->
      <circle cx="195" cy="60" r="17" fill="#fca5a5"/>
      <text x="195" y="58" font-size="7.5" font-weight="800" fill="#ffffff" text-anchor="middle">Wealthy</text>
      <text x="195" y="67" font-size="7.5" font-weight="800" fill="#ffffff" text-anchor="middle">customer</text>

      <!-- 4. Elderly customers -->
      <circle cx="265" cy="40" r="18" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="1"/>
      <text x="265" y="38" font-size="7.5" font-weight="800" fill="#334155" text-anchor="middle">Elderly</text>
      <text x="265" y="47" font-size="7.5" font-weight="800" fill="#334155" text-anchor="middle">customers</text>

      <!-- X-axis Age milestones -->
      <text x="50" y="137" font-size="7.5" font-weight="600" fill="#64748b" text-anchor="middle">Adolescence</text>
      <text x="130" y="137" font-size="7.5" font-weight="600" fill="#64748b" text-anchor="middle">Middle age</text>
      <text x="210" y="137" font-size="7.5" font-weight="600" fill="#64748b" text-anchor="middle">Retirement</text>
      <text x="280" y="137" font-size="7.5" font-weight="600" fill="#64748b" text-anchor="middle">Inheritance</text>
    </svg>
    """
    return f"""
<div class="figure-box">
  <div class="figure-header">{escape_html(title)}</div>
  <div class="figure-content">
    {svg}
  </div>
  <div class="figure-source">Source: SSI, TCBS, VPS, Team analysis</div>
</div>
"""


def render_benchmark_bar_chart(benchmarks, title="Fig 8. AUM in other Asia countries", unit="Total AUM ($B)"):
    width, height = 340, 160
    pad_left, pad_right, pad_top, pad_bottom = 30, 15, 22, 46
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    max_val = max(b["value"] for b in benchmarks) * 1.15 or 100
    num = len(benchmarks)
    col_w = plot_w / num
    bar_w = min(22.0, col_w * 0.52)

    svg = [
        f'<svg class="report-chart" viewBox="0 0 {width} {height}" width="100%" height="{height}px" xmlns="http://www.w3.org/2000/svg">',
        f'  <text x="{pad_left}" y="13" font-size="8.5" font-weight="700" fill="#64748b">{unit}</text>'
    ]

    for i, b in enumerate(benchmarks):
        x_center = pad_left + i * col_w + col_w / 2
        bx = x_center - bar_w / 2
        val = b["value"]
        # Scale for visualization
        log_h = (math.log10(val) / math.log10(max_val)) * plot_h if val > 1 else (val / max_val) * plot_h
        by = pad_top + plot_h - log_h
        color = b.get("color", "#a30008" if i == 0 else "#dc2626")

        svg.append(f'  <rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{log_h:.1f}" fill="{color}" rx="0.5"/>')
        svg.append(f'  <text x="{x_center:.1f}" y="{by - 4:.1f}" font-size="9" font-weight="800" fill="#0f172a" text-anchor="middle">{val:.0f}</text>')
        svg.append(f'  <text x="{x_center:.1f}" y="{height - pad_bottom + 12}" font-size="8" font-weight="700" fill="#334155" text-anchor="middle">{escape_html(b["label"])}</text>')

        # % Capitalization share box below
        share = b.get("share", "10%")
        svg.append(f'  <rect x="{bx - 2:.1f}" y="{height - pad_bottom + 16}" width="{bar_w + 4:.1f}" height="14" fill="#fca5a5" rx="1"/>')
        svg.append(f'  <text x="{x_center:.1f}" y="{height - pad_bottom + 26.5}" font-size="7.5" font-weight="800" fill="#7f1d1d" text-anchor="middle">{share}</text>')

    # Label for % Capitalization row
    svg.append(f'  <text x="2" y="{height - pad_bottom + 26.5}" font-size="7" font-weight="700" fill="#64748b">% Cap</text>')

    svg.append('</svg>')

    return f"""
<div class="figure-box">
  <div class="figure-header">{escape_html(title)}</div>
  <div class="figure-content">
    {"".join(svg)}
  </div>
  <div class="figure-source">Source: FiinPro, Team analysis</div>
</div>
"""
