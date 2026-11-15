
import re

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from models import User
from auth import hash_password, verify_password


# =====================================================
# 1. ĐĂNG KÝ TÀI KHOẢN
# =====================================================

def register_user(
    session: Session,
    username: str,
    email: str,
    password: str
):
    username = (username or "").strip()
    email = (email or "").strip().lower()

    if not username or not email or not password:
        return False, "Vui lòng nhập đầy đủ thông tin."

    if len(username) < 3:
        return False, "Tên đăng nhập phải có ít nhất 3 ký tự."

    if len(username) > 50:
        return False, "Tên đăng nhập không được vượt quá 50 ký tự."

    if not re.fullmatch(r"[A-Za-z0-9_.-]+", username):
        return False, (
            "Tên đăng nhập chỉ được chứa chữ, số, "
            "dấu chấm, gạch ngang và gạch dưới."
        )

    email_pattern = r"[^@\s]+@[^@\s]+\.[^@\s]+"

    if len(email) > 254 or not re.fullmatch(email_pattern, email):
        return False, "Địa chỉ email không hợp lệ."

    if len(password) < 8:
        return False, "Mật khẩu phải có ít nhất 8 ký tự."

    if len(password) > 128:
        return False, "Mật khẩu không được vượt quá 128 ký tự."

    try:
        existing_user = session.exec(
            select(User).where(User.username == username)
        ).first()

        if existing_user:
            return False, "Tên đăng nhập đã tồn tại."

        existing_email = session.exec(
            select(User).where(User.email == email)
        ).first()

        if existing_email:
            return False, "Email đã được sử dụng."

        new_user = User(
            username=username,
            email=email,
            password_hash=hash_password(password)
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return True, "Đăng ký tài khoản thành công!"

    except IntegrityError:
        session.rollback()
        return False, "Tên đăng nhập hoặc email đã được sử dụng."

    except SQLAlchemyError:
        session.rollback()
        return False, "Không thể lưu tài khoản. Vui lòng thử lại."


# =====================================================
# 2. ĐĂNG NHẬP
# =====================================================

def login_user(
    session: Session,
    username: str,
    password: str
):
    username = (username or "").strip()

    if not username or not password:
        return False, "Vui lòng nhập đầy đủ thông tin."

    try:
        user = session.exec(
            select(User).where(User.username == username)
        ).first()

        if user is None:
            return False, "Tên đăng nhập hoặc mật khẩu không chính xác."

        if not verify_password(password, user.password_hash):
            return False, "Tên đăng nhập hoặc mật khẩu không chính xác."

        return True, user

    except SQLAlchemyError:
        session.rollback()
        return False, "Không thể đăng nhập. Vui lòng thử lại."
