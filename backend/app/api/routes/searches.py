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
from app.schemas.search import SearchCreate, SearchRead
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
    search = Search(project_id=project.id, status="running", **search_data)
    db.add(search)
    db.commit()
    db.refresh(search)

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
