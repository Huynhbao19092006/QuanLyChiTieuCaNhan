
from datetime import timedelta

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    Security
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
    SecurityScopes
)
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from database import engine, create_db_and_tables
from models import User, Transaction

from auth import (
    oauth2_scheme,
    verify_password,
    hash_password,
    create_access_token,
    decode_access_token
)

from config import ACCESS_TOKEN_EXPIRE_MINUTES

from services.auth_service import register_user
from services.transaction_service import get_transactions


# =====================================================
# 1. KHỞI TẠO FASTAPI
# =====================================================

app = FastAPI(
    title="Personal Expense Management API",
    description="API quản lý chi tiêu cá nhân và xác thực JWT OAuth2",
    version="1.0.0"
)

create_db_and_tables()


# =====================================================
# 2. KẾT NỐI DATABASE
# =====================================================

def get_db():
    with Session(engine) as session:
        yield session


# =====================================================
# 3. SCHEMAS
# =====================================================

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []


# =====================================================
# 4. ĐĂNG KÝ NGƯỜI DÙNG
# =====================================================

@app.post("/users/", response_model=UserRead)
def create_user(
    user_data: UserCreate,
    session: Session = Depends(get_db)
):
    success, result = register_user(
        session,
        user_data.username,
        user_data.email,
        user_data.password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )

    user = session.exec(
        select(User).where(
            User.username == user_data.username.strip()
        )
    ).first()

    return user


# =====================================================
# 5. ĐĂNG NHẬP VÀ CẤP JWT TOKEN
# =====================================================

@app.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_db)
):
    user = session.exec(
        select(User).where(
            User.username == form_data.username
        )
    ).first()

    if (
        user is None
        or not verify_password(
            form_data.password,
            user.password_hash
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Người dùng thông thường không được cấp quyền admin.
    allowed_scopes = {
        "me",
        "transactions",
        "categories"
    }

    if not set(form_data.scopes).issubset(allowed_scopes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scope không hợp lệ."
        )

    access_token_expires = timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    access_token = create_access_token(
        data={
            "sub": user.username,
            "scopes": form_data.scopes
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# =====================================================
# 6. XÁC THỰC NGƯỜI DÙNG TỪ JWT
# =====================================================

def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db)
):
    authenticate_value = "Bearer"

    if security_scopes.scopes:
        authenticate_value = (
            f'Bearer scope="{security_scopes.scope_str}"'
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập.",
        headers={"WWW-Authenticate": authenticate_value}
    )

    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    username = payload.get("sub")
    scopes = payload.get("scopes", [])

    if not username or not isinstance(scopes, list):
        raise credentials_exception

    user = session.exec(
        select(User).where(User.username == username)
    ).first()

    if user is None:
        raise credentials_exception

    token_data = TokenData(
        username=username,
        scopes=scopes
    )

    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không đủ quyền truy cập."
            )

    return user


# =====================================================
# 7. LẤY THÔNG TIN NGƯỜI DÙNG HIỆN TẠI
# =====================================================

@app.get("/users/me", response_model=UserRead)
def read_users_me(
    current_user: User = Security(
        get_current_user,
        scopes=["me"]
    )
):
    return current_user


# =====================================================
# 8. LẤY DANH SÁCH GIAO DỊCH CÓ XÁC THỰC
# =====================================================

@app.get("/transactions")
def read_transactions(
    current_user: User = Security(
        get_current_user,
        scopes=["transactions"]
    ),
    session: Session = Depends(get_db)
):
    transactions = get_transactions(
        session,
        current_user.id
    )

    return [
        {
            "id": item.id,
            "transaction_type": item.transaction_type,
            "amount": float(item.amount),
            "description": item.description,
            "transaction_date": item.transaction_date,
            "category_id": item.category_id
        }
        for item in transactions
    ]


# =====================================================
# 9. KIỂM TRA API
# =====================================================

@app.get("/")
def home():
    return {
        "message": "Personal Expense Management API",
        "status": "running"
    }
