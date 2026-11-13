
from datetime import date
from decimal import Decimal, InvalidOperation

from sqlmodel import Session, select

from models import Transaction, Category


# ==========================================
# KIỂM TRA DANH MỤC THUỘC VỀ NGƯỜI DÙNG
# ==========================================
def check_category(session, user_id, category_id, transaction_type):
    category = session.exec(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
            Category.category_type == transaction_type
        )
    ).first()

    return category


# ==========================================
# LẤY DANH SÁCH GIAO DỊCH
# ==========================================
def get_transactions(session: Session, user_id: int):
    statement = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date.desc())
    )

    return session.exec(statement).all()


# ==========================================
# THÊM GIAO DỊCH
# ==========================================
def add_transaction(
    session: Session,
    user_id: int,
    category_id: int,
    transaction_type: str,
    amount,
    description: str = "",
    transaction_date: date = None
):
    if transaction_type not in ["income", "expense"]:
        return False, "Loại giao dịch không hợp lệ."

    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        return False, "Số tiền không hợp lệ."

    if not amount.is_finite() or amount <= 0:
        return False, "Số tiền phải lớn hơn 0."

    category = check_category(
        session, user_id, category_id, transaction_type
    )

    if category is None:
        return False, "Danh mục không hợp lệ."

    transaction = Transaction(
        user_id=user_id,
        category_id=category_id,
        transaction_type=transaction_type,
        amount=amount,
        description=description.strip(),
        transaction_date=transaction_date or date.today()
    )

    session.add(transaction)
    session.commit()
    session.refresh(transaction)

    return True, "Thêm giao dịch thành công!"


# ==========================================
# CẬP NHẬT GIAO DỊCH
# ==========================================
def update_transaction(
    session: Session,
    user_id: int,
    transaction_id: int,
    category_id: int,
    transaction_type: str,
    amount,
    description: str = "",
    transaction_date: date = None
):
    transaction = session.exec(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        )
    ).first()

    if transaction is None:
        return False, "Không tìm thấy giao dịch."

    if transaction_type not in ["income", "expense"]:
        return False, "Loại giao dịch không hợp lệ."

    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        return False, "Số tiền không hợp lệ."

    if not amount.is_finite() or amount <= 0:
        return False, "Số tiền phải lớn hơn 0."

    category = check_category(
        session, user_id, category_id, transaction_type
    )

    if category is None:
        return False, "Danh mục không hợp lệ."

    transaction.category_id = category_id
    transaction.transaction_type = transaction_type
    transaction.amount = amount
    transaction.description = description.strip()

    if transaction_date is not None:
        transaction.transaction_date = transaction_date

    session.add(transaction)
    session.commit()
    session.refresh(transaction)

    return True, "Cập nhật giao dịch thành công!"


# ==========================================
# XÓA GIAO DỊCH
# ==========================================
def delete_transaction(
    session: Session,
    user_id: int,
    transaction_id: int
):
    transaction = session.exec(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        )
    ).first()

    if transaction is None:
        return False, "Không tìm thấy giao dịch."

    session.delete(transaction)
    session.commit()

    return True, "Xóa giao dịch thành công!"
