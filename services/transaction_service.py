
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError

from models import Transaction, Category


# =====================================================
# 1. KIỂM TRA DANH MỤC
# =====================================================

def check_category(
    session: Session,
    user_id: int,
    category_id: int,
    transaction_type: str
):
    return session.exec(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
            Category.category_type == transaction_type
        )
    ).first()


# =====================================================
# 2. KIỂM TRA SỐ TIỀN
# =====================================================

def validate_amount(amount):

    try:
        amount = Decimal(str(amount))

    except (InvalidOperation, ValueError, TypeError):
        return None

    if not amount.is_finite() or amount <= 0:
        return None

    if amount.as_tuple().exponent < -2:
        return None

    if amount > Decimal("9999999999999999.99"):
        return None

    return amount


# =====================================================
# 3. KIỂM TRA MÔ TẢ
# =====================================================

def validate_description(description):

    if description is None:
        description = ""

    if not isinstance(description, str):
        return None

    description = description.strip()

    if len(description) > 500:
        return None

    return description


# =====================================================
# 4. KIỂM TRA NGÀY GIAO DỊCH
# =====================================================

def validate_transaction_date(transaction_date):

    if transaction_date is None:
        return date.today()

    if (
        not isinstance(transaction_date, date)
        or isinstance(transaction_date, datetime)
    ):
        return None

    return transaction_date


# =====================================================
# 5. LẤY DANH SÁCH GIAO DỊCH
# =====================================================

def get_transactions(
    session: Session,
    user_id: int,
    limit: int = 100,
    offset: int = 0
):

    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))

    statement = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc()
        )
        .offset(offset)
        .limit(limit)
    )

    return session.exec(statement).all()


# =====================================================
# 6. THÊM GIAO DỊCH
# =====================================================

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

    amount = validate_amount(amount)

    if amount is None:
        return False, "Số tiền không hợp lệ."

    description = validate_description(description)

    if description is None:
        return False, "Mô tả không được vượt quá 500 ký tự."

    transaction_date = validate_transaction_date(
        transaction_date
    )

    if transaction_date is None:
        return False, "Ngày giao dịch không hợp lệ."

    category = check_category(
        session,
        user_id,
        category_id,
        transaction_type
    )

    if category is None:
        return False, "Danh mục không hợp lệ."

    try:

        transaction = Transaction(
            user_id=user_id,
            category_id=category_id,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            transaction_date=transaction_date
        )

        session.add(transaction)
        session.commit()
        session.refresh(transaction)

        return True, "Thêm giao dịch thành công!"

    except SQLAlchemyError:

        session.rollback()

        return False, "Không thể thêm giao dịch. Vui lòng thử lại."


# =====================================================
# 7. CẬP NHẬT GIAO DỊCH
# =====================================================

def update_transaction(
    session: Session,
    user_id: int,
    transaction_id: int,
    category_id=None,
    transaction_type=None,
    amount=None,
    description=None,
    transaction_date=None
):

    try:

        transaction = session.exec(
            select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id
            )
        ).first()

        if transaction is None:
            return False, "Không tìm thấy giao dịch."

        # Giữ giá trị cũ nếu không gửi trường mới
        new_category_id = (
            category_id
            if category_id is not None
            else transaction.category_id
        )

        new_type = (
            transaction_type
            if transaction_type is not None
            else transaction.transaction_type
        )

        new_amount = (
            validate_amount(amount)
            if amount is not None
            else transaction.amount
        )

        new_description = (
            validate_description(description)
            if description is not None
            else transaction.description
        )

        new_date = (
            validate_transaction_date(transaction_date)
            if transaction_date is not None
            else transaction.transaction_date
        )

        if new_type not in ["income", "expense"]:
            return False, "Loại giao dịch không hợp lệ."

        if new_amount is None:
            return False, "Số tiền không hợp lệ."

        if new_description is None:
            return False, "Mô tả không hợp lệ."

        if new_date is None:
            return False, "Ngày giao dịch không hợp lệ."

        category = check_category(
            session,
            user_id,
            new_category_id,
            new_type
        )

        if category is None:
            return False, "Danh mục không hợp lệ."

        transaction.category_id = new_category_id
        transaction.transaction_type = new_type
        transaction.amount = new_amount
        transaction.description = new_description
        transaction.transaction_date = new_date

        session.add(transaction)
        session.commit()
        session.refresh(transaction)

        return True, "Cập nhật giao dịch thành công!"

    except SQLAlchemyError:

        session.rollback()

        return False, "Không thể cập nhật giao dịch. Vui lòng thử lại."


# =====================================================
# 8. XÓA GIAO DỊCH
# =====================================================

def delete_transaction(
    session: Session,
    user_id: int,
    transaction_id: int
):

    try:

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

    except SQLAlchemyError:

        session.rollback()

        return False, "Không thể xóa giao dịch. Vui lòng thử lại."
