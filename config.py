
import os
import secrets
from pathlib import Path

# Thư mục gốc của dự án
BASE_DIR = Path(__file__).resolve().parent

# Tạo SECRET_KEY ổn định cho môi trường phát triển
def get_secret_key():
    env_key = os.getenv("SECRET_KEY")

    if env_key:
        return env_key

    key_file = BASE_DIR / ".secret_key"

    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()

    new_key = secrets.token_urlsafe(48)
    key_file.write_text(new_key, encoding="utf-8")

    return new_key


# Cấu hình JWT
SECRET_KEY = get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Cấu hình OAuth2 Scopes
OAUTH2_SCOPES = {
    "me": "Truy cập thông tin tài khoản cá nhân",
    "transactions": "Quản lý giao dịch cá nhân",
    "categories": "Quản lý danh mục cá nhân",
    "admin": "Quyền quản trị hệ thống"
}
