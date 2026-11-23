import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from company_context import build_public_company_context


MODEL_NAME = "gemini-2.5-flash"
API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL_NAME}:generateContent"
)

SYNTHETIC_PAGES = {
    "executive-summary": {
        "title": "Executive Summary",
        "metrics": {
            "period": "Synthetic Month Z",
            "revenue": 1000000,
            "prior_period_revenue": 940000,
            "gross_profit": 270000,
            "gross_margin_pct": 27.0,
            "operating_cash_flow": 80000,
        },
    },
    "sales": {
        "title": "Sales",
        "metrics": {
            "period": "Synthetic Month Z",
            "customer_sales": [
                {"name": "Synthetic Customer A", "sales": 500000, "share_pct": 50.0},
                {"name": "Synthetic Customer B", "sales": 300000, "share_pct": 30.0},
                {"name": "Synthetic Customer C", "sales": 200000, "share_pct": 20.0},
            ],
        },
    },
    "financial-performance": {
        "title": "Financial Performance",
        "metrics": {
            "period": "Synthetic Month Z",
            "revenue": 1000000,
            "cost_of_goods_sold": 730000,
            "gross_profit": 270000,
            "operating_expenses": 210000,
            "net_income": 60000,
        },
    },
    "commercial-analysis": {
        "title": "Commercial Analysis",
        "metrics": {
            "period": "Synthetic Month Z",
            "products": [
                {"name": "Synthetic Product A", "sales": 450000, "gross_profit": 90000},
                {"name": "Synthetic Product B", "sales": 350000, "gross_profit": 105000},
                {"name": "Synthetic Product C", "sales": 200000, "gross_profit": 30000},
            ],
        },
    },
    "inventory": {
        "title": "Inventory",
        "metrics": {
            "period": "Synthetic Month Z",
            "inventory_categories": [
                {"name": "Synthetic Raw Materials", "value": 400000, "share_pct": 50.0},
                {"name": "Synthetic Work in Progress", "value": 120000, "share_pct": 15.0},
                {"name": "Synthetic Finished Goods", "value": 280000, "share_pct": 35.0},
            ],
            "reconciliation_status": "synthetic example only",
        },
    },
    "working-capital": {
        "title": "Balance Sheet and Working Capital",
        "metrics": {
            "period": "Synthetic Month Z",
            "accounts_receivable": 240000,
            "accounts_payable": 180000,
            "current_assets": 900000,
            "current_liabilities": 600000,
            "ar_aging_pct": {"current": 70.0, "over_90_days": 8.0},
        },
    },
    "capex-cash-flow": {
        "title": "CapEx and Cash Flow",
        "metrics": {
            "period": "Synthetic YTD",
            "operating_cash_flow": 80000,
            "investing_cash_flow": -30000,
            "financing_cash_flow": 10000,
            "net_change_in_cash": 60000,
            "capital_expenditure": 25000,
        },
    },
    "payroll": {
        "title": "Payroll Cost Analysis",
        "metrics": {
            "period": "Synthetic YTD",
            "payroll_mix_pct": {
                "direct_labor": 45.0,
                "production_payroll": 30.0,
                "administration_payroll": 23.0,
                "processing_fees": 2.0,
            },
            "headcount": None,
        },
    },
}

_REQUIRED_RESULT_KEYS = {
    "page_id",
    "summary",
    "observations",
    "management_questions",
    "limitations",
}


class GeminiConfigurationError(Exception):
    pass


class GeminiApiError(Exception):
    pass


class GeminiResponseError(Exception):
    pass


def get_api_key(environment=None):
    values = os.environ if environment is None else environment
    api_key = values.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise GeminiConfigurationError(
            "GEMINI_API_KEY is not set. Add it to the process environment "
            "before running the synthetic Gemini demo."
        )
    return api_key


def build_prompt(page_id):
    if page_id not in SYNTHETIC_PAGES:
        raise ValueError(f"Unknown report page: {page_id}")

    page = SYNTHETIC_PAGES[page_id]
    request_data = {
        "page_id": page_id,
        "page_title": page["title"],
        "data_classification": (
            "All page metrics below are fabricated synthetic test data. "
            "They are unrelated to Dan On Foods, DOF, DOAU, and any real customer."
        ),
        "company_background": build_public_company_context(),
        "synthetic_page_metrics": page["metrics"],
    }
    return (
        "You are a management-report analyst. Analyze only the supplied page "
        "metrics and use the company background only as general context. "
        "The metrics are synthetic and must never be described as real company "
        "performance. Do not invent causes, targets, company facts, or missing "
        "data. Tie each observation to a supplied metric. Preserve the "
        "distinction between Dan On Foods Corporation (DOF), DAN-D FOODS "
        "Group, product brands, and the DOAU report code. Treat preliminary "
        "profile information as qualified context, not verified internal fact. "
        "Return only a JSON object with exactly these keys: page_id (string), "
        "summary (string), observations (array of strings), "
        "management_questions (array of strings), limitations (array of strings). "
        "Do not include Markdown or additional keys.\n\n"
        "Input:\n"
        + json.dumps(request_data, ensure_ascii=False, indent=2)
    )


def validate_analysis(page_id, result):
    if not isinstance(result, dict) or set(result) != _REQUIRED_RESULT_KEYS:
        raise GeminiResponseError(
            "Gemini response must be a JSON object with the required result keys."
        )
    if result["page_id"] != page_id:
        raise GeminiResponseError("Gemini response page_id does not match the request.")
    if not isinstance(result["summary"], str) or not result["summary"].strip():
        raise GeminiResponseError("Gemini response summary must be a non-empty string.")
    for key in ("observations", "management_questions", "limitations"):
        values = result[key]
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value.strip() for value in values
        ):
            raise GeminiResponseError(
                f"Gemini response {key} must be an array of non-empty strings."
            )
    return result


def parse_analysis(page_id, response_text):
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as error:
        raise GeminiResponseError("Gemini response was not valid JSON.") from error
    return validate_analysis(page_id, result)


class GeminiRestClient:
    def __init__(self, api_key, timeout=30):
        if not api_key:
            raise GeminiConfigurationError("A Gemini API key is required.")
        self._api_key = api_key
        self._timeout = timeout

    def generate_content(self, prompt):
        request_body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        request = Request(
            API_URL,
            data=json.dumps(request_body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise GeminiApiError(
                f"Gemini API returned HTTP {error.code}."
            ) from None
        except URLError:
            raise GeminiApiError("Could not connect to the Gemini API.") from None
        except TimeoutError:
            raise GeminiApiError("The Gemini API request timed out.") from None
        except json.JSONDecodeError as error:
            raise GeminiApiError("Gemini API returned invalid JSON.") from error

        candidates = body.get("candidates")
        if not candidates or not isinstance(candidates[0], dict):
            raise GeminiResponseError("Gemini API returned no candidate response.")
        content = candidates[0].get("content", {})
        parts = content.get("parts", []) if isinstance(content, dict) else []
        text_parts = [
            part["text"]
            for part in parts
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ]
        if not text_parts:
            raise GeminiResponseError("Gemini API response contained no text.")
        return "".join(text_parts)


def analyze_synthetic_page(page_id, client):
    prompt = build_prompt(page_id)
    return parse_analysis(page_id, client.generate_content(prompt))
