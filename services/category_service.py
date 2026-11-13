
from sqlmodel import Session, select

from models import Category


def get_categories(session: Session, user_id: int):
    statement = select(Category).where(
        Category.user_id == user_id
    )
    return session.exec(statement).all()


def add_category(
    session: Session,
    user_id: int,
    name: str,
    category_type: str
):
    name = name.strip()

    if not name:
        return False, "Vui lòng nhập tên danh mục."

    if category_type not in ["income", "expense"]:
        return False, "Loại danh mục không hợp lệ."

    existing = session.exec(
        select(Category).where(
            Category.user_id == user_id,
            Category.name == name,
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


def delete_category(
    session: Session,
    user_id: int,
    category_id: int
):
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
