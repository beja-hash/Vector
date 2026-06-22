import random

from app.services.company_providers.base import CompanyCandidate, CompanyProvider


class MockProvider(CompanyProvider):
    company_roots = [
        "ТехноСофт",
        "Бизнес Автоматизация",
        "Логистик Про",
        "Маркетинг Групп",
        "Интеграция Плюс",
        "Северная Логистика",
        "ПромТех Комплект",
        "Айти Решения",
        "Диджитал Сервис",
        "Консалт Партнер",
        "Финанс Сервис",
        "МедТех Профи",
        "Строй Контур",
        "Образование Онлайн",
        "ЮрПартнер",
    ]
    okved_by_industry = {
        "IT": ("62.01", "Разработка компьютерного программного обеспечения"),
        "Маркетинг": ("73.11", "Деятельность рекламных агентств"),
        "Производство": ("25.62", "Обработка металлических изделий механическая"),
        "Логистика": ("52.29", "Деятельность вспомогательная, связанная с перевозками"),
        "Медицина": ("86.90", "Деятельность в области медицины прочая"),
        "Образование": ("85.41", "Образование дополнительное детей и взрослых"),
        "Консалтинг": ("70.22", "Консультирование по вопросам коммерческой деятельности"),
        "Строительство": ("41.20", "Строительство жилых и нежилых зданий"),
        "Финансы": ("66.19", "Деятельность вспомогательная в сфере финансовых услуг"),
        "Юридические услуги": ("69.10", "Деятельность в области права"),
    }
    cities_by_region = {
        "Москва": ["Москва"],
        "Санкт-Петербург": ["Санкт-Петербург"],
        "Московская область": ["Химки", "Мытищи", "Красногорск", "Подольск"],
        "Вся РФ": ["Москва", "Санкт-Петербург", "Казань", "Екатеринбург", "Новосибирск", "Краснодар"],
        "Другой регион": ["Казань", "Екатеринбург", "Новосибирск", "Самара", "Ростов-на-Дону"],
    }

    def search_companies(self, filters) -> list[CompanyCandidate]:
        count = max(1, int(filters.requested_companies_count or 50))
        rng = random.Random(f"{filters.id}:{count}:{filters.industry}:{filters.region}")
        companies: list[CompanyCandidate] = []

        for index in range(count):
            root = self.company_roots[index % len(self.company_roots)]
            suffix = "" if index < len(self.company_roots) else f" {index + 1}"
            company_name = f'ООО "{root}{suffix}"'
            inn = self._digits(rng, 10)
            ogrn = self._digits(rng, 13)
            region = filters.region or rng.choice(["Москва", "Санкт-Петербург", "Московская область", "Вся РФ"])
            city = filters.city or rng.choice(self.cities_by_region.get(region, self.cities_by_region["Вся РФ"]))
            okved_main, okved_description = self._okved(filters)
            revenue = self._revenue(filters, rng)
            employees = self._employees(filters, rng)
            company_age = max(filters.company_age_min or 1, rng.randint(filters.company_age_min or 1, 22))
            has_website = self._has_website(filters, rng)
            website = self._website(root, index) if has_website else None
            vacancies_total = self._vacancies_total(filters, rng)
            sales_vacancies = rng.randint(1, max(1, vacancies_total)) if vacancies_total and self._needs_sales(filters) else 0
            marketing_vacancies = rng.randint(0, max(0, vacancies_total - sales_vacancies)) if vacancies_total else 0
            business_type = filters.business_type if filters.business_type != "Любой" else rng.choice(["B2B", "B2C", "B2G"])

            companies.append(
                CompanyCandidate(
                    company_name=company_name,
                    inn=inn,
                    ogrn=ogrn,
                    region=region,
                    city=city,
                    okved_main=filters.okved or okved_main,
                    okved_description=okved_description,
                    revenue=revenue,
                    employees_count=employees,
                    company_age=company_age,
                    website=website,
                    has_website=has_website,
                    vacancies_total=vacancies_total,
                    sales_vacancies=sales_vacancies,
                    marketing_vacancies=marketing_vacancies,
                    business_type=business_type,
                    source_name="MockProvider",
                    source_url="mock://company-provider",
                    comment="Моковая компания, сгенерирована по фильтрам ICP.",
                )
            )

        return companies

    def _digits(self, rng: random.Random, length: int) -> str:
        first = str(rng.randint(1, 9))
        rest = "".join(str(rng.randint(0, 9)) for _ in range(length - 1))
        return first + rest

    def _okved(self, filters) -> tuple[str, str]:
        if filters.industry in self.okved_by_industry:
            return self.okved_by_industry[filters.industry]
        return ("46.90", "Торговля оптовая неспециализированная")

    def _revenue(self, filters, rng: random.Random) -> int | None:
        if filters.exclude_no_revenue or filters.data_completeness == "revenue_only":
            minimum = filters.revenue_min or 12_000_000
            maximum = filters.revenue_max or max(minimum, 450_000_000)
            return rng.randint(minimum, maximum)
        if rng.random() < 0.1:
            return None
        minimum = filters.revenue_min or 5_000_000
        maximum = filters.revenue_max or max(minimum, 700_000_000)
        return rng.randint(minimum, maximum)

    def _employees(self, filters, rng: random.Random) -> int:
        minimum = filters.employees_min or (11 if filters.exclude_microbusiness else 3)
        maximum = filters.employees_max or max(minimum, 250)
        return rng.randint(minimum, maximum)

    def _has_website(self, filters, rng: random.Random) -> bool:
        if filters.website_requirement == "required" or filters.data_completeness == "website_only":
            return True
        if filters.website_requirement == "not_required":
            return False
        return rng.random() > 0.2

    def _vacancies_total(self, filters, rng: random.Random) -> int:
        if filters.vacancies_requirement == "has_vacancies" or filters.data_completeness == "vacancies_only":
            return rng.randint(1, 12)
        return rng.randint(0, 8) if rng.random() > 0.35 else 0

    def _needs_sales(self, filters) -> bool:
        return (
            filters.sales_department_requirement in {"required", "preferred"}
            or "sales" in filters.vacancy_categories
        )

    def _website(self, root: str, index: int) -> str:
        slug = self._slug(root)
        return f"https://{slug}-{index + 1}.example.ru"

    def _slug(self, value: str) -> str:
        letters = {
            "а": "a",
            "б": "b",
            "в": "v",
            "г": "g",
            "д": "d",
            "е": "e",
            "ё": "e",
            "ж": "zh",
            "з": "z",
            "и": "i",
            "й": "y",
            "к": "k",
            "л": "l",
            "м": "m",
            "н": "n",
            "о": "o",
            "п": "p",
            "р": "r",
            "с": "s",
            "т": "t",
            "у": "u",
            "ф": "f",
            "х": "h",
            "ц": "c",
            "ч": "ch",
            "ш": "sh",
            "щ": "sch",
            "ы": "y",
            "э": "e",
            "ю": "yu",
            "я": "ya",
        }
        parts = []
        for char in value.lower():
            if char.isascii() and char.isalnum():
                parts.append(char)
            elif char in letters:
                parts.append(letters[char])
            elif char in {" ", "-", "_"}:
                parts.append("-")
        return "-".join(part for part in "".join(parts).split("-") if part)
