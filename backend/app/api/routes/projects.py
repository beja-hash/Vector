from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.project import Project
from app.models.search import Search
from app.schemas.project import ProjectCreate, ProjectRead


router = APIRouter(prefix="/projects", tags=["projects"])


def project_to_read(project: Project) -> ProjectRead:
    search_count = len(project.searches)
    companies_count = sum(len(search.results) for search in project.searches)
    return ProjectRead.model_validate(project).model_copy(
        update={
            "search_count": search_count,
            "companies_count": companies_count,
            "status": "active",
        }
    )


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[ProjectRead]:
    projects = db.scalars(
        select(Project)
        .options(selectinload(Project.searches).selectinload(Search.results))
        .order_by(Project.created_at.desc())
    ).all()
    return [project_to_read(project) for project in projects]


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectRead:
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project_to_read(project)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)) -> ProjectRead:
    project = db.scalar(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.searches).selectinload(Search.results))
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_to_read(project)
