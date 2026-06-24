EMPTY_FILTER_LABELS = {"", "не выбрано", "null", "undefined"}


def is_empty_filter_value(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in EMPTY_FILTER_LABELS
    return False


def normalize_filter_value(value: object) -> str | None:
    if is_empty_filter_value(value):
        return None
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def should_apply_okved(okved_code: object) -> bool:
    return not is_empty_filter_value(okved_code)


def should_apply_industry(industry: object) -> bool:
    return not is_empty_filter_value(industry)
