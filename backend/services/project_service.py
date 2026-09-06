# backend/app/services/project_service.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID, uuid4

from app.models.project import Project, ProjectMember, ProjectRole
from app.models.user import User
from app.repositories.project_repo import ProjectRepository
from app.repositories.user_repo import UserRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectNotFound(Exception):
    """Raised when a project does not exist or is not accessible."""
    def __init__(self, project_id: UUID):
        self.project_id = project_id
        super().__init__(f"Project {project_id} not found")


class ValidationError(Exception):
    """Raised when project data fails validation."""
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message)


class PermissionDenied(Exception):
    """Raised when user lacks required project role."""
    def __init__(self, action: str, required_role: ProjectRole):
        self.action = action
        self.required_role = required_role
        super().__init__(
            f"Permission denied: {action} requires {required_role.value} role or higher"
        )


@dataclass(slots=True)
class ProjectService:
    """
    Domain service for project lifecycle and membership.
    Encapsulates business rules: ownership, roles, workflow initiation gates.
    """
    project_repo: ProjectRepository
    user_repo: UserRepository

    # ──────────────────────────────────────────────────────────────
    # Read operations
    # ──────────────────────────────────────────────────────────────
    async def list_projects(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Project]:
        """Return projects where user is a member (any role)."""
        if limit < 1 or limit > 200:
            raise ValidationError("limit must be between 1 and 200", "limit")
        if offset < 0:
            raise ValidationError("offset must be non-negative", "offset")

        return await self.project_repo.list_for_user(user_id, limit=limit, offset=offset)

    async def get_project(self, project_id: UUID, user_id: UUID) -> Project:
        """Fetch project and verify membership."""
        project = await self.project_repo.get_with_members(project_id)
        if not project:
            raise ProjectNotFound(project_id)

        if not self._is_member(project, user_id):
            raise ProjectNotFound(project_id)  # don't leak existence

        return project

    async def get_project_for_owner(self, project_id: UUID, owner_id: UUID) -> Project:
        """Fetch project and verify ownership (for destructive ops)."""
        project = await self.get_project(project_id, owner_id)
        if project.owner_id != owner_id:
            raise PermissionDenied("access project as owner", ProjectRole.OWNER)
        return project

    # ──────────────────────────────────────────────────────────────
    # Write operations
    # ──────────────────────────────────────────────────────────────
    async def create_project(self, owner_id: UUID, data: ProjectCreate) -> Project:
        """Create a new project with the caller as owner."""
        owner = await self.user_repo.get(owner_id)
        if not owner:
            raise ValidationError("Owner user does not exist", "owner_id")

        self._validate_create_data(data)

        project = Project(
            id=uuid4(),
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            owner_id=owner_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Owner membership row
        project.members.append(
            ProjectMember(
                project_id=project.id,
                user_id=owner_id,
                role=ProjectRole.OWNER,
                joined_at=datetime.utcnow(),
            )
        )

        await self.project_repo.add(project)
        return project

    async def update_project(
        self,
        project_id: UUID,
        user_id: UUID,
        data: ProjectUpdate,
    ) -> Project:
        """Update project metadata. Requires ADMIN or OWNER role."""
        project = await self.get_project(project_id, user_id)
        self._require_role(project, user_id, ProjectRole.ADMIN)

        if data.name is not None:
            name = data.name.strip()
            if not name:
                raise ValidationError("Project name cannot be empty", "name")
            if len(name) > 200:
                raise ValidationError("Project name too long (max 200 chars)", "name")
            project.name = name

        if data.description is not None:
            desc = data.description.strip()
            if len(desc) > 5000:
                raise ValidationError("Description too long (max 5000 chars)", "description")
            project.description = desc or None

        project.updated_at = datetime.utcnow()
        await self.project_repo.flush()
        return project

    async def delete_project(self, project_id: UUID, owner_id: UUID) -> None:
        """Hard delete project. Only owner may invoke."""
        project = await self.get_project_for_owner(project_id, owner_id)
        await self.project_repo.delete(project)

    # ──────────────────────────────────────────────────────────────
    # Membership management
    # ──────────────────────────────────────────────────────────────
    async def add_member(
        self,
        project_id: UUID,
        actor_id: UUID,
        new_member_id: UUID,
        role: ProjectRole = ProjectRole.VIEWER,
    ) -> ProjectMember:
        """Add a user to project. Requires ADMIN or OWNER."""
        project = await self.get_project(project_id, actor_id)
        self._require_role(project, actor_id, ProjectRole.ADMIN)

        if role == ProjectRole.OWNER:
            raise ValidationError("Cannot assign OWNER role via add_member", "role")

        new_user = await self.user_repo.get(new_member_id)
        if not new_user:
            raise ValidationError("User to add does not exist", "new_member_id")

        if self._is_member(project, new_member_id):
            raise ValidationError("User is already a member", "new_member_id")

        member = ProjectMember(
            project_id=project_id,
            user_id=new_member_id,
            role=role,
            joined_at=datetime.utcnow(),
        )
        project.members.append(member)
        await self.project_repo.flush()
        return member

    async def remove_member(
        self,
        project_id: UUID,
        actor_id: UUID,
        target_user_id: UUID,
    ) -> None:
        """Remove a member. Requires ADMIN/OWNER; cannot remove owner."""
        project = await self.get_project(project_id, actor_id)
        self._require_role(project, actor_id, ProjectRole.ADMIN)

        if target_user_id == project.owner_id:
            raise ValidationError("Cannot remove project owner", "target_user_id")

        member = next((m for m in project.members if m.user_id == target_user_id), None)
        if not member:
            raise ValidationError("User is not a member", "target_user_id")

        project.members.remove(member)
        await self.project_repo.flush()

    async def change_member_role(
        self,
        project_id: UUID,
        actor_id: UUID,
        target_user_id: UUID,
        new_role: ProjectRole,
    ) -> ProjectMember:
        """Change a member's role. Requires OWNER; cannot change owner."""
        project = await self.get_project(project_id, actor_id)
        self._require_role(project, actor_id, ProjectRole.OWNER)

        if target_user_id == project.owner_id:
            raise ValidationError("Cannot change owner's role", "target_user_id")

        if new_role == ProjectRole.OWNER:
            raise ValidationError("Use transfer_ownership to change owner", "new_role")

        member = next((m for m in project.members if m.user_id == target_user_id), None)
        if not member:
            raise ValidationError("User is not a member", "target_user_id")

        member.role = new_role
        await self.project_repo.flush()
        return member

    async def transfer_ownership(
        self,
        project_id: UUID,
        current_owner_id: UUID,
        new_owner_id: UUID,
    ) -> Project:
        """Transfer project ownership. Only current owner may invoke."""
        project = await self.get_project_for_owner(project_id, current_owner_id)

        new_owner = await self.user_repo.get(new_owner_id)
        if not new_owner:
            raise ValidationError("New owner user does not exist", "new_owner_id")

        if not self._is_member(project, new_owner_id):
            raise ValidationError("New owner must be a project member", "new_owner_id")

        # Demote current owner to ADMIN
        current_owner_member = next(
            m for m in project.members if m.user_id == current_owner_id
        )
        current_owner_member.role = ProjectRole.ADMIN

        # Promote new owner
        new_owner_member = next(
            m for m in project.members if m.user_id == new_owner_id
        )
        new_owner_member.role = ProjectRole.OWNER

        project.owner_id = new_owner_id
        project.updated_at = datetime.utcnow()
        await self.project_repo.flush()
        return project

    # ──────────────────────────────────────────────────────────────
    # Workflow initiation gate
    # ──────────────────────────────────────────────────────────────
    async def can_start_workflow(self, project_id: UUID, user_id: UUID) -> bool:
        """Check if user has permission to start a workflow (EDITOR+)."""
        project = await self.get_project(project_id, user_id)
        member = next(m for m in project.members if m.user_id == user_id)
        return member.role.value in {ProjectRole.OWNER.value, ProjectRole.ADMIN.value, ProjectRole.EDITOR.value}

    # ──────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────
    @staticmethod
    def _is_member(project: Project, user_id: UUID) -> bool:
        return any(m.user_id == user_id for m in project.members)

    @staticmethod
    def _require_role(project: Project, user_id: UUID, min_role: ProjectRole) -> None:
        member = next((m for m in project.members if m.user_id == user_id), None)
        if not member:
            raise PermissionDenied("access project", min_role)

        role_hierarchy = {
            ProjectRole.VIEWER: 0,
            ProjectRole.EDITOR: 1,
            ProjectRole.ADMIN: 2,
            ProjectRole.OWNER: 3,
        }
        if role_hierarchy[member.role] < role_hierarchy[min_role]:
            raise PermissionDenied("perform action", min_role)

    @staticmethod
    def _validate_create_data(data: ProjectCreate) -> None:
        name = data.name.strip()
        if not name:
            raise ValidationError("Project name is required", "name")
        if len(name) > 200:
            raise ValidationError("Project name too long (max 200 chars)", "name")
        if data.description and len(data.description) > 5000:
            raise ValidationError("Description too long (max 5000 chars)", "description")