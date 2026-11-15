
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Numeric, CheckConstraint


# ==================================================
# 1. USER - QUẢN LÝ NGƯỜI DÙNG
# ==================================================

class User(SQLModel, table=True):

    __tablename__ = "user"

    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )

    username: str = Field(
        index=True,
        unique=True,
        min_length=3,
        max_length=50
    )

    email: str = Field(
        index=True,
        unique=True,
        max_length=254
    )

    password_hash: str = Field(
        max_length=255
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ==================================================
# 2. CATEGORY - QUẢN LÝ DANH MỤC
# ==================================================

class Category(SQLModel, table=True):

    __tablename__ = "category"

    __table_args__ = (
        CheckConstraint(
            "category_type IN ('income', 'expense')",
            name="ck_category_type"
        ),

        CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_category_name_not_empty"
        ),
    )

    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )

    user_id: int = Field(
        foreign_key="user.id",
        index=True
    )

    name: str = Field(
        min_length=1,
        max_length=100
    )

    category_type: str = Field(
        max_length=10
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ==================================================
# 3. TRANSACTION - QUẢN LÝ GIAO DỊCH
# ==================================================

class Transaction(SQLModel, table=True):

    __tablename__ = "transaction"

    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('income', 'expense')",
            name="ck_transaction_type"
        ),

        CheckConstraint(
            "amount > 0",
            name="ck_transaction_amount_positive"
        ),

        CheckConstraint(
            "length(description) <= 500",
            name="ck_transaction_description_length"
        ),
    )

    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )

    user_id: int = Field(
        foreign_key="user.id",
        index=True
    )

    category_id: int = Field(
        foreign_key="category.id",
        index=True
    )

    transaction_type: str = Field(
        max_length=10
    )

    amount: Decimal = Field(
        sa_column=Column(
            Numeric(18, 2),
            nullable=False
        )
    )

    description: str = Field(
        default="",
        max_length=500
    )

    transaction_date: date = Field(
        default_factory=date.today,
        index=True
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
