from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.routes.projects import project_to_read
from app.core.database import get_db
from app.models.company_result import CompanyResult
from app.models.project import Project
from app.models.search import Search
from app.schemas.company_result import CompanyResultRead
from app.schemas.search import RusprofileRunRequest, RusprofileRunResponse, SearchCreate, SearchRead
from app.services.company_providers.rusprofile.errors import FilterApplyError
from app.services.company_providers.rusprofile.filters import normalize_filter_value
from app.services.company_providers.rusprofile.schemas import RusprofileSearchFilters
from app.services.export_service import build_companies_csv
from app.services.search_runner import SearchRunner


router = APIRouter(prefix="/searches", tags=["searches"])


def search_to_read(search: Search) -> SearchRead:
    project = project_to_read(search.project) if search.project else None
    return SearchRead.model_validate(search).model_copy(
        update={
            "found_companies_count": len(search.results),
            "project": project,
        }
    )


@router.get("", response_model=list[SearchRead])
def list_searches(db: Session = Depends(get_db)) -> list[SearchRead]:
    searches = db.scalars(
        select(Search)
        .options(selectinload(Search.project).selectinload(Project.searches).selectinload(Search.results))
        .options(selectinload(Search.results))
        .order_by(Search.created_at.desc())
    ).all()
    return [search_to_read(search) for search in searches]


@router.post("", response_model=SearchRead, status_code=status.HTTP_201_CREATED)
def create_search(payload: SearchCreate, db: Session = Depends(get_db)) -> SearchRead:
    project = _resolve_project(db, payload)
    search_data = payload.model_dump(exclude={"project", "project_id"})
    status_value = "running" if payload.data_source == "mock" else "draft"
    search = Search(project_id=project.id, status=status_value, **search_data)
    db.add(search)
    db.commit()
    db.refresh(search)

    if payload.data_source == "rusprofile":
        search = db.scalar(
            select(Search)
            .where(Search.id == search.id)
            .options(selectinload(Search.project).selectinload(Project.searches).selectinload(Search.results))
            .options(selectinload(Search.results))
        )
        if search is None:
            raise HTTPException(status_code=404, detail="Search not found")
        return search_to_read(search)

    runner = SearchRunner()
    try:
        search = runner.run(db, search)
    except Exception as exc:
        db.rollback()
        persisted_search = db.get(Search, search.id)
        if persisted_search is not None:
            persisted_search.status = "failed"
            persisted_search.error_message = str(exc)
            persisted_search.completed_at = datetime.utcnow()
            db.commit()
        raise HTTPException(status_code=500, detail="Search failed") from exc

    search = db.scalar(
        select(Search)
        .where(Search.id == search.id)
        .options(selectinload(Search.project).selectinload(Project.searches).selectinload(Search.results))
        .options(selectinload(Search.results))
    )
    if search is None:
        raise HTTPException(status_code=404, detail="Search not found")
    return search_to_read(search)


@router.post("/{search_id}/run-rusprofile", response_model=RusprofileRunResponse)
def run_rusprofile_search(
    search_id: str,
    payload: RusprofileRunRequest | None = None,
    db: Session = Depends(get_db),
) -> RusprofileRunResponse:
    search = _get_search_or_404(db, search_id)
    request = payload or RusprofileRunRequest()
    if request.llm_scoring_enabled is not None:
        search.llm_scoring_enabled = request.llm_scoring_enabled
    if request.llm_scoring_threshold is not None:
        search.llm_scoring_threshold = request.llm_scoring_threshold
    okved_code = request.okved_code if request.okved_code is not None else search.okved
    region = request.region if request.region is not None else search.region
    filters = RusprofileSearchFilters(
        active_only=search.active_only if request.active_only is None else request.active_only,
        industry=normalize_filter_value(search.industry),
        okved_code=normalize_filter_value(okved_code),
        region=normalize_filter_value(region),
        revenue_min=request.revenue_min if request.revenue_min is not None else search.revenue_min,
        revenue_max=request.revenue_max if request.revenue_max is not None else search.revenue_max,
        employees_min=request.employees_min if request.employees_min is not None else search.employees_min,
        employees_max=request.employees_max if request.employees_max is not None else search.employees_max,
        limit=request.limit if request.limit is not None else search.requested_companies_count,
        visible_browser=request.visible_browser if request.visible_browser is not None else search.visible_browser,
        human_mode=request.human_mode if request.human_mode is not None else search.human_mode,
    )
    runner = SearchRunner()
    try:
        result = runner.run_rusprofile(db, search, filters)
    except FilterApplyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        persisted_search = db.get(Search, search.id)
        if persisted_search is not None:
            persisted_search.status = "failed"
            persisted_search.error_message = str(exc)
            persisted_search.completed_at = datetime.utcnow()
            db.commit()
        raise HTTPException(status_code=500, detail="Rusprofile search failed") from exc
    return RusprofileRunResponse(**result)


@router.get("/{search_id}", response_model=SearchRead)
def get_search(search_id: str, db: Session = Depends(get_db)) -> SearchRead:
    search = _get_search_or_404(db, search_id)
    return search_to_read(search)


@router.get("/{search_id}/results", response_model=list[CompanyResultRead])
def get_search_results(search_id: str, db: Session = Depends(get_db)) -> list[CompanyResultRead]:
    _get_search_or_404(db, search_id)
    results = db.scalars(
        select(CompanyResult)
        .where(CompanyResult.search_id == search_id)
        .order_by(CompanyResult.created_at.asc(), CompanyResult.company_name.asc())
    ).all()
    return list(results)


@router.get("/{search_id}/export.csv")
def export_search_csv(search_id: str, db: Session = Depends(get_db)) -> Response:
    search = _get_search_or_404(db, search_id)
    csv_body = build_companies_csv(search.results)
    filename = f"vector-search-{search_id}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=csv_body, media_type="text/csv; charset=utf-8", headers=headers)


def _resolve_project(db: Session, payload: SearchCreate) -> Project:
    if payload.project_id:
        project = db.get(Project, payload.project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    if payload.project is None:
        raise HTTPException(status_code=400, detail="Either project_id or project must be provided")

    project = Project(**payload.project.model_dump())
    db.add(project)
    db.flush()
    return project


def _get_search_or_404(db: Session, search_id: str) -> Search:
    search = db.scalar(
        select(Search)
        .where(Search.id == search_id)
        .options(selectinload(Search.project).selectinload(Project.searches).selectinload(Search.results))
        .options(selectinload(Search.results))
    )
    if search is None:
        raise HTTPException(status_code=404, detail="Search not found")
    return search
