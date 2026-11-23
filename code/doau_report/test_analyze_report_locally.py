import json
import os
import tempfile
import unittest

from analyze_report_locally import (
    analyze_file,
    build_page_analyses,
    render_markdown,
)


def _sample_data():
    return {
        "months": ["Sep 2026", "Oct 2026"],
        "monthly_trend": [
            {"month": "Sep 2026", "revenue": 90, "gross_profit": -3},
            {"month": "Oct 2026", "revenue": 100, "gross_profit": -5},
        ],
        "ytd_summary": {
            "revenue_ytd26": 180,
            "revenue_ytd25": 200,
            "gross_profit_ytd26": -10,
            "gross_profit_ytd25": 20,
            "net_income_ytd26": -20,
            "net_income_ytd25": 5,
            "total_opex_ytd26": 30,
            "total_opex_ytd25": 25,
        },
        "pl_oct": {"revenue_oct": 100, "gross_profit_oct": -5},
        "balance_sheet": {
            "total_current_assets": 80,
            "total_current_liabilities": 100,
            "total_liabilities": 120,
            "total_equity": 60,
        },
        "ar_aging": {"totals": {"over90": 5, "total": 50}},
        "ap_aging": {"totals": {"over90": 4, "total": 40}},
        "hr_payroll": {
            "ytd": {
                "direct_labor": 10,
                "production_payroll": 8,
                "admin_payroll": 7,
                "payroll_processing_fees": 1,
                "total_labor_ytd26": 25,
                "total_labor_ytd25": 30,
            }
        },
        "top_customers": [
            {"name": "Synthetic Customer A", "sales": 50},
            {"name": "Synthetic Customer B", "sales": 20},
            {"name": "Synthetic Customer C", "sales": 10},
        ],
        "total_sales_cust": 80,
        "top_items": [
            {"name": "Synthetic Product A", "sales": 30, "gp": 3, "gm_pct": 0.1},
            {"name": "Synthetic Product B", "sales": 20, "gp": -2, "gm_pct": -0.1},
        ],
        "cash_flow": {
            "net_cfo": -20,
            "net_cfi": 5,
            "net_cff": 10,
            "net_change_cash": -5,
            "opening_cash": 100,
            "closing_cash": 95,
            "net_cfi_capex": 3,
        },
        "inventory_skus": [
            {"name": "Synthetic SKU A", "asset_value": 12},
            {"name": "Synthetic SKU B", "asset_value": 8},
        ],
        "inventory_sku_total": 20,
        "inventory_breakdown": {"bs_total_inventory": 25},
        "data_quality": {
            "inventory_bs_difference": 5,
            "ar_aging_bs_net_difference": 0,
            "ap_aging_bs_difference": 0,
            "monthly_ytd_gross_profit_difference": 2,
        },
    }


class LocalReportAnalysisTests(unittest.TestCase):
    def test_builds_eight_page_analyses_from_report_data(self):
        analyses = build_page_analyses(_sample_data())

        self.assertEqual(len(analyses), 8)
        self.assertEqual(analyses[0]["page_id"], "executive-summary")
        self.assertEqual(analyses[-1]["page_id"], "payroll")
        self.assertTrue(
            any("difference $5" in item for item in analyses[4]["observations"])
        )
        self.assertTrue(
            any("Synthetic SKU A" in item for item in analyses[4]["observations"])
        )
        markdown = render_markdown("Oct 2026", analyses)
        self.assertIn("Generated locally", markdown)
        self.assertIn("No external AI service", markdown)

    def test_writes_analysis_to_local_output_directory(self):
        with tempfile.TemporaryDirectory() as output_dir:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".json",
                delete=False,
            ) as source:
                json.dump(_sample_data(), source)
                source_path = source.name
            try:
                output_path = analyze_file(source_path, output_dir)
            finally:
                os.remove(source_path)

            self.assertTrue(os.path.isfile(output_path))
            self.assertTrue(output_path.endswith("DOAU_Page_Analysis_Oct_2026.md"))

    def test_negative_ap_aging_bucket_is_reported_as_amount_not_percentage(self):
        data = _sample_data()
        data["ap_aging"]["totals"] = {"over90": -10, "total": 40}

        page = build_page_analyses(data)[5]

        self.assertIn(
            "Reported AP over-90 bucket was ($10)",
            page["observations"][2],
        )
        self.assertIn(
            "No percentage is calculated",
            page["observations"][2],
        )


if __name__ == "__main__":
    unittest.main()
