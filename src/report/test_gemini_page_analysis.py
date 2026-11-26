import json
import unittest
from unittest.mock import patch

from company_context import build_public_company_context
from gemini_page_analysis import (
    GeminiConfigurationError,
    GeminiRestClient,
    GeminiResponseError,
    SYNTHETIC_PAGES,
    analyze_synthetic_page,
    build_prompt,
    get_api_key,
    parse_analysis,
)


class _FakeResponse:
    def __init__(self, body):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(self._body).encode("utf-8")


class GeminiPageAnalysisTests(unittest.TestCase):
    def test_company_context_distinguishes_company_group_brands_and_report_code(self):
        context = build_public_company_context()

        self.assertEqual(
            context["identity"]["profile_company_name"],
            "Dan On Foods Corporation",
        )
        self.assertEqual(context["identity"]["abbreviation"], "DOF")
        self.assertEqual(context["identity"]["group_name"], "DAN-D FOODS Group")
        self.assertIn("DOAU is the report code", context["identity"]["report_code_note"])
        self.assertEqual(
            context["identity"]["brands"],
            ["Dan-D-Pak", "Dan-D-Bulk", "Andi", "Dan-D-Organic"],
        )

    def test_every_report_page_has_a_fixed_synthetic_prompt(self):
        self.assertEqual(
            set(SYNTHETIC_PAGES),
            {
                "executive-summary",
                "sales",
                "financial-performance",
                "commercial-analysis",
                "inventory",
                "working-capital",
                "capex-cash-flow",
                "payroll",
            },
        )
        for page_id in SYNTHETIC_PAGES:
            prompt = build_prompt(page_id)
            self.assertIn("fabricated synthetic test data", prompt)
            self.assertIn("synthetic_page_metrics", prompt)
            self.assertIn("Dan On Foods Corporation", prompt)
            self.assertIn("DOAU", prompt)

    def test_prompt_rejects_pages_outside_the_fixed_fixture_catalog(self):
        with self.assertRaises(ValueError):
            build_prompt("real-doau-data")

    def test_missing_api_key_is_reported_without_a_fallback(self):
        with self.assertRaises(GeminiConfigurationError):
            get_api_key({})

    def test_gemini_request_keeps_key_in_header_and_sends_only_prompt(self):
        response_body = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "page_id": "sales",
                                        "summary": "Synthetic sales increased.",
                                        "observations": ["Revenue is synthetic."],
                                        "management_questions": ["What changed?"],
                                        "limitations": ["All values are fabricated."],
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }
        client = GeminiRestClient("test-secret")
        with patch(
            "gemini_page_analysis.urlopen",
            return_value=_FakeResponse(response_body),
        ) as open_url:
            result = analyze_synthetic_page("sales", client)

        request = open_url.call_args.args[0]
        request_headers = dict(request.header_items())
        request_body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(result["page_id"], "sales")
        self.assertEqual(request_headers["X-goog-api-key"], "test-secret")
        self.assertNotIn("test-secret", request.full_url)
        self.assertNotIn("test-secret", request_body["contents"][0]["parts"][0]["text"])
        self.assertIn("Synthetic Customer A", request_body["contents"][0]["parts"][0]["text"])

    def test_response_schema_and_page_id_are_validated(self):
        valid = {
            "page_id": "inventory",
            "summary": "Synthetic inventory is mostly raw materials.",
            "observations": ["Raw materials are 50%."],
            "management_questions": ["Is that mix expected?"],
            "limitations": ["Values are synthetic."],
        }
        self.assertEqual(
            parse_analysis("inventory", json.dumps(valid)),
            valid,
        )
        with self.assertRaises(GeminiResponseError):
            parse_analysis("sales", json.dumps(valid))
        with self.assertRaises(GeminiResponseError):
            parse_analysis("inventory", '{"page_id": "inventory"}')


if __name__ == "__main__":
    unittest.main()
