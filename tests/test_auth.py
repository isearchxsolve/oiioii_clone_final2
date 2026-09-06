
import pytest
from backend.schemas.auth import UserCreate, LoginRequest

def test_user_create_schema():
    user = UserCreate(email='test@example.com', username='testuser', password='password123', full_name='Test User')
    assert user.email == 'test@example.com'
    assert user.username == 'testuser'

def test_login_request_schema():
    login = LoginRequest(email='test@example.com', password='password123')
    assert login.email == 'test@example.com'
    assert login.password == 'password123'
