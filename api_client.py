
import os
import requests
import streamlit as st

from datetime import date
from decimal import Decimal, InvalidOperation
from dotenv import load_dotenv

# =====================================================
# CẤU HÌNH API
# =====================================================

load_dotenv()

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
).strip().rstrip("/")

# Render Free có thể mất 50 giây hoặc hơn để khởi động.
# 15 giây trước đây có thể khiến yêu cầu đăng nhập bị timeout.
API_TIMEOUT = (15, 90)


# =====================================================
# HÀM HỖ TRỢ
# =====================================================

def get_headers():
    """Tạo Authorization Header chứa JWT."""

    token = st.session_state.get("access_token")

    headers = {
        "Accept": "application/json"
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def _handle_response(response):
    """Xử lý phản hồi chung từ FastAPI."""

    if response.status_code == 401:
        logout()
        return False, "Tên đăng nhập hoặc mật khẩu không đúng, hoặc phiên đăng nhập đã hết hạn."

    try:
        data = response.json()
    except ValueError:
        data = {}

    if response.ok:
        return True, data

    if isinstance(data, dict):
        detail = data.get(
            "detail",
            "Đã xảy ra lỗi từ máy chủ."
        )
    else:
        detail = "Đã xảy ra lỗi từ máy chủ."

    return False, detail


def _request(method, endpoint, **kwargs):
    """Gửi yêu cầu HTTP đến FastAPI."""

    try:
        response = requests.request(
            method=method,
            url=f"{API_BASE_URL}{endpoint}",
            headers=get_headers(),
            timeout=API_TIMEOUT,
            **kwargs
        )

        return _handle_response(response)

    except requests.Timeout:
        return False, (
            "Máy chủ phản hồi quá lâu. "
            "Render có thể đang khởi động lại. "
            "Vui lòng chờ một chút rồi thử lại."
        )

    except requests.ConnectionError:
        return False, (
            "Không thể kết nối đến máy chủ FastAPI. "
            "Vui lòng kiểm tra API_BASE_URL và trạng thái Backend."
        )

    except requests.RequestException as e:
        return False, f"Lỗi gửi yêu cầu đến máy chủ: {str(e)}"


# =====================================================
# 1. ĐĂNG KÝ
# =====================================================

def register(username, email, password):
    username = username.strip()
    email = email.strip()

    if not username or not email or not password:
        return False, "Vui lòng nhập đầy đủ thông tin."

    return _request(
        "POST",
        "/users/",
        json={
            "username": username,
            "email": email,
            "password": password
        }
    )


# =====================================================
# 2. ĐĂNG NHẬP
# =====================================================

def login(username, password, scopes=None):
    username = username.strip()

    if not username or not password:
        return False, "Vui lòng nhập tên đăng nhập và mật khẩu."

    if scopes is None:
        scopes = [
            "me",
            "categories",
            "transactions"
        ]

    try:
        response = requests.post(
            f"{API_BASE_URL}/token",
            data={
                "username": username,
                "password": password,
                "scope": " ".join(scopes)
            },
            headers={
                "Accept": "application/json"
            },
            timeout=API_TIMEOUT
        )

        success, result = _handle_response(response)

        if not success:
            return False, result

        if not isinstance(result, dict):
            return False, "Dữ liệu đăng nhập từ máy chủ không hợp lệ."

        token = result.get("access_token")

        if not token:
            return False, "Máy chủ không trả về Access Token."

        # Lưu JWT vào session của Streamlit.
        st.session_state["access_token"] = token

        st.session_state["token_type"] = result.get(
            "token_type",
            "bearer"
        )

        return True, "Đăng nhập thành công."

    except requests.Timeout:
        return False, (
            "Máy chủ khởi động hoặc phản hồi quá lâu. "
            "Vui lòng chờ rồi thử đăng nhập lại."
        )

    except requests.ConnectionError:
        return False, (
            "Không thể kết nối đến máy chủ FastAPI."
        )

    except requests.RequestException as e:
        return False, f"Lỗi đăng nhập: {str(e)}"


# =====================================================
# 3. THÔNG TIN NGƯỜI DÙNG
# =====================================================

def get_current_user():
    success, result = _request(
        "GET",
        "/users/me"
    )

    return result if success else None


def update_profile_api(email):
    email = email.strip().lower()

    if not email:
        return False, "Email không được để trống."

    return _request(
        "PUT",
        "/users/me",
        json={"email": email},
    )


def change_password_api(current_password, new_password):
    if not current_password or not new_password:
        return False, "Vui lòng nhập đầy đủ mật khẩu."

    return _request(
        "POST",
        "/users/me/change-password",
        json={
            "current_password": current_password,
            "new_password": new_password,
        },
    )


# =====================================================
# 4. QUẢN LÝ DANH MỤC
# =====================================================

def get_categories_api():
    success, result = _request(
        "GET",
        "/categories"
    )

    return result if success else None


def create_category_api(name, category_type):
    name = name.strip()

    if not name:
        return False, "Tên danh mục không được để trống."

    if category_type not in ("income", "expense"):
        return False, "Loại danh mục không hợp lệ."

    return _request(
        "POST",
        "/categories",
        json={
            "name": name,
            "category_type": category_type
        }
    )


def update_category_api(category_id, name, category_type):
    name = name.strip()

    if not name:
        return False, "Tên danh mục không được để trống."

    if category_type not in ("income", "expense"):
        return False, "Loại danh mục không hợp lệ."

    return _request(
        "PUT",
        f"/categories/{int(category_id)}",
        json={
            "name": name,
            "category_type": category_type,
        },
    )


def delete_category_api(category_id):
    return _request(
        "DELETE",
        f"/categories/{int(category_id)}"
    )


# =====================================================
# 5. QUẢN LÝ GIAO DỊCH
# =====================================================

def get_transactions_api():
    success, result = _request(
        "GET",
        "/transactions"
    )

    return result if success else None


def create_transaction_api(
    category_id,
    transaction_type,
    amount,
    description="",
    transaction_date=None
):
    if transaction_type not in ("income", "expense"):
        return False, "Loại giao dịch không hợp lệ."

    try:
        amount = Decimal(str(amount))

        if not amount.is_finite() or amount <= 0:
            return False, "Số tiền phải lớn hơn 0."

    except (InvalidOperation, ValueError):
        return False, "Số tiền không hợp lệ."

    if transaction_date is None:
        transaction_date = date.today()

    payload = {
        "category_id": int(category_id),
        "transaction_type": transaction_type,
        "amount": str(amount),
        "description": str(description).strip(),
        "transaction_date": transaction_date.isoformat()
    }

    return _request(
        "POST",
        "/transactions",
        json=payload
    )


def update_transaction_api(
    transaction_id,
    category_id=None,
    transaction_type=None,
    amount=None,
    description=None,
    transaction_date=None
):
    payload = {}

    if category_id is not None:
        payload["category_id"] = int(category_id)

    if transaction_type is not None:
        if transaction_type not in ("income", "expense"):
            return False, "Loại giao dịch không hợp lệ."

        payload["transaction_type"] = transaction_type

    if amount is not None:
        try:
            amount = Decimal(str(amount))

            if not amount.is_finite() or amount <= 0:
                return False, "Số tiền không hợp lệ."

            payload["amount"] = str(amount)

        except (InvalidOperation, ValueError):
            return False, "Số tiền không hợp lệ."

    if description is not None:
        payload["description"] = str(description).strip()

    if transaction_date is not None:
        payload["transaction_date"] = (
            transaction_date.isoformat()
            if isinstance(transaction_date, date)
            else str(transaction_date)
        )

    if not payload:
        return False, "Không có thông tin nào cần cập nhật."

    return _request(
        "PUT",
        f"/transactions/{int(transaction_id)}",
        json=payload
    )


def delete_transaction_api(transaction_id):
    return _request(
        "DELETE",
        f"/transactions/{int(transaction_id)}"
    )


# =====================================================
# 6. ĐĂNG XUẤT
# =====================================================

def logout():
    st.session_state.pop("access_token", None)
    st.session_state.pop("token_type", None)
    st.session_state.pop("user", None)

    st.session_state["logged_in"] = False
