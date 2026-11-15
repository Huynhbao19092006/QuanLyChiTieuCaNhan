
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from models import Category


def normalize_name(name: str):
    return " ".join((name or "").split())


def get_categories(session: Session, user_id: int):
    statement = (
        select(Category)
        .where(Category.user_id == user_id)
        .order_by(Category.name)
    )

    return session.exec(statement).all()


def add_category(
    session: Session,
    user_id: int,
    name: str,
    category_type: str
):
    name = normalize_name(name)

    if not name:
        return False, "Vui lòng nhập tên danh mục."

    if len(name) > 100:
        return False, "Tên danh mục không được vượt quá 100 ký tự."

    if category_type not in ["income", "expense"]:
        return False, "Loại danh mục không hợp lệ."

    try:
        existing = session.exec(
            select(Category).where(
                Category.user_id == user_id,
                Category.name.ilike(name),
                Category.category_type == category_type
            )
        ).first()

        if existing:
            return False, "Danh mục đã tồn tại."

        category = Category(
            user_id=user_id,
            name=name,
            category_type=category_type
        )

        session.add(category)
        session.commit()
        session.refresh(category)

        return True, "Thêm danh mục thành công!"

    except IntegrityError:
        session.rollback()
        return False, "Danh mục đã tồn tại."

    except SQLAlchemyError:
        session.rollback()
        return False, "Không thể thêm danh mục. Vui lòng thử lại."


def delete_category(
    session: Session,
    user_id: int,
    category_id: int
):
    try:
        category = session.exec(
            select(Category).where(
                Category.id == category_id,
                Category.user_id == user_id
            )
        ).first()

        if category is None:
            return False, "Không tìm thấy danh mục."

        session.delete(category)
        session.commit()

        return True, "Xóa danh mục thành công!"

    except IntegrityError:
        session.rollback()
        return False, "Không thể xóa danh mục vì đang có giao dịch sử dụng."

    except SQLAlchemyError:
        session.rollback()
        return False, "Không thể xóa danh mục. Vui lòng thử lại."
