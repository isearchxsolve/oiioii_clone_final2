# backend/services/auth_service.py
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from backend.core.config import settings


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, payload: RegisterRequest) -> TokenResponse:
        if self.db.query(User).filter(User.email == payload.email).first():
            raise AuthError("Email already registered", 409)

        password_hash = bcrypt.hashpw(
            payload.password.encode("utf-8"),
            bcrypt.gensalt(rounds=12)
        ).decode("utf-8")

        user = User(
            email=payload.email,
            password_hash=password_hash,
            full_name=payload.full_name,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return self._create_token_response(user)

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.db.query(User).filter(User.email == payload.email).first()
        if not user:
            raise AuthError("Invalid credentials", 401)

        if not bcrypt.checkpw(
            payload.password.encode("utf-8"),
            user.password_hash.encode("utf-8")
        ):
            raise AuthError("Invalid credentials", 401)

        return self._create_token_response(user)

    def _create_token_response(self, user: User) -> TokenResponse:
        access_token = self._create_access_token(user.id)
        refresh_token = self._create_refresh_token(user.id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def _create_access_token(self, user_id: int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": str(user_id), "exp": expire, "type": "access"}
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def _create_refresh_token(self, user_id: int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {"sub": str(user_id), "exp": expire, "type": "refresh"}
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def verify_token(self, token: str, token_type: str = "access") -> int:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") != token_type:
                raise AuthError("Invalid token type", 401)
            return int(payload["sub"])
        except JWTError as e:
            raise AuthError(f"Invalid token: {str(e)}", 401)

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        user_id = self.verify_token(refresh_token, "refresh")
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AuthError("User not found", 404)
        return self._create_token_response(user)