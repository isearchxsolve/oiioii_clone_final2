# backend/schemas/project.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from enum import Enum


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ProjectVisibility(str, Enum):
    PRIVATE = "private"
    TEAM = "team"
    PUBLIC = "public"


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    visibility: ProjectVisibility = ProjectVisibility.PRIVATE
    tags: List[str] = Field(default_factory=list)
    settings: dict = Field(default_factory=dict)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    visibility: Optional[ProjectVisibility] = None
    tags: Optional[List[str]] = None
    status: Optional[ProjectStatus] = None
    settings: Optional[dict] = None


class ProjectInDB(ProjectBase):
    id: UUID
    owner_id: UUID
    team_id: Optional[UUID] = None
    status: ProjectStatus = ProjectStatus.DRAFT
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Project(ProjectBase):
    id: UUID
    owner_id: UUID
    team_id: Optional[UUID] = None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectListItem(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    status: ProjectStatus
    visibility: ProjectVisibility
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
