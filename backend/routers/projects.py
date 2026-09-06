# backend/routers/projects.py
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict

from backend.services.project_service import (
    ProjectService,
    ProjectNotFoundError,
    ProjectValidationError,
    ProjectPermissionError,
)
from backend.core.dependencies import get_project_service
from backend.models.project import ProjectStatus, ProjectVisibility


router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    visibility: ProjectVisibility = ProjectVisibility.PRIVATE
    tags: List[str] = Field(default_factory=list, max_length=20)


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    visibility: Optional[ProjectVisibility] = None
    tags: Optional[List[str]] = Field(None, max_length=20)
    status: Optional[ProjectStatus] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str]
    visibility: ProjectVisibility
    status: ProjectStatus
    tags: List[str]
    owner_id: UUID
    created_at: str
    updated_at: str
    thumbnail_url: Optional[str] = None


class ProjectListResponse(BaseModel):
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class ProjectDeleteResponse(BaseModel):
    success: bool
    message: str


def _map_service_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ProjectNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ProjectValidationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if isinstance(exc, ProjectPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_project(
    payload: ProjectCreateRequest,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    try:
        project = await service.create_project(
            name=payload.name,
            description=payload.description,
            visibility=payload.visibility,
            tags=payload.tags,
        )
        return ProjectResponse.model_validate(project)
    except Exception as e:
        raise _map_service_error(e)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project by ID",
)
async def get_project(
    project_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    try:
        project = await service.get_project(project_id)
        return ProjectResponse.model_validate(project)
    except Exception as e:
        raise _map_service_error(e)


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="List projects with pagination and filters",
)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[ProjectStatus] = Query(None, alias="status", description="Filter by status"),
    visibility_filter: Optional[ProjectVisibility] = Query(None, alias="visibility", description="Filter by visibility"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    service: ProjectService = Depends(get_project_service),
) -> ProjectListResponse:
    try:
        result = await service.list_projects(
            page=page,
            page_size=page_size,
            status=status_filter,
            visibility=visibility_filter,
            tag=tag,
            search=search,
        )
        return ProjectListResponse(
            items=[ProjectResponse.model_validate(p) for p in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            has_more=result.has_more,
        )
    except Exception as e:
        raise _map_service_error(e)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
)
async def update_project(
    project_id: UUID,
    payload: ProjectUpdateRequest,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    try:
        update_data = payload.model_dump(exclude_unset=True)
        project = await service.update_project(project_id, **update_data)
        return ProjectResponse.model_validate(project)
    except Exception as e:
        raise _map_service_error(e)


@router.delete(
    "/{project_id}",
    response_model=ProjectDeleteResponse,
    summary="Delete project",
)
async def delete_project(
    project_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> ProjectDeleteResponse:
    try:
        await service.delete_project(project_id)
        return ProjectDeleteResponse(success=True, message="Project deleted successfully")
    except Exception as e:
        raise _map_service_error(e)


@router.post(
    "/{project_id}/archive",
    response_model=ProjectResponse,
    summary="Archive project",
)
async def archive_project(
    project_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    try:
        project = await service.archive_project(project_id)
        return ProjectResponse.model_validate(project)
    except Exception as e:
        raise _map_service_error(e)


@router.post(
    "/{project_id}/restore",
    response_model=ProjectResponse,
    summary="Restore archived project",
)
async def restore_project(
    project_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    try:
        project = await service.restore_project(project_id)
        return ProjectResponse.model_validate(project)
    except Exception as e:
        raise _map_service_error(e)