import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import asdict

from app.services.company_providers.rusprofile.antibot import is_antibot_text, wait_for_manual_antibot_clearance
from app.services.company_providers.rusprofile.errors import CardCollectionError
from app.services.company_providers.rusprofile.human_like import HumanLikePlaywrightController
from app.services.company_providers.rusprofile.schemas import RusprofileRawCompanySnapshot, RusprofileSearchItem

logger = logging.getLogger(__name__)


class RusprofileCardCollector:
    def __init__(self, human: HumanLikePlaywrightController) -> None:
        self.human = human

    async def collect(
        self,
        page,
        source_url: str,
        listing_item: RusprofileSearchItem | None = None,
        *,
        allow_manual_clearance: bool = False,
        screenshot: Callable[[str], Awaitable[None]] | None = None,
    ) -> RusprofileRawCompanySnapshot:
        logger.info("[Rusprofile] opening card: %s", source_url)
        await self.human.random_delay()
        await page.goto(source_url, wait_until="domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception as exc:
            logger.info("[Rusprofile] card networkidle skipped: %s", exc)
        await self.human.smooth_scroll(page, steps=2)

        raw_page_text = await page.locator("body").inner_text(timeout=10000)
        if is_antibot_text(raw_page_text):
            logger.warning("[Rusprofile] antibot page detected: %s", source_url)
            cleared = await wait_for_manual_antibot_clearance(
                page,
                allow_manual_clearance=allow_manual_clearance,
                screenshot=screenshot,
                context=source_url,
            )
            if not cleared:
                raise CardCollectionError("captcha_required")
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except Exception as exc:
                logger.info("[Rusprofile] card networkidle after captcha skipped: %s", exc)
            raw_page_text = await page.locator("body").inner_text(timeout=10000)

        fields = await self.extract_basic_fields(page)
        summary_text = await self.extract_summary_text(page)
        if is_antibot_text(summary_text):
            logger.warning("[Rusprofile] antibot summary detected: %s", source_url)
            raise CardCollectionError("captcha_required")

        listing_payload = asdict(listing_item) if listing_item else {}
        errors: list[str] = []
        if summary_text:
            logger.info("[Rusprofile] extracted summary")
        else:
            errors.append("summary_not_found")
            logger.warning("[Rusprofile] summary_not_found: %s", source_url)

        return RusprofileRawCompanySnapshot(
            source_name="rusprofile",
            source_url=source_url,
            raw_company_name=fields.get("company_name") or listing_payload.get("company_name"),
            raw_inn=fields.get("inn") or listing_payload.get("inn"),
            raw_ogrn=fields.get("ogrn") or listing_payload.get("ogrn"),
            raw_summary_text=summary_text,
            raw_page_text=raw_page_text,
            raw_payload={"fields": fields, "listing": listing_payload, "errors": errors},
            status="collected",
        )

    async def extract_summary_text(self, page) -> str | None:
        block = page.locator(".company-description, .company-description__wrapper").first
        if not await block.count():
            heading = page.get_by_text("Главное о компании за 1 минуту", exact=False).first
            if await heading.count():
                try:
                    await self.human.scroll_to_locator(page, heading)
                except Exception:
                    pass
                block = page.locator("section, div, article").filter(has_text="Главное о компании за 1 минуту").first
        if not await block.count():
            logger.warning("[Rusprofile] summary block not found")
            return None

        try:
            await self.human.scroll_to_locator(page, block)
        except Exception:
            pass

        show_button = block.locator("button.company-description__button").first
        if not await show_button.count():
            show_button = block.get_by_text(re.compile(r"Показать|Развернуть|Еще|Ещё", re.IGNORECASE)).first
        try:
            if await show_button.count() and await show_button.is_visible():
                logger.info("[Rusprofile] expanding company summary")
                await self.human.human_click(page, show_button, "Показать summary")
                await page.wait_for_timeout(300)
        except Exception:
            pass

        text_locator = block.locator(".company-description__text").first
        if await text_locator.count():
            text = await text_locator.inner_text(timeout=5000)
        else:
            text = await block.inner_text(timeout=5000)
        cleaned = (_clean_text(text) or "").replace("Главное о компании за 1 минуту", "", 1).strip()
        return cleaned or None

    async def extract_basic_fields(self, page) -> dict:
        body_text = await page.locator("body").inner_text(timeout=10000)
        title = await _text_or_none(page.locator("h1").first)
        fields = {
            "company_name": title,
            "full_company_name": _extract_after_label(body_text, "Полное наименование"),
            "status": _extract_status(body_text),
            "inn": _extract_labeled_digits(body_text, "ИНН", (10, 12)),
            "kpp": _extract_labeled_digits(body_text, "КПП", (9, 9)),
            "ogrn": _extract_labeled_digits(body_text, "ОГРН", (13, 15)),
            "registration_date": _extract_registration_date(body_text),
            "address": _extract_after_label(body_text, "Юридический адрес") or _extract_after_label(body_text, "Адрес"),
            "okved_main": _extract_okved_code(body_text),
            "okved_description": _extract_okved_description(body_text),
            "employees_count": _extract_after_label(body_text, "Среднесписочная численность"),
            "website": _extract_url(body_text),
            "phone": _extract_phone(body_text),
            "email": _extract_email(body_text),
            "revenue": _extract_revenue(body_text),
        }
        return {key: value for key, value in fields.items() if value}


async def _text_or_none(locator) -> str | None:
    try:
        text = await locator.inner_text(timeout=3000)
    except Exception:
        return None
    return _clean_text(text) or None


def _clean_text(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"\s+", " ", value).strip()


def _extract_after_label(text: str, label: str) -> str | None:
    patterns = [
        rf"{label}\s*[:\n]\s*([^\n]+)",
        rf"{label}\s+([^\n]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return _clean_text(match.group(1))
    return None


def _extract_labeled_digits(text: str, label: str, lengths: tuple[int, int]) -> str | None:
    match = re.search(rf"{label}\D*(\d{{{lengths[0]},{lengths[1]}}})", text, re.IGNORECASE)
    return match.group(1) if match else None


def _extract_status(text: str) -> str | None:
    for value in ("Действующая организация", "В процессе реорганизации", "В процессе ликвидации", "В процессе банкротства", "Ликвидированная"):
        if value.lower() in text.lower():
            return value
    return None


def _extract_registration_date(text: str) -> str | None:
    match = re.search(r"(?:Дата регистрации|Зарегистрирована)\D*(\d{2}\.\d{2}\.\d{4})", text)
    return match.group(1) if match else None


def _extract_okved_code(text: str) -> str | None:
    match = re.search(r"(?:Основной вид деятельности|ОКВЭД)[\s\S]{0,120}?(\d{2}\.\d{2}(?:\.\d+)?)", text)
    return match.group(1) if match else None


def _extract_okved_description(text: str) -> str | None:
    match = re.search(r"(?:Основной вид деятельности|ОКВЭД)[\s\S]{0,180}?\d{2}\.\d{2}(?:\.\d+)?\s*([^\n]+)", text)
    if not match:
        return None
    description = _clean_text(match.group(1))
    return description if description and re.search(r"[A-Za-zА-Яа-яЁё0-9]", description) else None


def _extract_url(text: str) -> str | None:
    match = re.search(r"https?://[^\s,;]+|www\.[^\s,;]+", text)
    return match.group(0) if match else None


def _extract_phone(text: str) -> str | None:
    match = re.search(r"(?:\+7|8)\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}", text)
    return match.group(0) if match else None


def _extract_email(text: str) -> str | None:
    match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    return match.group(0) if match else None


def _extract_revenue(text: str) -> str | None:
    match = re.search(r"Выручка[^\n]*(\d[\d\s,.]*(?:тыс|млн|млрд)?\s*(?:руб|₽|рублей)?)", text, re.IGNORECASE)
    return _clean_text(match.group(1)) if match else None
