import asyncio
import logging
import os
import platform
import re
from dataclasses import asdict, replace
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.company_result import CompanyResult
from app.models.raw_company_snapshot import RawCompanySnapshot
from app.models.search import Search
from app.services.company_scoring import CompanyForScoring, CompanyIcpScorer, IcpProfile, IcpScoreResult
from app.services.company_scoring.icp_scorer import hard_prefilter_company, hard_skip_result, manual_review_result
from app.services.company_providers.base import CompanyProvider
from app.services.company_providers.mock_provider import MockProvider
from app.services.company_providers.rusprofile.errors import FilterApplyError
from app.services.company_providers.rusprofile.human_like import HumanLikePlaywrightController
from app.services.company_providers.rusprofile.schemas import RusprofileRunResult, RusprofileSearchFilters
from app.services.company_providers.rusprofile.search_worker import RusprofileSearchWorker

logger = logging.getLogger(__name__)


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

    def run_rusprofile(self, db: Session, search: Search, filters: RusprofileSearchFilters) -> dict:
        self._clear_previous_results(db, search.id)
        search.data_source = "rusprofile"
        search.status = "running"
        search.error_message = None
        db.commit()

        filters = self._ensure_supported_browser_mode(filters)
        human = HumanLikePlaywrightController(enabled=filters.human_mode)
        worker = RusprofileSearchWorker(human=human)
        try:
            result = asyncio.run(worker.run(filters))
        except FilterApplyError as exc:
            search.status = "failed"
            search.error_message = str(exc)
            search.completed_at = datetime.utcnow()
            db.commit()
            raise

        counters = self._persist_rusprofile_result(db, search, result)
        search.status = "completed" if not result.errors or counters["saved"] or counters["manual_review"] else "failed"
        search.completed_at = datetime.utcnow()
        search.error_message = "; ".join(result.errors) if search.status == "failed" else None
        db.commit()
        db.refresh(search)
        return {
            "search_id": search.id,
            "status": search.status,
            "collected": result.collected,
            "saved": counters["saved"],
            "duplicates": counters["duplicates"],
            "failed": result.failed,
            "scored": counters["scored"],
            "manual_review": counters["manual_review"],
            "skipped": counters["skipped"],
            "errors": result.errors,
        }

    def _persist_rusprofile_result(self, db: Session, search: Search, result: RusprofileRunResult) -> dict:
        saved = 0
        duplicates = 0
        scored = 0
        manual_review = 0
        skipped = 0
        existing_keys = self._existing_company_keys(db, search.id)
        scoring_enabled = self._is_llm_scoring_enabled(search)
        scorer = self._build_scorer(search) if scoring_enabled else None
        icp = self._build_icp_profile(search) if scoring_enabled else None

        for raw, parsed in zip(result.raw_snapshots, result.parsed_companies, strict=False):
            self._sanitize_raw_snapshot(raw)
            raw_model = RawCompanySnapshot(search_id=search.id, **asdict(raw))
            db.add(raw_model)
            db.flush()

            candidate = parsed.candidate
            key = self._dedupe_key(candidate.inn, candidate.source_url)
            if key and key in existing_keys:
                duplicates += 1
                raw_model.status = "duplicate"
                raw_model.error_message = "duplicate_inn_skipped" if candidate.inn else "duplicate_source_url_skipped"
                continue

            payload = asdict(candidate)
            payload["raw_snapshot_id"] = raw_model.id
            if scorer and icp:
                company_for_scoring = self._build_company_for_scoring(candidate)
                score_result, llm_model, was_llm_scored = self._score_candidate(scorer, icp, company_for_scoring)
                payload.update(self._score_payload(score_result, llm_model))
                self._attach_scoring_snapshot(raw_model, score_result, llm_model)
                if was_llm_scored:
                    scored += 1
                if score_result.recommended_action == "add_to_results":
                    saved += 1
                    raw_model.status = "scored"
                elif score_result.recommended_action == "manual_review":
                    manual_review += 1
                    raw_model.status = "manual_review"
                else:
                    skipped += 1
                    raw_model.status = "llm_skip"
            else:
                saved += 1
            db.add(CompanyResult(search_id=search.id, **payload))
            if key:
                existing_keys.add(key)
            logger_message = candidate.inn or candidate.source_url or candidate.company_name
            logger.info("[Rusprofile] saved company result: %s", logger_message)

        return {"saved": saved, "duplicates": duplicates, "scored": scored, "manual_review": manual_review, "skipped": skipped}

    def _clear_previous_results(self, db: Session, search_id: str) -> None:
        db.execute(delete(CompanyResult).where(CompanyResult.search_id == search_id))
        db.execute(delete(RawCompanySnapshot).where(RawCompanySnapshot.search_id == search_id))

    def _existing_company_keys(self, db: Session, search_id: str) -> set[str]:
        rows = db.execute(
            select(CompanyResult.inn, CompanyResult.source_url).where(CompanyResult.search_id == search_id)
        ).all()
        return {key for inn, source_url in rows if (key := self._dedupe_key(inn, source_url))}

    def _dedupe_key(self, inn: str | None, source_url: str | None) -> str | None:
        if inn:
            return f"inn:{inn}"
        if source_url:
            return f"url:{source_url}"
        return None

    def _sanitize_raw_snapshot(self, raw) -> None:
        raw.raw_inn = self._digit_token(raw.raw_inn, (10, 12))
        raw.raw_ogrn = self._digit_token(raw.raw_ogrn, (13, 15))

    def _digit_token(self, value: str | None, lengths: tuple[int, int]) -> str | None:
        if not value:
            return None
        tokens = re.findall(r"\d+", value)
        for token in tokens:
            if lengths[0] <= len(token) <= lengths[1]:
                return token
        return None

    def _is_llm_scoring_enabled(self, search: Search) -> bool:
        if not settings.polza_enabled or not settings.llm_scoring_enabled or not search.llm_scoring_enabled:
            return False
        if not settings.polza_api_key:
            logger.warning("[LLM][ICP] failed: POLZA_API_KEY is not configured")
            return False
        return True

    def _build_scorer(self, search: Search) -> CompanyIcpScorer:
        threshold = search.llm_scoring_threshold or settings.llm_scoring_threshold
        return CompanyIcpScorer(threshold=threshold)

    def _score_candidate(
        self,
        scorer: CompanyIcpScorer,
        icp: IcpProfile,
        company: CompanyForScoring,
    ) -> tuple[IcpScoreResult, str | None, bool]:
        hard_skip_reason = hard_prefilter_company(icp, company)
        if hard_skip_reason:
            logger.info("[LLM][ICP] skipped by hard prefilter: %s", hard_skip_reason)
            return hard_skip_result(hard_skip_reason), None, False
        try:
            return asyncio.run(scorer.score_company(icp, company)), scorer.client.model, True
        except Exception as exc:
            logger.warning("[LLM][ICP] failed: %s", exc)
            return manual_review_result("LLM scoring failed"), scorer.client.model, False

    def _score_payload(self, score_result: IcpScoreResult, llm_model: str | None) -> dict:
        return {
            "icp_score": score_result.score,
            "icp_is_match": score_result.is_match,
            "icp_confidence": score_result.confidence,
            "icp_fit_reason": score_result.fit_reason,
            "icp_mismatch_reason": score_result.mismatch_reason,
            "icp_matched_criteria": score_result.matched_criteria,
            "icp_failed_criteria": score_result.failed_criteria,
            "icp_recommended_action": score_result.recommended_action,
            "llm_model": llm_model,
            "llm_scored_at": datetime.utcnow(),
        }

    def _attach_scoring_snapshot(
        self,
        raw_model: RawCompanySnapshot,
        score_result: IcpScoreResult,
        llm_model: str | None,
    ) -> None:
        raw_payload = dict(raw_model.raw_payload or {})
        raw_payload["icp_scoring"] = {
            **score_result.model_dump(),
            "llm_model": llm_model,
            "scored_at": datetime.utcnow().isoformat(),
        }
        raw_model.raw_payload = raw_payload

    def _build_company_for_scoring(self, candidate) -> CompanyForScoring:
        return CompanyForScoring(
            company_name=candidate.company_name,
            full_company_name=candidate.full_company_name,
            inn=candidate.inn,
            ogrn=candidate.ogrn,
            region=candidate.region,
            city=candidate.city,
            address=candidate.address,
            okved_main=candidate.okved_main,
            okved_description=candidate.okved_description,
            revenue=candidate.revenue,
            revenue_raw=candidate.revenue_raw,
            employees_count=candidate.employees_count,
            website=candidate.website,
            business_type=candidate.business_type,
            activity_description=candidate.okved_description,
            summary_text=candidate.summary_text,
        )

    def _build_icp_profile(self, search: Search) -> IcpProfile:
        project = search.project
        exclude_rules = self._exclude_rules(search, project.excluded_customers if project else None)
        good_signals = self._good_signals(search, project.usual_customers if project else None, project.comment if project else None)
        bad_signals = self._bad_signals(search, project.excluded_customers if project else None)
        business_type = search.business_type if search.business_type != "Любой" else (project.sales_type if project else None)
        return IcpProfile(
            project_name=project.name if project else None,
            offer=project.client_offer if project else None,
            average_check=project.average_deal_size if project else None,
            business_type=business_type if business_type != "Любой" else None,
            industry=search.industry,
            okved_code=search.okved,
            region=self._scoring_region(search.region),
            city=search.city,
            revenue_min=search.revenue_min,
            revenue_max=search.revenue_max,
            employees_min=search.employees_min,
            employees_max=search.employees_max,
            company_age_min=search.company_age_min,
            must_have_website=True if search.website_requirement == "required" else None,
            must_have_vacancies=True if search.vacancies_requirement == "has_vacancies" else None,
            good_signals=good_signals,
            bad_signals=bad_signals,
            exclude_rules=exclude_rules,
        )

    def _scoring_region(self, value: str | None) -> str | None:
        if not value:
            return None
        if value.strip().lower() in {"вся рф", "другой регион", "любой"}:
            return None
        return value

    def _good_signals(self, search: Search, usual_customers: str | None, comment: str | None) -> list[str]:
        signals = self._split_signal_text(usual_customers)
        if search.website_requirement == "required":
            signals.append("У компании есть сайт")
        if search.vacancies_requirement == "has_vacancies":
            signals.append("У компании есть открытые вакансии")
        if search.sales_department_requirement in {"preferred", "required"}:
            signals.append(f"Отдел продаж: {search.sales_department_requirement}")
        if search.vacancy_categories:
            signals.append(f"Интересующие вакансии: {', '.join(search.vacancy_categories)}")
        if search.data_completeness != "partial_allowed":
            signals.append(f"Минимальная полнота данных: {search.data_completeness}")
        if comment:
            signals.append(f"Комментарий пользователя: {comment}")
        return signals

    def _bad_signals(self, search: Search, excluded_customers: str | None) -> list[str]:
        signals = self._split_signal_text(excluded_customers)
        if search.exclude_no_revenue:
            signals.append("Нет выручки")
        if search.exclude_microbusiness:
            signals.append("Микробизнес")
        if search.exclude_government:
            signals.append("Госучреждение")
        if search.exclude_marketplace_sellers:
            signals.append("Маркетплейс-селлер")
        return signals

    def _exclude_rules(self, search: Search, excluded_customers: str | None) -> list[str]:
        rules = self._split_signal_text(excluded_customers)
        if search.exclude_ip:
            rules.append("ИП")
        if search.exclude_liquidated:
            rules.append("Ликвидированные компании")
        if search.exclude_no_revenue:
            rules.append("Компании без выручки")
        if search.exclude_microbusiness:
            rules.append("Микробизнес")
        if search.exclude_government:
            rules.append("Госучреждения")
        if search.exclude_marketplace_sellers:
            rules.append("Маркетплейс-селлеры")
        return rules

    def _split_signal_text(self, value: str | None) -> list[str]:
        if not value:
            return []
        return [item.strip() for item in re.split(r"[\n;]+", value) if item.strip()]

    def _ensure_supported_browser_mode(self, filters: RusprofileSearchFilters) -> RusprofileSearchFilters:
        if not filters.visible_browser:
            return filters
        if platform.system() in {"Darwin", "Windows"}:
            return filters
        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            return filters
        logger.warning("[Rusprofile] visible browser requested but DISPLAY is not set; falling back to headless")
        return replace(filters, visible_browser=False)
