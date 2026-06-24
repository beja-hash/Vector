import re
from datetime import date, datetime

from app.services.company_providers.base import CompanyCandidate
from app.services.company_providers.rusprofile.schemas import (
    RusprofileParsedCompany,
    RusprofileRawCompanySnapshot,
)


def normalize_money(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = value.lower().replace("\xa0", " ").replace(",", ".")
    multiplier = 1
    if "млрд" in text:
        multiplier = 1_000_000_000
    elif "млн" in text:
        multiplier = 1_000_000
    elif "тыс" in text:
        multiplier = 1_000
    match = re.search(r"(\d+(?:[\s.]\d+)*)", text)
    if not match:
        return None
    numeric_text = match.group(1).replace(" ", "")
    try:
        return int(float(numeric_text) * multiplier)
    except ValueError:
        return None


def normalize_int(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    digits = re.sub(r"\D+", "", value)
    return int(digits) if digits else None


def normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    formats = ("%d.%m.%Y", "%Y-%m-%d", "%d.%m.%y")
    for date_format in formats:
        try:
            return datetime.strptime(text, date_format).date().isoformat()
        except ValueError:
            continue
    match = re.search(r"(\d{2}\.\d{2}\.\d{4})", text)
    if match:
        return normalize_date(match.group(1))
    return None


def normalize_status(value: str | None) -> str | None:
    if not value:
        return None
    text = value.lower()
    if "банкрот" in text:
        return "bankruptcy"
    if "реорганиза" in text:
        return "reorganization"
    if "ликвидац" in text and "процесс" in text:
        return "liquidation"
    if "ликвид" in text:
        return "liquidated"
    if "действ" in text:
        return "active"
    return None


def extract_inn(text: str | None) -> str | None:
    return _extract_labeled_digits(text, "ИНН", (10, 12))


def extract_ogrn(text: str | None) -> str | None:
    return _extract_labeled_digits(text, "ОГРН", (13, 15))


def extract_region_from_address(address: str | None) -> str | None:
    if not address:
        return None
    known_regions = [
        "Москва",
        "Санкт-Петербург",
        "Московская область",
        "Ленинградская область",
        "Краснодарский край",
        "Республика Татарстан",
    ]
    for region in known_regions:
        if region.lower() in address.lower():
            return region
    match = re.search(r"(?:область|край|республика)\s+[А-ЯЁа-яё -]+", address)
    return match.group(0).strip() if match else None


def calculate_company_age(registration_date: str | None) -> int | None:
    if not registration_date:
        return None
    try:
        registered = date.fromisoformat(registration_date)
    except ValueError:
        return None
    today = date.today()
    return today.year - registered.year - ((today.month, today.day) < (registered.month, registered.day))


class RusprofileNormalizer:
    def normalize(self, raw: RusprofileRawCompanySnapshot) -> RusprofileParsedCompany:
        payload = raw.raw_payload or {}
        fields = payload.get("fields") or {}
        listing = payload.get("listing") or {}
        page_text = raw.raw_page_text or ""

        company_name = _first_non_empty(fields.get("company_name"), raw.raw_company_name, listing.get("company_name"), "Без названия")
        full_company_name = _first_non_empty(fields.get("full_company_name"), fields.get("company_name"), raw.raw_company_name)
        inn = _only_digits(_first_non_empty(fields.get("inn"), raw.raw_inn, listing.get("inn"), extract_inn(page_text)))
        ogrn = _only_digits(_first_non_empty(fields.get("ogrn"), raw.raw_ogrn, listing.get("ogrn"), extract_ogrn(page_text)))
        registration_date = normalize_date(_first_non_empty(fields.get("registration_date"), listing.get("registration_date_raw")))
        address = _first_non_empty(fields.get("address"), listing.get("address_raw"))
        website = _first_non_empty(fields.get("website"))
        phone = _first_non_empty(fields.get("phone"))
        email = _first_non_empty(fields.get("email"))

        candidate = CompanyCandidate(
            company_name=company_name,
            full_company_name=full_company_name,
            inn=inn,
            kpp=_only_digits(fields.get("kpp")),
            ogrn=ogrn,
            status=normalize_status(_first_non_empty(fields.get("status"), listing.get("status_label"))),
            region=_first_non_empty(fields.get("region"), extract_region_from_address(address), listing.get("region")),
            city=_first_non_empty(fields.get("city"), _extract_city(address)),
            address=address,
            okved_main=_first_non_empty(fields.get("okved_main")),
            okved_description=_first_non_empty(fields.get("okved_description"), listing.get("activity_description")),
            revenue=normalize_money(_first_non_empty(fields.get("revenue"), listing.get("revenue_raw"))),
            revenue_raw=_first_non_empty(fields.get("revenue"), listing.get("revenue_raw")),
            employees_count=normalize_int(fields.get("employees_count")),
            registration_date=registration_date,
            company_age=calculate_company_age(registration_date),
            website=website,
            has_website=bool(website),
            phone=phone,
            email=email,
            vacancies_total=0,
            sales_vacancies=0,
            marketing_vacancies=0,
            business_type="B2B",
            source_name="rusprofile",
            source_url=raw.source_url,
            summary_text=raw.raw_summary_text,
            comment=raw.raw_summary_text,
        )
        return RusprofileParsedCompany(candidate=candidate)


def _extract_labeled_digits(text: str | None, label: str, lengths: tuple[int, int]) -> str | None:
    if not text:
        return None
    match = re.search(rf"{label}\D*(\d{{{lengths[0]},{lengths[1]}}})", text, re.IGNORECASE)
    return match.group(1) if match else None


def _only_digits(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D+", "", value)
    return digits or None


def _first_non_empty(*values):
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _extract_city(address: str | None) -> str | None:
    if not address:
        return None
    for pattern in (r"город\s+([А-ЯЁа-яё -]+)", r"г\.\s*([А-ЯЁа-яё -]+)"):
        match = re.search(pattern, address)
        if match:
            return match.group(1).split(",")[0].strip()
    if "Москва" in address:
        return "Москва"
    if "Санкт-Петербург" in address:
        return "Санкт-Петербург"
    return None
