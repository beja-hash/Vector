async def find_fieldset_by_legend(page, legend_text: str):
    fieldset = page.locator("fieldset").filter(has=page.locator("legend", has_text=legend_text))
    if await fieldset.count():
        return fieldset.first
    return page.locator("section, div").filter(has_text=legend_text).first


async def first_visible(locator):
    count = await locator.count()
    for index in range(count):
        item = locator.nth(index)
        if await item.is_visible():
            return item
    return locator.first


def absolute_rusprofile_url(href: str | None) -> str | None:
    if not href:
        return None
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return f"https://www.rusprofile.ru{href}"
    return f"https://www.rusprofile.ru/{href}"
