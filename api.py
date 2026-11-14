
from datetime import date, timedelta
from decimal import Decimal
from typing import Literal

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    Security,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session, select

from database import engine, create_db_and_tables
from models import User, Category, Transaction

from auth import (
    oauth2_scheme,
    verify_password,
    create_access_token,
    decode_access_token,
)

from config import ACCESS_TOKEN_EXPIRE_MINUTES
from services.auth_service import register_user


# =====================================================
# 1. KHỞI TẠO FASTAPI
# =====================================================

app = FastAPI(
    title="Personal Expense Management API",
    description=(
        "API quản lý chi tiêu cá nhân, "
        "JWT Authentication và OAuth2 Scopes."
    ),
    version="2.0.0",
)

create_db_and_tables()


# =====================================================
# 2. KẾT NỐI DATABASE
# =====================================================

def get_db():
    with Session(engine) as session:
        yield session


# =====================================================
# 3. SCHEMAS - NGƯỜI DÙNG
# =====================================================

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6)


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


# =====================================================
# 4. SCHEMAS - DANH MỤC
# =====================================================

class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category_type: Literal["income", "expense"]


class CategoryRead(BaseModel):
    id: int
    name: str
    category_type: str


# =====================================================
# 5. SCHEMAS - GIAO DỊCH
# =====================================================

class TransactionCreate(BaseModel):
    category_id: int
    transaction_type: Literal["income", "expense"]
    amount: Decimal = Field(gt=0)
    description: str = ""
    transaction_date: date


class TransactionUpdate(BaseModel):
    category_id: int
    transaction_type: Literal["income", "expense"]
    amount: Decimal = Field(gt=0)
    description: str = ""
    transaction_date: date


class TransactionRead(BaseModel):
    id: int
    transaction_type: str
    amount: Decimal
    description: str
    transaction_date: date
    category_id: int


# =====================================================
# 6. ĐĂNG KÝ TÀI KHOẢN
# =====================================================

@app.post(
    "/users/",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def create_user(
    user_data: UserCreate,
    session: Session = Depends(get_db),
):
    username = user_data.username.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Tên đăng nhập không được để trống.",
        )

    success, result = register_user(
        session,
        username,
        user_data.email,
        user_data.password,
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail=result,
        )

    user = session.exec(
        select(User).where(User.username == username)
    ).first()

    if user is None:
        raise HTTPException(
            status_code=500,
            detail="Không thể tạo tài khoản.",
        )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
    }


# =====================================================
# 7. ĐĂNG NHẬP - JWT
# =====================================================

@app.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_db),
):
    user = session.exec(
        select(User).where(
            User.username == form_data.username.strip()
        )
    ).first()

    if (
        user is None
        or not verify_password(
            form_data.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    allowed_scopes = {
        "me",
        "transactions",
        "categories",
    }

    if not set(form_data.scopes).issubset(allowed_scopes):
        raise HTTPException(
            status_code=400,
            detail="Scope không hợp lệ.",
        )

    access_token = create_access_token(
        data={
            "sub": user.username,
            "scopes": form_data.scopes,
        },
        expires_delta=timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# =====================================================
# 8. XÁC THỰC JWT VÀ OAUTH2 SCOPES
# =====================================================

def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db),
):
    authenticate_value = "Bearer"

    if security_scopes.scopes:
        authenticate_value = (
            f'Bearer scope="{security_scopes.scope_str}"'
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập.",
        headers={"WWW-Authenticate": authenticate_value},
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

    for scope in security_scopes.scopes:
        if scope not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có đủ quyền truy cập.",
            )

    return user


# =====================================================
# 9. LẤY THÔNG TIN NGƯỜI DÙNG
# =====================================================

@app.get(
    "/users/me",
    response_model=UserRead,
)
def read_users_me(
    current_user: User = Security(
        get_current_user,
        scopes=["me"],
    ),
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
    }


# =====================================================
# 10. HÀM KIỂM TRA DANH MỤC THUỘC NGƯỜI DÙNG
# =====================================================

def get_owned_category(
    session: Session,
    category_id: int,
    user_id: int,
):
    category = session.exec(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
        )
    ).first()

    return category


# =====================================================
# 11. LẤY DANH SÁCH DANH MỤC
# =====================================================

@app.get(
    "/categories",
    response_model=list[CategoryRead],
)
def read_categories(
    current_user: User = Security(
        get_current_user,
        scopes=["categories"],
    ),
    session: Session = Depends(get_db),
):
    categories = session.exec(
        select(Category)
        .where(Category.user_id == current_user.id)
        .order_by(Category.id.desc())
    ).all()

    return [
        {
            "id": item.id,
            "name": item.name,
            "category_type": item.category_type,
        }
        for item in categories
    ]


# =====================================================
# 12. THÊM DANH MỤC
# =====================================================

@app.post(
    "/categories",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    category_data: CategoryCreate,
    current_user: User = Security(
        get_current_user,
        scopes=["categories"],
    ),
    session: Session = Depends(get_db),
):
    name = category_data.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Tên danh mục không được để trống.",
        )

    existing = session.exec(
        select(Category).where(
            Category.user_id == current_user.id,
            Category.name == name,
            Category.category_type == category_data.category_type,
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Danh mục này đã tồn tại.",
        )

    category = Category(
        user_id=current_user.id,
        name=name,
        category_type=category_data.category_type,
    )

    session.add(category)
    session.commit()
    session.refresh(category)

    return {
        "id": category.id,
        "name": category.name,
        "category_type": category.category_type,
    }


# =====================================================
# 13. XÓA DANH MỤC
# =====================================================

@app.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    current_user: User = Security(
        get_current_user,
        scopes=["categories"],
    ),
    session: Session = Depends(get_db),
):
    category = get_owned_category(
        session,
        category_id,
        current_user.id,
    )

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy danh mục.",
        )

    linked_transaction = session.exec(
        select(Transaction).where(
            Transaction.category_id == category_id,
            Transaction.user_id == current_user.id,
        )
    ).first()

    if linked_transaction:
        raise HTTPException(
            status_code=400,
            detail=(
                "Không thể xóa danh mục đang có giao dịch. "
                "Hãy chuyển hoặc xóa các giao dịch liên quan trước."
            ),
        )

    session.delete(category)
    session.commit()

    return {
        "message": "Xóa danh mục thành công."
    }


# =====================================================
# 14. LẤY DANH SÁCH GIAO DỊCH
# =====================================================

@app.get(
    "/transactions",
    response_model=list[TransactionRead],
)
def read_transactions(
    current_user: User = Security(
        get_current_user,
        scopes=["transactions"],
    ),
    session: Session = Depends(get_db),
):
    transactions = session.exec(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.transaction_date.desc())
    ).all()

    return [
        {
            "id": item.id,
            "transaction_type": item.transaction_type,
            "amount": item.amount,
            "description": item.description or "",
            "transaction_date": item.transaction_date,
            "category_id": item.category_id,
        }
        for item in transactions
    ]


# =====================================================
# 15. THÊM GIAO DỊCH
# =====================================================

@app.post(
    "/transactions",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Security(
        get_current_user,
        scopes=["transactions"],
    ),
    session: Session = Depends(get_db),
):
    category = get_owned_category(
        session,
        transaction_data.category_id,
        current_user.id,
    )

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Danh mục không tồn tại hoặc không thuộc tài khoản.",
        )

    if category.category_type != transaction_data.transaction_type:
        raise HTTPException(
            status_code=400,
            detail="Loại giao dịch không khớp với danh mục.",
        )

    transaction = Transaction(
        user_id=current_user.id,
        category_id=transaction_data.category_id,
        transaction_type=transaction_data.transaction_type,
        amount=transaction_data.amount,
        description=transaction_data.description.strip(),
        transaction_date=transaction_data.transaction_date,
    )

    session.add(transaction)
    session.commit()
    session.refresh(transaction)

    return {
        "id": transaction.id,
        "transaction_type": transaction.transaction_type,
        "amount": transaction.amount,
        "description": transaction.description or "",
        "transaction_date": transaction.transaction_date,
        "category_id": transaction.category_id,
    }


# =====================================================
# 16. SỬA GIAO DỊCH
# =====================================================

@app.put(
    "/transactions/{transaction_id}",
    response_model=TransactionRead,
)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    current_user: User = Security(
        get_current_user,
        scopes=["transactions"],
    ),
    session: Session = Depends(get_db),
):
    transaction = session.exec(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
        )
    ).first()

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy giao dịch.",
        )

    category = get_owned_category(
        session,
        transaction_data.category_id,
        current_user.id,
    )

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Danh mục không tồn tại hoặc không thuộc tài khoản.",
        )

    if category.category_type != transaction_data.transaction_type:
        raise HTTPException(
            status_code=400,
            detail="Loại giao dịch không khớp với danh mục.",
        )

    transaction.category_id = transaction_data.category_id
    transaction.transaction_type = transaction_data.transaction_type
    transaction.amount = transaction_data.amount
    transaction.description = transaction_data.description.strip()
    transaction.transaction_date = transaction_data.transaction_date

    session.add(transaction)
    session.commit()
    session.refresh(transaction)

    return {
        "id": transaction.id,
        "transaction_type": transaction.transaction_type,
        "amount": transaction.amount,
        "description": transaction.description or "",
        "transaction_date": transaction.transaction_date,
        "category_id": transaction.category_id,
    }


# =====================================================
# 17. XÓA GIAO DỊCH
# =====================================================

@app.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    current_user: User = Security(
        get_current_user,
        scopes=["transactions"],
    ),
    session: Session = Depends(get_db),
):
    transaction = session.exec(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
        )
    ).first()

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy giao dịch.",
        )

    session.delete(transaction)
    session.commit()

    return {
        "message": "Xóa giao dịch thành công."
    }


# =====================================================
# 18. KIỂM TRA API
# =====================================================

@app.get("/")
def home():
    return {
        "message": "Personal Expense Management API",
        "status": "running",
        "version": "2.0.0",
    }
