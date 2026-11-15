
import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel, Session, create_engine


# ==================================================
# 1. XÁC ĐỊNH THƯ MỤC DỰ ÁN
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env", override=False)


# ==================================================
# 2. CẤU HÌNH LOG
# ==================================================

logger = logging.getLogger(__name__)


# ==================================================
# 3. CẤU HÌNH DATABASE
# ==================================================

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development"
).strip().lower()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    ""
).strip()

if not DATABASE_URL:

    if ENVIRONMENT == "production":
        raise RuntimeError(
            "Chưa cấu hình DATABASE_URL. "
            "Không thể sử dụng SQLite trong production."
        )

    DATABASE_URL = f"sqlite:///{DATA_DIR / 'expenses.db'}"


# Chuẩn hóa PostgreSQL sang psycopg 3
if DATABASE_URL.startswith("postgres://"):

    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+psycopg://",
        1
    )

elif DATABASE_URL.startswith("postgresql://"):

    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )


# ==================================================
# 4. TẠO DATABASE ENGINE
# ==================================================

connect_args = {}

engine_options = {
    "echo": False,
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite"):

    connect_args = {
        "check_same_thread": False
    }

    engine_options["connect_args"] = connect_args

else:

    engine_options["pool_recycle"] = 1800
    engine_options["pool_size"] = 5
    engine_options["max_overflow"] = 5

engine = create_engine(
    DATABASE_URL,
    **engine_options
)


# ==================================================
# 5. KIỂM TRA KẾT NỐI DATABASE
# ==================================================

def check_database_connection():

    try:

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True, "Kết nối database thành công."

    except SQLAlchemyError:

        logger.exception(
            "Không thể kết nối database."
        )

        return False, (
            "Không thể kết nối database. "
            "Hãy kiểm tra cấu hình."
        )


# ==================================================
# 6. KHỞI TẠO CÁC BẢNG
# ==================================================

def create_db_and_tables():

    from models import User, Category, Transaction

    success, message = check_database_connection()

    if not success:
        raise RuntimeError(message)

    SQLModel.metadata.create_all(engine)

    logger.info(
        "Khởi tạo database thành công."
    )


# ==================================================
# 7. QUẢN LÝ SESSION
# ==================================================

def get_session():

    with Session(engine) as session:
        yield session
