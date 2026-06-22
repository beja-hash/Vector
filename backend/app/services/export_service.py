import csv
from io import StringIO

from app.models.company_result import CompanyResult


CSV_COLUMNS = [
    "company_name",
    "inn",
    "ogrn",
    "region",
    "city",
    "okved_main",
    "okved_description",
    "revenue",
    "employees_count",
    "company_age",
    "website",
    "vacancies_total",
    "sales_vacancies",
    "marketing_vacancies",
    "business_type",
    "source_name",
    "source_url",
    "comment",
]


def build_companies_csv(results: list[CompanyResult]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()

    for result in results:
        writer.writerow({column: getattr(result, column) for column in CSV_COLUMNS})

    return output.getvalue()
