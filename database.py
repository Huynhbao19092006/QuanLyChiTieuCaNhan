
from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine

# Xac dinh duong dan database
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Tao thu muc data neu chua ton tai
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'expenses.db'}"

# Tao ket noi SQLite
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)


# Khoi tao cac bang trong database
def create_db_and_tables():
    from models import User, Category, Transaction

    SQLModel.metadata.create_all(engine)


# Tao session lam viec voi database
def get_session():
    return Session(engine)
