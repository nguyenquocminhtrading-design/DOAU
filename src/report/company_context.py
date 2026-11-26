import os


PROFILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "assets",
    "Dan_On_Foods_Company_Industry_Profile.md",
)


def build_public_company_context():
    if not os.path.isfile(PROFILE_PATH):
        raise FileNotFoundError(
            f"Company profile was not found: {PROFILE_PATH}"
        )

    return {
        "source": "assets/Dan_On_Foods_Company_Industry_Profile.md",
        "source_sections": ["1", "2", "3", "4", "5", "16"],
        "source_status": (
            "Preliminary research profile based on public sources; "
            "not an audited or authoritative legal record."
        ),
        "identity": {
            "profile_company_name": "Dan On Foods Corporation",
            "profile_vietnamese_name": "Công ty Cổ phần Thực phẩm Dân Ôn",
            "short_name": "Dan On Foods",
            "abbreviation": "DOF",
            "group_name": "DAN-D FOODS Group",
            "group_relationship": (
                "The profile describes DAN-D FOODS Group as a separate group "
                "identity related to the company, not as an alias."
            ),
            "brands": [
                "Dan-D-Pak",
                "Dan-D-Bulk",
                "Andi",
                "Dan-D-Organic",
            ],
            "report_code_note": (
                "DOAU is the report code/context; the profile does not "
                "establish DOAU as an alias or legal name for DOF."
            ),
        },
        "industry_context": (
            "The profile describes food processing and production, with "
            "products including nuts, dried fruits, cereals or granola, "
            "snacks, and packaged foods."
        ),
        "business_model_context": (
            "The profile uses procurement, processing, packaging, and "
            "distribution or export as a high-level value-chain framework; "
            "actual company processes require confirmation."
        ),
        "history_context": (
            "The profile reports that the founder's DAN-D FOODS activity "
            "began in Canada in 1989 and that Dan On Foods was established "
            "in Vietnam in 1999. Attribute these dates to the profile; do "
            "not present them as audited facts."
        ),
        "analysis_caveats": [
            "Do not treat DOAU as interchangeable with DOF without confirmation.",
            "Do not treat DAN-D FOODS Group or product brands as aliases of DOF.",
            "Organizational structure, internal processes, revenue mix, "
            "certifications, and competitive advantages in the profile are "
            "preliminary or require verification.",
            "Use the company context only as background; do not infer "
            "company performance from synthetic test metrics.",
        ],
    }
