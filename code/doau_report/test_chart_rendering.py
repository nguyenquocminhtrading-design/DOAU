import re
import unittest

from chart_rendering import svg_line_chart, svg_pie_chart, svg_product_bars


class ChartRenderingTests(unittest.TestCase):
    def test_line_chart_is_enlarged_and_keeps_each_point_value_label(self):
        svg = svg_line_chart(
            [
                {"month": "Sep 2026", "revenue": 900000},
                {"month": "Oct 2026", "revenue": 1000000},
            ],
            "revenue",
        )

        self.assertIn('viewBox="0 0 760 270"', svg)
        self.assertEqual(svg.count('class="data-label"'), 2)
        self.assertIn("$0.90M", svg)
        self.assertIn("$1.00M", svg)

    def test_pie_chart_labels_large_slices_and_keeps_small_shares_in_legend(self):
        svg = svg_pie_chart(
            [
                {"name": "Large customer", "value": 94},
                {"name": "Small customer", "value": 5},
                {"name": "Tiny customer", "value": 1},
            ],
            "Synthetic customer share",
        )

        self.assertIn('viewBox="0 0 480 280"', svg)
        self.assertEqual(svg.count('class="data-label"'), 1)
        self.assertIn(">94.0%</text>", svg)
        self.assertIn(">5.0%</tspan>", svg)
        self.assertIn(">1.0%</tspan>", svg)

    def test_product_values_are_inside_wide_bars_and_outside_narrow_bars(self):
        svg = svg_product_bars(
            [
                {"name": "Wide item", "sales": 1000000},
                {"name": "Narrow item", "sales": 100},
            ],
            "sales",
        )

        self.assertIn('class="data-label data-label--inside"', svg)
        self.assertIn('class="data-label data-label--outside"', svg)
        self.assertIn("Sales by product", svg)

    def test_diverging_chart_preserves_negative_values_and_sign(self):
        svg = svg_product_bars(
            [
                {"name": "Large loss", "gp": -1000000},
                {"name": "Small loss", "gp": -100},
                {"name": "Profit", "gp": 500000},
            ],
            "gp",
            diverging=True,
        )

        self.assertIn("Gross profit by product", svg)
        self.assertIn("($1.0M)", svg)
        self.assertIn("($0k)", svg)
        self.assertIn('stroke="#64748b"', svg)
        self.assertGreaterEqual(
            len(re.findall(r'class="data-label data-label--(?:inside|outside)"', svg)),
            3,
        )


if __name__ == "__main__":
    unittest.main()
