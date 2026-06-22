from dataclasses import asdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.company_result import CompanyResult
from app.models.search import Search
from app.services.company_providers.base import CompanyProvider
from app.services.company_providers.mock_provider import MockProvider


class SearchRunner:
    def __init__(self, provider: CompanyProvider | None = None) -> None:
        self.provider = provider or MockProvider()

    def run(self, db: Session, search: Search) -> Search:
        candidates = self.provider.search_companies(search)

        for candidate in candidates:
            db.add(CompanyResult(search_id=search.id, **asdict(candidate)))

        search.status = "completed"
        search.completed_at = datetime.utcnow()
        search.error_message = None
        db.commit()
        db.refresh(search)
        return search
