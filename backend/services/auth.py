import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.user import User, UserRole
from backend.models.api_key import APIKey
from backend.db.session import get_db


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"


@dataclass
class TokenPayload:
    sub: str
    email: str
    role: str
    token_type: TokenType
    exp: int
    iat: int
    jti: str
    permissions: List[str]


@dataclass
class AuthResult:
    user: User
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthConfig:
    SECRET_KEY: str = os.getenv("AUTH_SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    API_KEY_PREFIX: str = "oiioii_"
    API_KEY_LENGTH: int = 32
    BCRYPT_ROUNDS: int = 12
    ISSUER: str = "oiioii"
    AUDIENCE: str = "oiioii-api"


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=AuthConfig.BCRYPT_ROUNDS)
security = HTTPBearer(auto_error=False)


class AuthError(Exception):
    def __init__(self, message: str, code: str = "AUTH_ERROR", status_code: int = status.HTTP_401_UNAUTHORIZED):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class InvalidCredentialsError(AuthError):
    def __init__(self):
        super().__init__("Invalid email or password", "INVALID_CREDENTIALS", status.HTTP_401_UNAUTHORIZED)


class TokenExpiredError(AuthError):
    def __init__(self):
        super().__init__("Token has expired", "TOKEN_EXPIRED", status.HTTP_401_UNAUTHORIZED)


class TokenInvalidError(AuthError):
    def __init__(self, detail: str = "Invalid token"):
        super().__init__(detail, "TOKEN_INVALID", status.HTTP_401_UNAUTHORIZED)


class InsufficientPermissionsError(AuthError):
    def __init__(self, required: str):
        super().__init__(f"Insufficient permissions: {required} required", "INSUFFICIENT_PERMISSIONS", status.HTTP_403_FORBIDDEN)


class UserNotFoundError(AuthError):
    def __init__(self):
        super().__init__("User not found", "USER_NOT_FOUND", status.HTTP_404_NOT_FOUND)


class EmailAlreadyExistsError(AuthError):
    def __init__(self):
        super().__init__("Email already registered", "EMAIL_EXISTS", status.HTTP_409_CONFLICT)


class AccountDisabledError(AuthError):
    def __init__(self):
        super().__init__("Account is disabled", "ACCOUNT_DISABLED", status.HTTP_403_FORBIDDEN)


class EmailNotVerifiedError(AuthError):
    def __init__(self):
        super().__init__("Email not verified", "EMAIL_NOT_VERIFIED", status.HTTP_403_FORBIDDEN)


ROLE_PERMISSIONS: Dict[UserRole, List[str]] = {
    UserRole.ADMIN: ["*"],
    UserRole.CREATOR: [
        "projects:create", "projects:read", "projects:update", "projects:delete",
        "workflows:create", "workflows:read", "workflows:update", "workflows:delete",
        "jobs:create", "jobs:read", "jobs:cancel",
        "assets:create", "assets:read", "assets:update", "assets:delete",
        "api_keys:create", "api_keys:read", "api_keys:revoke",
        "billing:read",
    ],
    UserRole.VIEWER: [
        "projects:read",
        "workflows:read",
        "jobs:read",
        "assets:read",
        "billing:read",
    ],
    UserRole.GUEST: [
        "projects:read",
        "assets:read",
    ],
}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(
    subject: str,
    email: str,
    role: UserRole,
    token_type: TokenType,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    now = datetime.now(timezone.utc)
    jti = secrets.token_urlsafe(16)
    
    if expires_delta:
        expire = now + expires_delta
    elif token_type == TokenType.ACCESS:
        expire = now + timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    elif token_type == TokenType.REFRESH:
        expire = now + timedelta(days=AuthConfig.REFRESH_TOKEN_EXPIRE_DAYS)
    elif token_type == TokenType.EMAIL_VERIFICATION:
        expire = now + timedelta(hours=24)
    elif token_type == TokenType.PASSWORD_RESET:
        expire = now + timedelta(hours=1)
    else:
        expire = now + timedelta(days=365)
    
    permissions = ROLE_PERMISSIONS.get(role, [])
    
    claims = {
        "sub": subject,
        "email": email,
        "role": role.value,
        "token_type": token_type.value,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": jti,
        "iss": AuthConfig.ISSUER,
        "aud": AuthConfig.AUDIENCE,
        "permissions": permissions,
    }
    
    if additional_claims:
        claims.update(additional_claims)
    
    return jwt.encode(claims, AuthConfig.SECRET_KEY, algorithm=AuthConfig.ALGORITHM)


def decode_token(token: str, expected_type: Optional[TokenType] = None) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            AuthConfig.SECRET_KEY,
            algorithms=[AuthConfig.ALGORITHM],
            issuer=AuthConfig.ISSUER,
            audience=AuthConfig.AUDIENCE,
        )
    except JWTError as e:
        raise TokenInvalidError(str(e))
    
    token_type = TokenType(payload.get("token_type", "access"))
    if expected_type and token_type != expected_type:
        raise TokenInvalidError(f"Expected token type {expected_type.value}, got {token_type.value}")
    
    return TokenPayload(
        sub=payload["sub"],
        email=payload["email"],
        role=payload["role"],
        token_type=token_type,
        exp=payload["exp"],
        iat=payload["iat"],
        jti=payload["jti"],
        permissions=payload.get("permissions", []),
    )


def generate_api_key() -> tuple[str, str]:
    raw_key = secrets.token_urlsafe(AuthConfig.API_KEY_LENGTH)
    prefixed_key = f"{AuthConfig.API_KEY_PREFIX}{raw_key}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return prefixed_key, key_hash


def create_access_token(user: User) -> str:
    return create_token(
        subject=str(user.id),
        email=user.email,
        role=user.role,
        token_type=TokenType.ACCESS,
    )


def create_refresh_token(user: User) -> str:
    return create_token(
        subject=str(user.id),
        email=user.email,
        role=user.role,
        token_type=TokenType.REFRESH,
    )


def create_email_verification_token(user: User) -> str:
    return create_token(
        subject=str(user.id),
        email=user.email,
        role=user.role,
        token_type=TokenType.EMAIL_VERIFICATION,
    )


def create_password_reset_token(user: User) -> str:
    return create_token(
        subject=str(user.id),
        email=user.email,
        role=user.role,
        token_type=TokenType.PASSWORD_RESET,
    )


async def authenticate_user(db: Session, email: str, password: str) -> User:
    stmt = select(User).where(User.email == email.lower())
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise InvalidCredentialsError()
    
    if not user.is_active:
        raise AccountDisabledError()
    
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError()
    
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    
    return user


async def register_user(
    db: Session,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    role: UserRole = UserRole.CREATOR,
) -> User:
    email = email.lower().strip()
    
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise EmailAlreadyExistsError()
    
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=True,
        is_verified=False,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise TokenInvalidError("Missing authorization header")
    
    payload = decode_token(credentials.credentials, TokenType.ACCESS)
    
    stmt = select(User).where(User.id == payload.sub)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise UserNotFoundError()
    
    if not user.is_active:
        raise AccountDisabledError()
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except AuthError:
        return None


def require_permission(permission: str):
    async def permission_checker(user: User = Depends(get_current_user)) -> User:
        user_permissions = ROLE_PERMISSIONS.get(user.role, [])
        if "*" not in user_permissions and permission not in user_permissions:
            raise InsufficientPermissionsError(permission)
        return user
    return permission_checker


def require_role(*roles: UserRole):
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise InsufficientPermissionsError(f"Role {' or '.join(r.value for r in roles)}")
        return user
    return role_checker


async def validate_api_key(db: Session, api_key: str) -> Optional[APIKey]:
    if not api_key.startswith(AuthConfig.API_KEY_PREFIX):
        return None
    
    raw_key = api_key[len(AuthConfig.API_KEY_PREFIX):]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    stmt = select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active == True)
    result = await db.execute(stmt)
    key_record = result.scalar_one_or_none()
    
    if not key_record:
        return None
    
    if key_record.expires_at and key_record.expires_at < datetime.now(timezone.utc):
        return None
    
    key_record.last_used_at = datetime.now(timezone.utc)
    await db.commit()
    
    return key_record


async def get_api_key_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise TokenInvalidError("Missing API key")
    
    key_record = await validate_api_key(db, credentials.credentials)
    if not key_record:
        raise TokenInvalidError("Invalid or expired API key")
    
    stmt = select(User).where(User.id == key_record.user_id, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise UserNotFoundError()
    
    return user


async def refresh_access_token(refresh_token: str, db: Session) -> AuthResult:
    payload = decode_token(refresh_token, TokenType.REFRESH)
    
    stmt = select(User).where(User.id == payload.sub, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise UserNotFoundError()
    
    access_token = create_access_token(user)
    new_refresh_token = create_refresh_token(user)
    
    return AuthResult(user=user, access_token=access_token, refresh_token=new_refresh_token)


async def verify_email_token(token: str, db: Session) -> User:
    payload = decode_token(token, TokenType.EMAIL_VERIFICATION)
    
    stmt = select(User).where(User.id == payload.sub)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise UserNotFoundError()
    
    if user.is_verified:
        return user
    
    user.is_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    
    return user


async def request_password_reset(email: str, db: Session) -> Optional[str]:
    stmt = select(User).where(User.email == email.lower())
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    return create_password_reset_token(user)


async def reset_password(token: str, new_password: str, db: Session) -> User:
    payload = decode_token(token, TokenType.PASSWORD_RESET)
    
    stmt = select(User).where(User.id == payload.sub, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise UserNotFoundError()