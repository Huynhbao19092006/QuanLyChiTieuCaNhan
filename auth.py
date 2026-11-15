
from datetime import datetime, timedelta, timezone

import jwt

from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

from config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    OAUTH2_SCOPES,
)


# =====================================================
# 1. CẤU HÌNH MÃ HÓA MẬT KHẨU ARGON2
# =====================================================

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Mã hóa mật khẩu trước khi lưu vào database."""
    return pwd_context.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    """Kiểm tra mật khẩu người dùng."""
    try:
        return pwd_context.verify(
            password,
            hashed_password,
        )
    except (ValueError, TypeError):
        return False


# =====================================================
# 2. CẤU HÌNH OAUTH2
# =====================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/token",
    scopes=OAUTH2_SCOPES,
)


# =====================================================
# 3. TẠO JWT ACCESS TOKEN
# =====================================================

def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Tạo JWT Access Token.

    data: thông tin cần lưu trong token.
    expires_delta: thời gian hết hạn tùy chỉnh.
    """

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return encoded_jwt


# =====================================================
# 4. GIẢI MÃ VÀ KIỂM TRA JWT
# =====================================================

def decode_access_token(token: str):
    """
    Giải mã JWT và kiểm tra tính hợp lệ.

    Trả về payload nếu hợp lệ.
    Trả về None nếu token không hợp lệ hoặc hết hạn.
    """

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={
                "require": ["exp", "iat", "sub"],
            },
        )

        username = payload.get("sub")
        scopes = payload.get("scopes", [])

        if (
            not isinstance(username, str)
            or not username.strip()
            or not isinstance(scopes, list)
            or not all(isinstance(scope, str) for scope in scopes)
        ):
            return None

        return payload

    except (InvalidTokenError, TypeError, ValueError):
        return None
