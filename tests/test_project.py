
import pytest
from backend.schemas.project import ProjectCreate, ProjectUpdate

def test_project_create_schema():
    project = ProjectCreate(name='Test Project', description='A test project')
    assert project.name == 'Test Project'
    assert project.description == 'A test project'

def test_project_update_schema():
    update = ProjectUpdate(name='Updated Name')
    assert update.name == 'Updated Name'
