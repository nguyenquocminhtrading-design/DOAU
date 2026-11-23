import argparse
import json
import sys

from gemini_page_analysis import (
    GeminiApiError,
    GeminiConfigurationError,
    GeminiRestClient,
    GeminiResponseError,
    SYNTHETIC_PAGES,
    analyze_synthetic_page,
    build_prompt,
    get_api_key,
)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Preview or send one synthetic report-page prompt to Gemini. "
            "This tool never reads report JSON or workbook data."
        )
    )
    parser.add_argument("--page", required=True, choices=sorted(SYNTHETIC_PAGES))
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send this page's fixed synthetic fixture to Gemini (uses GEMINI_API_KEY).",
    )
    args = parser.parse_args(argv)

    if not args.send:
        print(build_prompt(args.page))
        return 0

    try:
        client = GeminiRestClient(get_api_key())
        result = analyze_synthetic_page(args.page, client)
    except (
        GeminiApiError,
        GeminiConfigurationError,
        GeminiResponseError,
        ValueError,
    ) as error:
        print(f"Gemini demo failed: {error}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
