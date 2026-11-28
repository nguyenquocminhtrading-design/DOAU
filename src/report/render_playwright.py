"""
Playwright-based Multi-Page Renderer & Visual Inspector for CFA Reports.
Takes generated HTML and renders pixel-accurate PNG screenshots for each page and print-ready PDFs.
"""

import os
import sys
from playwright.sync_api import sync_playwright

def render_multi_page_report(html_path, output_dir, pdf_name="DOAU_Comprehensive_Management_Report.pdf"):
    if not os.path.isabs(html_path):
        html_path = os.path.abspath(html_path)

    if not os.path.exists(html_path):
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    file_url = f"file:///{html_path.replace(os.sep, '/')}"
    os.makedirs(output_dir, exist_ok=True)
    pages_dir = os.path.join(output_dir, "rendered_pages")
    os.makedirs(pages_dir, exist_ok=True)

    pdf_path = os.path.join(output_dir, pdf_name)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Viewport set to standard A4 ratio at 2x device scale for crisp charts
        page = browser.new_page(viewport={"width": 1200, "height": 1700}, device_scale_factor=2)
        
        print(f"Loading URL: {file_url}")
        page.goto(file_url, wait_until="networkidle")

        # 1. Capture each page individually
        page_containers = page.locator(".cfa-page-container")
        count = page_containers.count()
        print(f"Detected {count} CFA report pages.")

        for i in range(count):
            container = page_containers.nth(i)
            page_num_str = f"{i + 1:02d}"
            png_name = f"page_{page_num_str}.png"
            png_path = os.path.join(pages_dir, png_name)
            container.screenshot(path=png_path)
            print(f"Rendered Page {i + 1}: {png_path} ({os.path.getsize(png_path):,} bytes)")

        # 2. Export vector PDF (all pages)
        page.pdf(
            path=pdf_path,
            format="A4",
            print_background=True,
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}
        )
        print(f"Exported Vector PDF: {pdf_path} ({os.path.getsize(pdf_path):,} bytes)")

        browser.close()

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    gen_dir = os.path.join(repo_root, "reports", "generated")
    html_target = os.path.join(gen_dir, "DOAU_Comprehensive_Management_Report.html")

    render_multi_page_report(html_target, gen_dir)
