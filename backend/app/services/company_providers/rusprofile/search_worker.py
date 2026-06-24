import logging
import re
from pathlib import Path

from app.core.config import settings
from app.services.company_providers.rusprofile.antibot import (
    safe_inner_text,
    wait_for_manual_antibot_clearance,
)
from app.services.company_providers.rusprofile.card_collector import RusprofileCardCollector
from app.services.company_providers.rusprofile.errors import FilterApplyError
from app.services.company_providers.rusprofile.filters import (
    normalize_filter_value,
    should_apply_industry,
    should_apply_okved,
)
from app.services.company_providers.rusprofile.human_like import HumanLikePlaywrightController
from app.services.company_providers.rusprofile.normalizer import RusprofileNormalizer
from app.services.company_providers.rusprofile.schemas import (
    RusprofileRunResult,
    RusprofileSearchFilters,
    RusprofileSearchItem,
)
from app.services.company_providers.rusprofile.selectors import absolute_rusprofile_url, find_fieldset_by_legend

logger = logging.getLogger(__name__)


class RusprofileSearchWorker:
    def __init__(self, human: HumanLikePlaywrightController | None = None) -> None:
        self.human = human or HumanLikePlaywrightController()
        self.card_collector = RusprofileCardCollector(self.human)
        self.normalizer = RusprofileNormalizer()
        self.screenshot_dir = Path("tmp/rusprofile/screenshots")
        if settings.rusprofile_debug_screenshots:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    async def run(self, filters: RusprofileSearchFilters) -> RusprofileRunResult:
        logger.info("[Rusprofile] starting run")
        result = RusprofileRunResult()
        from playwright.async_api import async_playwright

        async with async_playwright() as playwright:
            launch_options = {
                "headless": not filters.visible_browser if filters.visible_browser is not None else settings.rusprofile_headless,
                "slow_mo": settings.rusprofile_slow_mo_ms,
            }
            if settings.rusprofile_browser_channel:
                launch_options["channel"] = settings.rusprofile_browser_channel
            if settings.rusprofile_executable_path:
                launch_options["executable_path"] = settings.rusprofile_executable_path

            browser = await playwright.chromium.launch(**launch_options)
            page = await browser.new_page(viewport={"width": 1440, "height": 1000}, locale="ru-RU")
            try:
                allow_manual_captcha = bool(filters.visible_browser)
                await self.open_rusprofile(page)
                await self._ensure_not_antibot(page, allow_manual_clearance=allow_manual_captcha)
                await self.debug_screenshot(page, "01-opened")
                await self.open_company_selection(page)
                await self._ensure_not_antibot(page, allow_manual_clearance=allow_manual_captcha)
                await self.reset_filters(page)
                await self._ensure_not_antibot(page, allow_manual_clearance=allow_manual_captcha)
                logger.info("[Rusprofile] status filter skipped by design")
                if should_apply_industry(filters.industry):
                    logger.info("[Rusprofile] industry filter ignored in Rusprofile V1: %s", filters.industry)
                else:
                    logger.info("[Rusprofile] industry filter skipped: empty")
                if should_apply_okved(filters.okved_code):
                    okved_code = normalize_filter_value(filters.okved_code)
                    assert okved_code is not None
                    logger.info("[Rusprofile] applying okved filter: %s", okved_code)
                    await self.apply_okved(page, okved_code)
                    await self.debug_screenshot(page, "03-okved-applied")
                else:
                    logger.info("[Rusprofile] okved filter skipped: empty")
                if filters.region:
                    await self.apply_region(page, filters.region)
                    await self.debug_screenshot(page, "04-region-applied")
                await self.apply_revenue(page, filters.revenue_min, filters.revenue_max)
                await self.debug_screenshot(page, "05-revenue-applied")
                await self.apply_employees(page, filters.employees_min, filters.employees_max)
                await self.debug_screenshot(page, "06-results")

                items = await self.collect_until_limit(page, filters.limit)
                result.collected = len(items)
                if not items:
                    result.errors.append("no_results_found")
                    return result
                for item in items:
                    try:
                        raw = await self.card_collector.collect(
                            page,
                            item.source_url,
                            item,
                            allow_manual_clearance=allow_manual_captcha,
                            screenshot=lambda name: self.debug_screenshot(page, name),
                        )
                        await self.debug_screenshot(page, "07-card-opened")
                        parsed = self.normalizer.normalize(raw)
                        result.raw_snapshots.append(raw)
                        result.parsed_companies.append(parsed)
                    except Exception as exc:
                        logger.exception("[Rusprofile] card_open_failed: %s", item.source_url)
                        result.failed += 1
                        result.errors.append(f"card_open_failed: {item.source_url}: {exc}")
                        continue
            except FilterApplyError as exc:
                logger.exception("[Rusprofile] filter_apply_failed")
                result.errors.append(f"filter_apply_failed: {exc}")
                raise
            finally:
                await browser.close()
        return result

    async def open_rusprofile(self, page) -> None:
        logger.info("[Rusprofile] opening homepage")
        await page.goto("https://www.rusprofile.ru/", wait_until="domcontentloaded")
        await self._safe_wait_networkidle(page)
        await self.human.wait_after_action()

    async def open_company_selection(self, page) -> None:
        logger.info("[Rusprofile] opening company selection")
        candidates = [
            page.get_by_text("Подбор компаний", exact=True).first,
            page.get_by_role("link", name=re.compile("Подбор компаний", re.IGNORECASE)).first,
            page.locator("a").filter(has_text="Подбор компаний").first,
        ]
        for locator in candidates:
            try:
                if await locator.count():
                    await self.human.human_click(page, locator, "Подбор компаний")
                    await self._safe_wait_networkidle(page)
                    return
            except Exception:
                continue
        await page.goto("https://www.rusprofile.ru/search-advanced", wait_until="domcontentloaded")
        await self._safe_wait_networkidle(page)

    async def reset_filters(self, page) -> None:
        reset = page.get_by_text(re.compile("Сбросить|Очистить", re.IGNORECASE)).first
        try:
            if await reset.count() and await reset.is_visible():
                await self.human.human_click(page, reset, "Сбросить фильтры")
                await self._safe_wait_networkidle(page)
        except Exception:
            logger.info("[Rusprofile] reset filters unavailable")

    async def apply_okved(self, page, okved_code: str) -> None:
        okved_code = okved_code.strip()
        await self._click_filter_header(page, "Вид деятельности")
        modal = page.locator(".modal-pop-body, [role='dialog']").filter(has_text="Виды деятельности по ОКВЭД").first
        await modal.wait_for(state="visible", timeout=10000)
        input_locator = modal.get_by_placeholder("Название или код").first
        if not await input_locator.count():
            input_locator = modal.locator("input").first
        await self.human.human_fill(page, input_locator, okved_code, "ОКВЭД")
        await self.human.random_delay(1500, 3000)

        try:
            await self._click_checkbox_row_by_text(page, modal, okved_code, okved_code)
        except FilterApplyError as exc:
            parent_code = self._parent_okved_code(okved_code)
            if parent_code:
                logger.warning("[Rusprofile] exact okved checkbox not found, trying parent code: %s", parent_code)
                try:
                    await self._click_checkbox_row_by_text(page, modal, parent_code, parent_code)
                except FilterApplyError as parent_exc:
                    modal_text = await self._safe_inner_text(modal)
                    logger.error("[Rusprofile] okved_not_found: %s; modal text: %s", okved_code, modal_text[:2000])
                    await self.debug_screenshot(page, "03-okved-not-found")
                    raise FilterApplyError(f"okved_not_found: {okved_code}") from parent_exc
            else:
                modal_text = await self._safe_inner_text(modal)
                logger.error("[Rusprofile] okved_not_found: %s; modal text: %s", okved_code, modal_text[:2000])
                await self.debug_screenshot(page, "03-okved-not-found")
                raise FilterApplyError(f"okved_not_found: {okved_code}") from exc

        main_only_text = "Искать только в основных видах деятельности"
        try:
            await self._click_checkbox_row_by_text(page, modal, main_only_text, "Основной ОКВЭД", only_if_unchecked=True)
        except FilterApplyError:
            logger.warning("[Rusprofile] okved_main_only_checkbox_not_found")
        await self._click_modal_done(page, modal)
        await self._wait_filter_update(page)

    async def apply_region(self, page, region: str) -> None:
        logger.info("[Rusprofile] applying region: %s", region)
        await self._click_filter_header(page, "Регион")
        modal = page.locator(".modal-pop-body, [role='dialog']").filter(has_text="Регион").first
        await modal.wait_for(state="visible", timeout=10000)
        input_locator = modal.get_by_placeholder("Округ или регион").first
        if not await input_locator.count():
            input_locator = modal.locator("input").first
        await self.human.human_fill(page, input_locator, region, "Регион")
        try:
            await self._click_checkbox_row_by_text(page, modal, region, region)
        except Exception as exc:
            modal_text = await self._safe_inner_text(modal)
            logger.error("[Rusprofile] region_not_found: %s; modal text: %s", region, modal_text[:2000])
            await self.debug_screenshot(page, "04-region-not-found")
            raise FilterApplyError(f"region_not_found: {region}") from exc
        await self._click_modal_done(page, modal)
        await self._wait_filter_update(page)

    async def apply_revenue(self, page, revenue_min: int | None, revenue_max: int | None) -> None:
        if revenue_min is None and revenue_max is None:
            return
        logger.info("[Rusprofile] applying revenue: %s - %s", revenue_min, revenue_max)
        await self._click_filter_header(page, "Выручка")
        fieldset = await find_fieldset_by_legend(page, "Выручка")
        from_input = page.locator("#finance_revenue_from").first
        inputs = fieldset.locator("input")
        if revenue_min is not None:
            target = from_input if await from_input.count() else inputs.nth(0)
            await self.human.human_fill(page, target, str(revenue_min), "Выручка от")
        if revenue_max is not None:
            target = page.locator("#finance_revenue_to").first
            if not await target.count():
                target = inputs.nth(1)
            await self.human.human_fill(page, target, str(revenue_max), "Выручка до")
        await self._wait_filter_update(page)

    async def apply_employees(self, page, employees_min: int | None, employees_max: int | None) -> None:
        if employees_min is None and employees_max is None:
            return
        logger.info("[Rusprofile] applying employees: %s - %s", employees_min, employees_max)
        await self._click_filter_header(page, "Количество сотрудников")
        fieldset = await find_fieldset_by_legend(page, "Количество сотрудников")
        inputs = fieldset.locator("input")
        if employees_min is not None:
            await self.human.human_fill(page, inputs.nth(0), str(employees_min), "Сотрудников от")
        if employees_max is not None:
            await self.human.human_fill(page, inputs.nth(1), str(employees_max), "Сотрудников до")
        await self._wait_filter_update(page)

    async def collect_until_limit(self, page, limit: int) -> list[RusprofileSearchItem]:
        items: list[RusprofileSearchItem] = []
        page_number = 1
        while len(items) < limit:
            page_items = await self.collect_results_page(page)
            logger.info("[Rusprofile] collected %s companies from page %s", len(page_items), page_number)
            for item in page_items:
                if item.source_url not in {existing.source_url for existing in items}:
                    items.append(item)
                if len(items) >= limit:
                    break
            if len(items) >= limit or not await self.go_to_next_page(page):
                break
            page_number += 1
        return items[:limit]

    async def collect_results_page(self, page) -> list[RusprofileSearchItem]:
        logger.info("[Rusprofile] collecting result cards")
        await self.human.smooth_scroll(page, direction="down", steps=2)
        links = page.locator("a[href*='/id/']")
        count = await links.count()
        items: list[RusprofileSearchItem] = []
        seen_urls: set[str] = set()
        for index in range(count):
            link = links.nth(index)
            href = absolute_rusprofile_url(await link.get_attribute("href"))
            if not href or href in seen_urls:
                continue
            seen_urls.add(href)
            text = await self._surrounding_result_text(link)
            company_name = await link.inner_text(timeout=3000)
            items.append(
                RusprofileSearchItem(
                    company_name=_clean(company_name),
                    source_url=href,
                    revenue_raw=_extract_line(text, "Выручка"),
                    activity_description=_extract_line(text, "Основной вид деятельности") or _extract_activity(text),
                    address_raw=_extract_line(text, "Адрес"),
                    inn=_extract_digits(text, "ИНН"),
                    ogrn=_extract_digits(text, "ОГРН"),
                    registration_date_raw=_extract_registration(text),
                    status_label=_extract_status(text),
                    raw_text=text,
                )
            )
        if not items:
            logger.warning("[Rusprofile] no result cards found")
        return items

    async def go_to_next_page(self, page) -> bool:
        next_link = page.get_by_text(re.compile(r"Следующая|Далее", re.IGNORECASE)).first
        try:
            if await next_link.count() and await next_link.is_visible():
                await self.human.human_click(page, next_link, "Следующая страница")
                await self._wait_filter_update(page)
                return True
        except Exception:
            return False
        return False

    async def debug_screenshot(self, page, name: str) -> None:
        if not settings.rusprofile_debug_screenshots:
            return
        await page.screenshot(path=str(self.screenshot_dir / f"{name}.png"), full_page=True)

    async def _click_filter_header(self, page, text: str) -> None:
        candidates = [
            page.get_by_text(text, exact=True).first,
            page.locator("legend").filter(has_text=text).first,
            page.locator("button, a, div").filter(has_text=text).first,
        ]
        await self._click_first_available(page, candidates, text)

    async def _click_first_available(self, page, candidates, label: str) -> None:
        for locator in candidates:
            try:
                if await locator.count() and await locator.is_visible():
                    await self.human.human_click(page, locator, label)
                    return
            except Exception:
                continue
        raise FilterApplyError(f"selector_not_found: {label}")

    async def _click_checkbox_row_by_text(
        self,
        page,
        container,
        text: str,
        label: str,
        only_if_unchecked: bool = False,
    ) -> None:
        clicked = await container.evaluate(
            """(root, args) => {
                const needle = (args.text || '').replace(/\\s+/g, ' ').trim();
                const onlyIfUnchecked = args.onlyIfUnchecked;
                const norm = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                const checkboxSelector = 'input[type="checkbox"], [role="checkbox"]';
                const candidates = [];

                const isChecked = (target) => {
                    if (!target) return false;
                    if (target.matches && target.matches('input[type="checkbox"]')) return Boolean(target.checked);
                    return target.getAttribute && target.getAttribute('aria-checked') === 'true';
                };

                const pushCandidate = (target, row, sourceRank) => {
                    if (!target || !row) return;
                    const rowText = norm(row.innerText || row.textContent);
                    if (!rowText.includes(needle)) return;
                    const startsWithNeedle = rowText.startsWith(needle);
                    const exactish = rowText === needle || rowText.startsWith(`${needle} `);
                    candidates.push({
                        target,
                        rowText,
                        sourceRank,
                        score: (exactish ? 0 : startsWithNeedle ? 1 : 2),
                        length: rowText.length,
                    });
                };

                for (const target of Array.from(root.querySelectorAll(checkboxSelector))) {
                    let row = target.closest('label, li, tr, .checkbox, .form-check, .tree-item') || target.parentElement;
                    for (let depth = 0; row && row !== root && depth < 8; depth += 1, row = row.parentElement) {
                        if (norm(row.innerText || row.textContent).includes(needle)) {
                            pushCandidate(target, row, 0);
                            break;
                        }
                    }
                }

                for (const node of Array.from(root.querySelectorAll('label, li, div, span, a, button'))) {
                    if (!norm(node.innerText || node.textContent).includes(needle)) continue;
                    const row = node.closest('label, li, tr, .checkbox, .form-check, .tree-item') || node;
                    const target = row.querySelector(checkboxSelector) || node;
                    pushCandidate(target, row, 1);
                }

                candidates.sort((a, b) => (
                    a.score - b.score ||
                    a.length - b.length ||
                    a.sourceRank - b.sourceRank
                ));

                const best = candidates[0];
                if (!best) return { clicked: false };
                if (onlyIfUnchecked && isChecked(best.target)) {
                    return { clicked: true, alreadyChecked: true, rowText: best.rowText };
                }
                best.target.click();
                return { clicked: true, rowText: best.rowText };
            }""",
            {"text": text, "onlyIfUnchecked": only_if_unchecked},
        )
        if clicked.get("clicked"):
            if clicked.get("alreadyChecked"):
                logger.info("[Rusprofile] checkbox already checked: %s (%s)", label, clicked.get("rowText"))
            else:
                logger.info("[Rusprofile] checkbox clicked: %s (%s)", label, clicked.get("rowText"))
            await self.human.wait_after_action()
            return

        candidates = [
            container.locator("label").filter(has_text=text).first,
            container.locator("li").filter(has_text=text).first,
            container.locator("div").filter(has_text=text).first,
            container.get_by_text(text, exact=False).first,
        ]
        for locator in candidates:
            try:
                if not await locator.count() or not await locator.is_visible():
                    continue
                checkbox = locator.locator("input[type='checkbox']").first
                if await checkbox.count():
                    checked = await checkbox.is_checked()
                    if only_if_unchecked and checked:
                        logger.info("[Rusprofile] checkbox already checked: %s", label)
                        return
                    await self.human.human_click(page, checkbox, label)
                    return
                await self.human.human_click(page, locator, label)
                return
            except Exception:
                continue
        raise FilterApplyError(f"selector_not_found: {label}")

    async def _click_modal_done(self, page, modal) -> None:
        done = modal.get_by_text("Готово", exact=True).first
        if not await done.count():
            done = page.get_by_text("Готово", exact=True).first
        await self.human.human_click(page, done, "Готово")

    def _parent_okved_code(self, okved_code: str) -> str | None:
        match = re.match(r"^(\d{2})\.", okved_code.strip())
        if not match:
            return None
        return f"{match.group(1)}."

    async def _wait_filter_update(self, page) -> None:
        await self._safe_wait_networkidle(page)
        await self.human.random_delay(800, 1800)

    async def _safe_wait_networkidle(self, page, timeout: int = 10000) -> None:
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception as exc:
            logger.info("[Rusprofile] networkidle skipped: %s", exc)

    async def _safe_inner_text(self, locator) -> str:
        return await safe_inner_text(locator)

    async def _ensure_not_antibot(self, page, allow_manual_clearance: bool = False) -> None:
        cleared = await wait_for_manual_antibot_clearance(
            page,
            allow_manual_clearance=allow_manual_clearance,
            screenshot=lambda name: self.debug_screenshot(page, name),
            context=page.url,
        )
        if cleared:
            await self._safe_wait_networkidle(page)
            return
        raise FilterApplyError("captcha_required")

    async def _surrounding_result_text(self, link) -> str:
        for selector in ("article", "li", "div"):
            parent = link.locator(f"xpath=ancestor::{selector}[1]")
            try:
                if await parent.count():
                    text = await parent.inner_text(timeout=3000)
                    if len(text) > 20:
                        return text
            except Exception:
                continue
        return await link.inner_text(timeout=3000)


def _clean(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"\s+", " ", value).strip()


def _extract_line(text: str | None, label: str) -> str | None:
    if not text:
        return None
    match = re.search(rf"{label}\s*[:\n]\s*([^\n]+)", text, re.IGNORECASE)
    return _clean(match.group(1)) if match else None


def _extract_activity(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"\d{2}\.\d{2}(?:\.\d+)?\s+([^\n]+)", text)
    return _clean(match.group(1)) if match else None


def _extract_digits(text: str | None, label: str) -> str | None:
    if not text:
        return None
    match = re.search(rf"{label}\D*(\d{{10,15}})", text, re.IGNORECASE)
    return match.group(1) if match else None


def _extract_registration(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"\d{2}\.\d{2}\.\d{4}", text)
    return match.group(0) if match else None


def _extract_status(text: str | None) -> str | None:
    if not text:
        return None
    for status in ("Действующая", "В процессе реорганизации", "В процессе ликвидации", "В процессе банкротства", "Ликвидированная"):
        if status.lower() in text.lower():
            return status
    return None
