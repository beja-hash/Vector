from app.services.company_scoring.schemas import CompanyForScoring, IcpProfile

SYSTEM_PROMPT = (
    "Ты B2B ICP scoring assistant. Твоя задача — определить, подходит ли компания под идеальный профиль клиента. "
    "Отвечай только валидным JSON. Не добавляй markdown. Не выдумывай факты. "
    "Если данных недостаточно, снижай confidence и ставь manual_review."
)

RULES_TEXT = """Правила:
1. Если компания явно не подходит по деятельности, ставь is_match=false.
2. Если компания подходит по масштабу, региону и деятельности, ставь is_match=true.
3. Если данных мало, но компания может подходить, ставь recommended_action="manual_review".
4. Не штрафуй компанию за пустые фильтры ICP. Пустой фильтр значит "не важно".
5. Верни только JSON по схеме:
{
  "is_match": true/false,
  "score": 0-100,
  "confidence": "low" | "medium" | "high",
  "fit_reason": "...",
  "mismatch_reason": "...",
  "matched_criteria": [],
  "failed_criteria": [],
  "recommended_action": "add_to_results" | "manual_review" | "skip"
}"""


def build_user_prompt(icp: IcpProfile, company: CompanyForScoring, max_input_chars: int) -> str:
    icp_text = _truncate_text(build_icp_text(icp), max(1200, max_input_chars // 2))
    overhead = len("ИДЕАЛЬНЫЙ ПРОФИЛЬ КЛИЕНТА:\n\nКОМПАНИЯ:\n\n\n") + len(RULES_TEXT)
    company_budget = max(0, max_input_chars - len(icp_text) - overhead)
    company_text = build_company_text(company, max_chars=company_budget)
    return f"ИДЕАЛЬНЫЙ ПРОФИЛЬ КЛИЕНТА:\n{icp_text}\n\nКОМПАНИЯ:\n{company_text}\n\n{RULES_TEXT}"


def build_icp_text(icp: IcpProfile) -> str:
    lines = [
        ("Проект", icp.project_name),
        ("Что продает проект", icp.offer),
        ("Средний чек", _format_money(icp.average_check)),
        ("Тип продаж", icp.business_type),
        ("Отрасль", icp.industry),
        ("ОКВЭД", icp.okved_code),
        ("Регион", icp.region),
        ("Город", icp.city),
        ("Выручка от", _format_money(icp.revenue_min)),
        ("Выручка до", _format_money(icp.revenue_max)),
        ("Сотрудников от", icp.employees_min),
        ("Сотрудников до", icp.employees_max),
        ("Возраст компании от", _format_years(icp.company_age_min)),
        ("Сайт важен", _format_bool(icp.must_have_website)),
        ("Вакансии важны", _format_bool(icp.must_have_vacancies)),
        ("Хорошие сигналы", _format_list(icp.good_signals)),
        ("Плохие сигналы", _format_list(icp.bad_signals)),
        ("Исключать", _format_list(icp.exclude_rules)),
    ]
    return "\n".join(f"- {label}: {_value_or_not_set(value)}" for label, value in lines)


def build_company_text(company: CompanyForScoring, *, max_chars: int) -> str:
    structured_lines = [
        ("Название", company.company_name),
        ("Полное название", company.full_company_name),
        ("ИНН", company.inn),
        ("ОГРН", company.ogrn),
        ("Регион", company.region),
        ("Город", company.city),
        ("Адрес", company.address),
        ("ОКВЭД", company.okved_main),
        ("Описание ОКВЭД", company.okved_description),
        ("Выручка", _format_money(company.revenue) or company.revenue_raw),
        ("Выручка raw", company.revenue_raw),
        ("Сотрудники", company.employees_count),
        ("Сайт", company.website),
        ("Тип бизнеса", company.business_type),
        ("Описание деятельности", company.activity_description),
    ]
    structured = "\n".join(f"- {label}: {_value_or_not_set(value)}" for label, value in structured_lines)
    summary_label = "\n- Главное о компании за 1 минуту: "
    summary = (company.summary_text or "").strip()
    if not summary:
        return f"{structured}{summary_label}не задано"

    remaining = max_chars - len(structured) - len(summary_label)
    if remaining <= 0:
        return f"{structured}{summary_label}не задано"
    return f"{structured}{summary_label}{_truncate_text(summary, remaining)}"


def _format_money(value: int | None) -> str | None:
    if value is None:
        return None
    return f"{value:,} руб.".replace(",", " ")


def _format_years(value: int | None) -> str | None:
    if value is None:
        return None
    return f"{value} лет"


def _format_bool(value: bool | None) -> str | None:
    if value is None:
        return None
    return "да" if value else "нет"


def _format_list(values: list[str]) -> str | None:
    cleaned = [value.strip() for value in values if value and value.strip()]
    if not cleaned:
        return None
    return "; ".join(cleaned)


def _value_or_not_set(value) -> str:
    if value is None or value == "":
        return "не задано"
    return str(value)


def _truncate_text(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    if max_chars <= 20:
        return value[:max_chars]
    trimmed = value[: max_chars - 15].rsplit(" ", 1)[0].strip()
    return f"{trimmed}... [truncated]"
