import unittest

from report_metrics import build_report_metrics, percent_change, safe_divide


class ReportMetricsTests(unittest.TestCase):
    def test_safe_ratios_handle_zero_denominators(self):
        self.assertIsNone(safe_divide(1, 0))
        self.assertIsNone(percent_change(10, 0))
        self.assertAlmostEqual(percent_change(80, 100), -0.2)

    def test_report_metrics_are_derived_from_source_data(self):
        data = {
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
                {"name": "A", "sales": 50},
                {"name": "B", "sales": 20},
                {"name": "C", "sales": 10},
            ],
            "total_sales_cust": 80,
            "top_items": [
                {"name": "Item A", "sales": 30, "gp": 3, "gm_pct": 0.1},
                {"name": "Item B", "sales": 20, "gp": -2, "gm_pct": -0.1},
            ],
            "cash_flow": {
                "net_cfo": -20,
                "net_cfi": 5,
                "net_cff": 10,
                "net_change_cash": -5,
            },
        }

        metrics = build_report_metrics(data)

        self.assertEqual(metrics["report_period"], "Oct 2026")
        self.assertAlmostEqual(metrics["monthly_revenue_change_pct"], 100 / 90 - 1)
        self.assertAlmostEqual(metrics["top_three_customer_share"], 1)
        self.assertAlmostEqual(metrics["net_working_capital"], -20)
        self.assertAlmostEqual(metrics["monthly_ytd_gross_profit_difference"], 2)
        self.assertIn("Operating (CFO)", metrics["cash_flow_svg"])
        self.assertIn('class="data-label data-label--inside"', metrics["cash_flow_svg"])
        self.assertIn('class="data-label data-label--outside"', metrics["cash_flow_svg"])
        self.assertIn("Payroll processing fees", metrics["payroll_mix_svg"])
        self.assertIn("38.5%", metrics["payroll_mix_svg"])
        self.assertIn('class="data-label data-label--inside"', metrics["payroll_mix_svg"])

    def test_ratio_metrics_report_unavailable_denominators(self):
        data = {
            "months": ["Oct 2026"],
            "monthly_trend": [
                {"month": "Oct 2026", "revenue": 100, "gross_profit": 10}
            ],
            "ytd_summary": {
                "revenue_ytd26": 0,
                "revenue_ytd25": 0,
                "gross_profit_ytd26": 0,
                "gross_profit_ytd25": 0,
            },
            "pl_oct": {"revenue_oct": 0, "gross_profit_oct": 0},
            "balance_sheet": {
                "total_current_assets": 10,
                "total_current_liabilities": 0,
                "total_liabilities": 5,
                "total_equity": 0,
            },
            "ar_aging": {"totals": {"over90": 0, "total": 0}},
            "ap_aging": {"totals": {"over90": 0, "total": 0}},
            "hr_payroll": {
                "ytd": {
                    "direct_labor": 1,
                    "production_payroll": 1,
                    "admin_payroll": 1,
                    "payroll_processing_fees": 1,
                    "total_labor_ytd26": 3,
                    "total_labor_ytd25": 3,
                }
            },
            "top_customers": [],
            "total_sales_cust": 0,
            "top_items": [],
            "cash_flow": {
                "net_cfo": 0,
                "net_cfi": 0,
                "net_cff": 0,
                "net_change_cash": 0,
            },
        }

        metrics = build_report_metrics(data)

        self.assertIsNone(metrics["monthly_revenue_change_pct"])
        self.assertIsNone(metrics["ytd_gross_margin"])
        self.assertIsNone(metrics["current_ratio"])
        self.assertIsNone(metrics["debt_equity_ratio"])


if __name__ == "__main__":
    unittest.main()
