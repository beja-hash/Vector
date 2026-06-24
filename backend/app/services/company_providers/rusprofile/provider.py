import asyncio

from app.core.config import settings
from app.services.company_providers.base import CompanyCandidate, CompanyProvider
from app.services.company_providers.rusprofile.filters import normalize_filter_value
from app.services.company_providers.rusprofile.human_like import HumanLikePlaywrightController
from app.services.company_providers.rusprofile.schemas import RusprofileSearchFilters
from app.services.company_providers.rusprofile.search_worker import RusprofileSearchWorker


class RusprofileProvider(CompanyProvider):
    def search_companies(self, filters) -> list[CompanyCandidate]:
        run_filters = RusprofileSearchFilters(
            active_only=filters.active_only,
            industry=normalize_filter_value(filters.industry),
            okved_code=normalize_filter_value(filters.okved),
            region=normalize_filter_value(filters.region),
            revenue_min=filters.revenue_min,
            revenue_max=filters.revenue_max,
            employees_min=filters.employees_min,
            employees_max=filters.employees_max,
            limit=filters.requested_companies_count,
            visible_browser=getattr(filters, "visible_browser", not settings.rusprofile_headless),
            human_mode=getattr(filters, "human_mode", settings.rusprofile_human_mode),
        )
        human = HumanLikePlaywrightController(enabled=run_filters.human_mode)
        worker = RusprofileSearchWorker(human=human)
        result = asyncio.run(worker.run(run_filters))
        return [parsed.candidate for parsed in result.parsed_companies]
