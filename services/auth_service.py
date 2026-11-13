
from sqlmodel import Session, select

from models import User
from auth import hash_password, verify_password


# ==============================
# CHỨC NĂNG ĐĂNG KÝ TÀI KHOẢN
# ==============================
def register_user(
    session: Session,
    username: str,
    email: str,
    password: str
):
    username = username.strip()
    email = email.strip().lower()

    if not username or not email or not password:
        return False, "Vui lòng nhập đầy đủ thông tin."

    if len(password) < 8:
        return False, "Mật khẩu phải có ít nhất 8 ký tự."

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


# ==============================
# CHỨC NĂNG ĐĂNG NHẬP TÀI KHOẢN
# ==============================
def login_user(
    session: Session,
    username: str,
    password: str
):
    username = username.strip()

    if not username or not password:
        return False, "Vui lòng nhập đầy đủ thông tin."

    user = session.exec(
        select(User).where(User.username == username)
    ).first()

    if user is None:
        return False, "Tên đăng nhập hoặc mật khẩu không chính xác."

    if not verify_password(password, user.password_hash):
        return False, "Tên đăng nhập hoặc mật khẩu không chính xác."

    return True, user
