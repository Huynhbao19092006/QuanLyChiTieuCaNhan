
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field


# ==============================
# MODEL USER - QUẢN LÝ NGƯỜI DÙNG
# ==============================
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str
    password_hash: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ==============================
# MODEL CATEGORY - QUẢN LÝ DANH MỤC
# ==============================
class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    category_type: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ==============================
# MODEL TRANSACTION - QUẢN LÝ GIAO DỊCH
# ==============================
class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    category_id: int = Field(foreign_key="category.id")
    transaction_type: str
    amount: Decimal
    description: str = ""
    transaction_date: date = Field(default_factory=date.today)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
