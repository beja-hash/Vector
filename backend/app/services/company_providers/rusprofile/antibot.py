import logging
from collections.abc import Awaitable, Callable

from app.core.config import settings

logger = logging.getLogger(__name__)

ANTIBOT_MARKERS = (
    "активность с вашего ip-адреса была распознана как автоматическая",
    "я не робот",
    "captcha",
    "капча",
)


def is_antibot_text(text: str | None) -> bool:
    if not text:
        return False
    normalized = text.lower()
    return any(marker in normalized for marker in ANTIBOT_MARKERS)


async def safe_inner_text(locator) -> str:
    try:
        return await locator.inner_text(timeout=3000)
    except Exception as exc:
        return f"<inner_text_failed: {exc}>"


async def wait_for_manual_antibot_clearance(
    page,
    *,
    allow_manual_clearance: bool,
    screenshot: Callable[[str], Awaitable[None]] | None = None,
    context: str = "page",
) -> bool:
    body_text = await safe_inner_text(page.locator("body"))
    if not is_antibot_text(body_text):
        return True

    logger.warning("[Rusprofile] captcha_required: %s", context)
    if screenshot:
        await screenshot("00-captcha-required")

    if not allow_manual_clearance:
        return False

    logger.warning("[Rusprofile] waiting for manual captcha clearance: %s", context)
    try:
        await page.bring_to_front()
    except Exception:
        pass

    poll_interval_ms = max(500, settings.rusprofile_captcha_poll_interval_ms)
    attempts = max(1, int(settings.rusprofile_captcha_manual_timeout_seconds * 1000 / poll_interval_ms))
    for _ in range(attempts):
        await page.wait_for_timeout(poll_interval_ms)
        body_text = await safe_inner_text(page.locator("body"))
        if not is_antibot_text(body_text):
            logger.info("[Rusprofile] captcha cleared manually: %s", context)
            return True

    logger.warning("[Rusprofile] manual captcha timeout: %s", context)
    return False
