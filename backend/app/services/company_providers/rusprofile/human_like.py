import logging
import random

from app.core.config import settings

logger = logging.getLogger(__name__)


class HumanLikePlaywrightController:
    def __init__(
        self,
        enabled: bool = True,
        min_delay_ms: int | None = None,
        max_delay_ms: int | None = None,
        scroll_step_min: int | None = None,
        scroll_step_max: int | None = None,
    ) -> None:
        self.enabled = enabled
        self.min_delay_ms = min_delay_ms or settings.rusprofile_min_delay_ms
        self.max_delay_ms = max_delay_ms or settings.rusprofile_max_delay_ms
        self.scroll_step_min = scroll_step_min or settings.rusprofile_scroll_step_min
        self.scroll_step_max = scroll_step_max or settings.rusprofile_scroll_step_max

    async def random_delay(self, min_ms: int | None = None, max_ms: int | None = None) -> None:
        if not self.enabled:
            return
        delay_ms = random.randint(min_ms or self.min_delay_ms, max_ms or self.max_delay_ms)
        logger.info("[Rusprofile][Human] delay %sms", delay_ms)
        from asyncio import sleep

        await sleep(delay_ms / 1000)

    async def move_to_element(self, page, locator) -> None:
        if not self.enabled:
            return
        box = await locator.bounding_box()
        if not box:
            return
        x_padding = min(5, max(0, box["width"] / 3))
        y_padding = min(5, max(0, box["height"] / 3))
        x = box["x"] + random.uniform(x_padding, max(x_padding, box["width"] - x_padding))
        y = box["y"] + random.uniform(y_padding, max(y_padding, box["height"] - y_padding))
        logger.info("[Rusprofile][Human] moving mouse")
        await page.mouse.move(x, y, steps=random.randint(8, 24))
        await self.random_delay(150, 600)

    async def human_click(self, page, locator, label: str | None = None) -> None:
        if label:
            logger.info("[Rusprofile][Human] moving to: %s", label)
        await self.random_delay()
        try:
            await locator.scroll_into_view_if_needed(timeout=5000)
            await self.move_to_element(page, locator)
            box = await locator.bounding_box()
            if self.enabled and box:
                x = box["x"] + random.uniform(3, max(3, box["width"] - 3))
                y = box["y"] + random.uniform(3, max(3, box["height"] - 3))
                await page.mouse.click(x, y)
            else:
                await locator.click()
        except Exception:
            await locator.click()
        await self.wait_after_action()

    async def human_fill(self, page, locator, value: str, label: str | None = None) -> None:
        if label:
            logger.info("[Rusprofile][Human] typing: %s", label)
        await self.random_delay()
        await locator.scroll_into_view_if_needed(timeout=5000)
        try:
            await self.move_to_element(page, locator)
            await locator.click()
            modifier = "Meta" if await page.evaluate("navigator.platform.includes('Mac')") else "Control"
            await page.keyboard.press(f"{modifier}+A")
            await page.keyboard.press("Backspace")
            if self.enabled:
                await locator.type(value, delay=random.randint(40, 120))
            else:
                await locator.fill(value)
        except Exception:
            await locator.fill(value)
        await self.wait_after_action()

    async def smooth_scroll(self, page, direction: str = "down", steps: int | None = None) -> None:
        if not self.enabled:
            return
        logger.info("[Rusprofile][Human] smooth scroll %s", direction)
        multiplier = -1 if direction == "up" else 1
        for _ in range(steps or random.randint(2, 6)):
            await page.mouse.wheel(0, multiplier * random.randint(self.scroll_step_min, self.scroll_step_max))
            await self.random_delay(150, 500)

    async def scroll_to_locator(self, page, locator) -> None:
        await self.smooth_scroll(page, steps=random.randint(1, 3))
        await locator.scroll_into_view_if_needed(timeout=5000)
        await self.random_delay(200, 700)

    async def wait_after_action(self) -> None:
        await self.random_delay(500, 1800)
