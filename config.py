
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv


# =====================================================
# 1. THƯ MỤC VÀ MÔI TRƯỜNG
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development"
).strip().lower()


# =====================================================
# 2. SECRET KEY
# =====================================================

def get_secret_key():
    env_key = os.getenv("SECRET_KEY", "").strip()

    if env_key:
        if len(env_key) < 32:
            raise ValueError(
                "SECRET_KEY phải có ít nhất 32 ký tự."
            )
        return env_key

    # Production bắt buộc phải khai báo SECRET_KEY
    if ENVIRONMENT == "production":
        raise ValueError(
            "Thiếu SECRET_KEY trong môi trường production."
        )

    # Local: sử dụng khóa lưu trong file
    key_file = BASE_DIR / ".secret_key"

    if key_file.exists():
        key = key_file.read_text(
            encoding="utf-8"
        ).strip()

        if len(key) < 32:
            raise ValueError(
                "Khóa trong .secret_key không hợp lệ."
            )

        return key

    new_key = secrets.token_urlsafe(48)

    key_file.write_text(
        new_key,
        encoding="utf-8"
    )

    return new_key


SECRET_KEY = get_secret_key()


# =====================================================
# 3. JWT
# =====================================================

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "30"
    )
)

if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise ValueError(
        "ACCESS_TOKEN_EXPIRE_MINUTES phải lớn hơn 0."
    )


# =====================================================
# 4. OAUTH2 SCOPES
# =====================================================

OAUTH2_SCOPES = {
    "me": "Truy cập thông tin tài khoản cá nhân",
    "transactions": "Quản lý giao dịch cá nhân",
    "categories": "Quản lý danh mục cá nhân",
    "admin": "Quyền quản trị hệ thống"
}
