import enum
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, DateTime, Enum, ForeignKey, Index, UniqueConstraint,
    Boolean, Integer, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ProjectVisibility(str, enum.Enum):
    PRIVATE = "private"
    TEAM = "team"
    PUBLIC = "public"


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False)
    visibility = Column(Enum(ProjectVisibility), default=ProjectVisibility.PRIVATE, nullable=False)

    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)

    settings = Column(JSON, default=dict, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    archived_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="projects")
    team = relationship("Team", back_populates="projects")
    workflows = relationship("Workflow", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
    collaborators = relationship("ProjectCollaborator", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_projects_owner_id", "owner_id"),
        Index("ix_projects_team_id", "team_id"),
        Index("ix_projects_status", "status"),
        Index("ix_projects_created_at", "created_at"),
        UniqueConstraint("owner_id", "name", name="uq_project_owner_name"),
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', status={self.status.value})>"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_archived(self) -> bool:
        return self.status == ProjectStatus.ARCHIVED

    def archive(self) -> None:
        self.status = ProjectStatus.ARCHIVED
        self.archived_at = datetime.utcnow()

    def restore(self) -> None:
        self.status = ProjectStatus.ACTIVE
        self.archived_at = None

    def soft_delete(self) -> None:
        self.status = ProjectStatus.DELETED
        self.deleted_at = datetime.utcnow()


class ProjectCollaboratorRole(str, enum.Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"


class ProjectCollaborator(Base):
    __tablename__ = "project_collaborators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(ProjectCollaboratorRole), default=ProjectCollaboratorRole.VIEWER, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="collaborators")
    user = relationship("User", back_populates="project_collaborations")

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_user"),
        Index("ix_project_collaborators_project_id", "project_id"),
        Index("ix_project_collaborators_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<ProjectCollaborator(project_id={self.project_id}, user_id={self.user_id}, role={self.role.value})>"