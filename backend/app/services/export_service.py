import csv
from io import StringIO

from app.models.company_result import CompanyResult


CSV_COLUMNS = [
    "company_name",
    "full_company_name",
    "inn",
    "kpp",
    "ogrn",
    "status",
    "region",
    "city",
    "address",
    "okved_main",
    "okved_description",
    "revenue",
    "revenue_raw",
    "employees_count",
    "registration_date",
    "company_age",
    "website",
    "phone",
    "email",
    "summary_text",
    "vacancies_total",
    "sales_vacancies",
    "marketing_vacancies",
    "business_type",
    "source_name",
    "source_url",
    "icp_score",
    "icp_is_match",
    "icp_confidence",
    "icp_fit_reason",
    "icp_mismatch_reason",
    "icp_matched_criteria",
    "icp_failed_criteria",
    "icp_recommended_action",
    "llm_model",
    "llm_scored_at",
    "comment",
]


def build_companies_csv(results: list[CompanyResult]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()

    for result in results:
        writer.writerow({column: getattr(result, column) for column in CSV_COLUMNS})

    return output.getvalue()
