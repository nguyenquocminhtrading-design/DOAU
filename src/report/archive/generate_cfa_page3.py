"""
CFA Research Report Page 3 HTML Generator.
Faithfully recreates the visual layout, 2-column grid, red header system,
and large-font financial figures from cfa_page_3.png.
"""

import os
from cfa_chart_components import (
    render_fig_badge_cards,
    render_stacked_bar_chart,
    render_dual_donuts,
    render_fig_customer_expansion,
    render_benchmark_bar_chart
)

def build_cfa_page_3_html():
    # 1. Figure 4: Holistic Solutions Cards
    fig4_cards = [
        {
            "label": "Margin lending",
            "pills": [
                {"text": "#2 market share, #1 margin loan room", "bg": "#a30008", "color": "#ffffff"}
            ]
        },
        {
            "label": "Brokerage service",
            "pills": [
                {"text": "#2 market share", "bg": "#f87171", "color": "#ffffff"},
                {"text": "#3 market share", "bg": "#dc2626", "color": "#ffffff"},
                {"text": "#2 Asia overall broker", "bg": "#a30008", "color": "#ffffff"}
            ]
        },
        {
            "label": "Proprietary trading",
            "pills": [
                {"text": "#1 revenue", "bg": "#a30008", "color": "#ffffff"}
            ]
        },
        {
            "label": "Asset management",
            "pills": [
                {"text": "#1 OEF performance", "bg": "#a30008", "color": "#ffffff"},
                {"text": "#1 fastest growing AM", "bg": "#880e4f", "color": "#ffffff"}
            ]
        },
        {
            "label": "Investment banking",
            "pills": [
                {"text": "#1 ECM", "bg": "#a30008", "color": "#ffffff"}
            ]
        }
    ]
    fig4_html = render_fig_badge_cards(fig4_cards, title="Fig 4. SSI holistic investment solutions")

    # 2. Figure 5: Revenue Segments Breakdown
    fig5_series = [
        {"name": "Brokerage", "values": [1200, 1600, 2800, 2200, 2500, 2100], "color": "#f87171"},
        {"name": "Margin Lending", "values": [900, 1200, 2100, 1900, 2150, 1900], "color": "#dc2626"},
        {"name": "Proprietary Trading", "values": [800, 1100, 1800, 1600, 1700, 1550], "color": "#991b1b"},
        {"name": "IB & Others", "values": [335, 467, 743, 636, 808, 758], "color": "#cbd5e1"}
    ]
    fig5_cats = ["19A", "20A", "21A", "22A", "23A", "9M24"]
    fig5_html = render_stacked_bar_chart(fig5_series, fig5_cats, title="Fig 5. SSI revenue segments breakdown", unit="(bn VND)", cagr="21.96%")

    # 3. Figure 6: Dual Donuts
    donut_left = {
        "title": "Overall market share",
        "items": [
            {"name": "VPS", "value": 19, "color": "#a30008"},
            {"name": "SSI", "value": 9, "color": "#f87171"},
            {"name": "TCBS", "value": 7, "color": "#dc2626"},
            {"name": "Others", "value": 65, "color": "#cbd5e1"}
        ]
    }
    donut_right = {
        "title": "Foreign institutional market share",
        "items": [
            {"name": "SSI", "value": 25, "color": "#a30008"},
            {"name": "Vietcap", "value": 23, "color": "#dc2626"},
            {"name": "HSC", "value": 23, "color": "#f87171"},
            {"name": "Others", "value": 29, "color": "#cbd5e1"}
        ]
    }
    fig6_html = render_dual_donuts(donut_left, donut_right, title="Fig 6. Brokerage market share in H1/2024")

    # 4. Figure 7: Customer Base Expansion
    fig7_html = render_fig_customer_expansion(title="Fig 7. SSI's strategy of customer base expansion")

    # 5. Figure 8: Peer Benchmarks
    fig8_benchmarks = [
        {"label": "China", "value": 3400, "share": "30.9%", "color": "#a30008"},
        {"label": "S.Korea", "value": 555, "share": "30.0%", "color": "#dc2626"},
        {"label": "Malaysia", "value": 206, "share": "50.8%", "color": "#f87171"},
        {"label": "Thailand", "value": 106, "share": "18.8%", "color": "#fca5a5"},
        {"label": "Philippines", "value": 26, "share": "6.5%", "color": "#cbd5e1"},
        {"label": "Vietnam", "value": 25, "share": "10.7%", "color": "#ef4444"}
    ]
    fig8_html = render_benchmark_bar_chart(fig8_benchmarks, title="Fig 8. AUM in other Asia countries", unit="Total AUM ($B)")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CFA Equity Research Report - Page 3</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 0;
  }}
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #111827;
    background-color: #f1f5f9;
    line-height: 1.32;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  .cfa-page-container {{
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
  }}

  @media print {{
    body {{
      background: #ffffff;
    }}
    .cfa-page-container {{
      margin: 0;
      box-shadow: none;
      width: 210mm;
      height: 297mm;
      page-break-after: always;
    }}
  }}

  /* LEFT COLUMN (31.5%) */
  .col-left {{
    display: flex;
    flex-direction: column;
    gap: 5px;
  }}

  /* RIGHT COLUMN (66%) */
  .col-right {{
    display: flex;
    flex-direction: column;
  }}

  /* SECTION HEADERS */
  .section-banner {{
    background-color: #a30008;
    color: #ffffff;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    padding: 3px 6px;
    margin-bottom: 4px;
  }}

  .editorial-lead {{
    color: #a30008;
    font-size: 9.2px;
    font-weight: 700;
    margin-top: 3.5px;
    margin-bottom: 1.5px;
  }}

  .editorial-lead-italic {{
    font-style: italic;
  }}

  .body-text {{
    font-size: 8.2px;
    line-height: 1.30;
    color: #1f2937;
    margin-bottom: 4px;
    text-align: justify;
  }}

  .body-text strong {{
    font-weight: 700;
    color: #0f172a;
  }}

  /* FIGURE BOXES (Left Column) */
  .figure-box {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 2px;
    margin-bottom: 2px;
  }}

  .figure-header {{
    background-color: #6e7073;
    color: #ffffff;
    font-size: 8.8px;
    font-weight: 800;
    padding: 2px 5px;
    text-align: center;
  }}

  .figure-content {{
    padding: 3px;
  }}

  .figure-source {{
    font-size: 6.8px;
    font-style: italic;
    color: #64748b;
    padding: 1px 5px 2px 5px;
  }}

  /* BADGE CARDS (Figure 4) */
  .badge-cards-container {{
    display: flex;
    flex-direction: column;
    gap: 2.5px;
  }}

  .badge-card-row {{
    display: flex;
    align-items: center;
    border: 1px solid #cbd5e1;
    border-radius: 3px;
    padding: 2px 3.5px;
    background: #f8fafc;
  }}

  .badge-label {{
    width: 38%;
    font-size: 7.8px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.1;
  }}

  .badge-pills {{
    width: 62%;
    display: flex;
    flex-direction: column;
    gap: 1.5px;
  }}

  .badge-pill {{
    display: block;
    text-align: center;
    font-size: 7.2px;
    font-weight: 700;
    padding: 1px 3px;
    border-radius: 9999px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}

  .badge-mini-legend {{
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 8px;
    padding-top: 2px;
  }}

  .legend-chip {{
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 1px;
  }}

  .legend-lbl {{
    font-size: 7.5px;
    font-weight: 600;
    color: #475569;
  }}

  /* FOOTER */
  .cfa-page-footer {{
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
  }}

  .footer-company {{
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  .footer-tag {{
    background: #ffffff;
    color: #a30008;
    padding: 0.5px 4px;
    border-radius: 2px;
    font-weight: 900;
    font-size: 8.5px;
  }}

  .footer-page {{
    font-size: 10px;
    font-weight: 800;
  }}
</style>
</head>
<body>

<div class="cfa-page-container">
  <!-- LEFT COLUMN (31.5%) -->
  <div class="col-left">
    {fig4_html}
    {fig5_html}
    {fig6_html}
    {fig7_html}
    {fig8_html}
  </div>

  <!-- RIGHT COLUMN (66%) -->
  <div class="col-right">
    <div class="section-banner">BUSINESS DESCRIPTION</div>
    <p class="body-text">
      <strong>SSI Securities Corporation (HOSE: SSI)</strong> has solidified its position as the longest-established securities firm with 24 years of development alongside the country's capital markets. Notably, SSI is the largest security firm in SEA by charter capital, totaling VND 18,130bn (as of Q3/2024). Utilizing the capital base, SSI has achieved top revenue performance with VND 7,108bn in 2023 and VND 6,308bn in 9M/2024, serving 600,000+ clients across Vietnam.
    </p>

    <div class="editorial-lead">A leading securities firm offers the most extensive product ecosystem,...</div>
    <p class="body-text">
      SSI offers a comprehensive investment product and service ecosystem targeting the highest standards. These offerings are designed to serve the investment preferences of all investor types in any economic conditions (Fig 4; Appendix F).
    </p>

    <div class="editorial-lead editorial-lead-italic">... yielding exceptional business performance across all key business sectors</div>
    <p class="body-text">
      SSI has held its position as a revenue leader for years from four main segments: <strong>(1)</strong> Brokerage, <strong>(2)</strong> Margin Lending, <strong>(3)</strong> Proprietary trading, and <strong>(4)</strong> Investment Banking, Asset Management, and Others (Fig 5).
    </p>
    <p class="body-text">
      <strong>Brokerage:</strong> By consistently building best-in-country research and broker teams for both retail and institutional clients, SSI market share consistently maintains 2nd rank (Fig 4). Notably, SSI is the only securities company that is consistently positioned in the top 3 across both customer segments (Fig 6).
    </p>
    <p class="body-text">
      <strong>Margin Lending:</strong> While SSI currently ranks 2nd in margin loan balance, they have the largest capacity for margin loan expansion with the available owner equity of 119.14% for further margin loans. In 2024F, SSI raised its charter capital to enhance margin lending capacity and solidify this segment as its primary growth driver.
    </p>
    <p class="body-text">
      <strong>Proprietary Trading:</strong> With top-tier asset base, SSI allocates 57.50% of assets on 2019-2023 average to proprietary trading, which generates substantial earnings and secures leadership in the segment. On average, over the past 5 years, SSI prioritizes stable investment assets with its main focus on CDs (49.53%), bonds (32.43%), and 11.66%, mostly in blue-chip equities.
    </p>
    <p class="body-text">
      <strong>Asset Management:</strong> SSI is recognized as the pioneering securities firm in asset management. By 2023, SSIAM managed a total AUM of VND 13,649bn and consistently outperformed the market. Notably, SSI-SCA delivered a 28.40% 3Y-return in 2021–2023 – the top performer among all open-ended funds.
    </p>
    <p class="body-text">
      <strong>Investment Banking:</strong> is an important attractor for institutional investors. Leading in ECM, SSI has mobilized USD 14bn+ through groundbreaking deals for Vietnam, reinforcing its network with major domestic and international institutions. SSI also plays a major role in SCIC's divestment deals, indicating solid growth prospects given promising pipelines ahead. Regarding DCM, SSI's bond issuance will be further supported by S&I Ratings, currently ranked fourth, within the limit of five credit rating agencies licensed by the government.
    </p>
    <p class="body-text">
      <em>Overall, SSI is the only securities firm with all four business segments consistently at the top ranking. This exceptional performance is expected to further accelerate, driven by the company's robust strategy and favorable industry conditions.</em>
    </p>

    <div class="section-banner" style="margin-top: 5px;">COMPANY STRATEGY</div>
    <p class="body-text">
      <em>SSI is known for its stability-focused business approach, which has successfully built a reputation for financial resilience. Nevertheless, this approach held SSI back in an intense race. Thus, SSI has actively transformed into a more dynamic business to seize the market potential. Evidently, SSI has been actively <strong>(1)</strong> promoting margin lending to meet expected rising demand, <strong>(2)</strong> broadening customer base, and <strong>(3)</strong> developing new products for investors of all asset levels, reinforcing its top-tier position.</em>
    </p>

    <div class="editorial-lead">Driving proactive leap towards margin lending to best absorb the upcoming market demand</div>
    <p class="body-text">
      SSI is strategically scaling margin lending operations to capitalize on rapid market participation growth. Evidently, recent charter capital raised an additional VND 4,533bn strengthening its capital foundation to expand the margin balance and promote lending activities. Additionally, SSI has crafted specialized product groups tailored to distinct customer segments, working closely with the broker team to effectively promote margin lending outreach. Moreover, by also providing competitive lending rates, SSI's substantial margin lending room is expected to fill up. While becoming more vibrant in margin lending, SSI will still maintain a prudent investment portfolio, focusing on CDs and bonds to sustain its principle of cautious practice. These improvements not only bolster SSI's competitive edge but also enable it to seize growing market potential, ultimately increasing margin lending market share.
    </p>

    <div class="editorial-lead">Expanding foreign institutional customer base through global partnerships and strong financial capability</div>
    <p class="body-text">
      After securing strong local corporations' network (~90% of total market cap), SSI is pivoting towards expanding its foreign institutional customer base. By expanding partnership with leading global financial institutions (e.g. Goldman Sachs), this portrays SSI as a credible business partner in eyes of investment community, hence enhancing their attractiveness with potential global institutional investors. Besides, SSI's well-prepared financial capabilities will accommodate the expected influx of foreign institutional investors in the light of Vietnam's upcoming upgrades to EM (Appendix N).
    </p>

    <div class="editorial-lead">Building bridge to young generation: SSI's pathway to conquer this future retail customer group</div>
    <p class="body-text">
      In response to Vietnam's evolving investor landscape, SSI is focusing on expanding its younger customers (aged 18–35), comprising 20% of its current clientele through a focused "technology-internet plus" customer acquisition strategy, via account opening promotions, financial education, and frequent trading platforms upgrades (IBoard Pro's user-friendliness to make stock investing more accessible). In fact, SSI is promoting partnerships with reputable media to organize numerous advisory programs, especially targeting students like "The Moneyverse" (+15,000 student participation) (Appendix F4). Given Vietnam's retail-driven stock market, this strategy will attract a broad retail investor base, particularly tech-savvy young customers, to grab a competitive share of this key future demographic.
    </p>

    <div class="editorial-lead">Focusing on product development to enhance accessibility for investors of all asset levels</div>
    <p class="body-text">
      <strong>Strategic product development to cater to the growing mass affluent clients, emerging as the primary segment,...</strong><br/>
      SSI is well-known serving the high net-worth customer segment. Moreover, with Vietnam's rising middle-class income, the mass affluent investors are emerging as a key customer group, accounting for 72.12% of total clients. Recognizing this trend, SSI is set to launch its wealth management products in early 2025, strategically catering to this growing customer segment. This also lays the foundation for future development to capture long-term trends of wealth management, driven by <strong>(1)</strong> intergenerational wealth transfers and <strong>(2)</strong> Vietnam's AUM by securities firms trailing behind Asian counterparts (Fig 8). Notably, the offered wealth management services will streamline SSI's product range, enhancing customer lifetime value and ensuring sustainable development.
    </p>
    <p class="body-text">
      <strong>...while ensuring inclusivity for all investors</strong><br/>
      Furthermore, SSI also crafts products to serve the smaller investment value investor brackets. Evidently, in 2023, SSI introduced iFollow – a convenient investment solution allowing users to replicate sample portfolio with an investment value of only VND 30mn.
    </p>
  </div>

  <!-- FOOTER -->
  <div class="cfa-page-footer">
    <div class="footer-company">
      <span>SSI Securities Corporation</span>
      <span class="footer-tag">SSI</span>
    </div>
    <div class="footer-page">3</div>
  </div>
</div>

</body>
</html>
"""
    return html

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "reports", "generated")
    os.makedirs(out_dir, exist_ok=True)
    out_html = os.path.join(out_dir, "cfa_page_3_reconstructed.html")
    content = build_cfa_page_3_html()
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated HTML: {out_html}")
