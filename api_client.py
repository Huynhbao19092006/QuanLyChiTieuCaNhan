
import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"


def register(username, email, password):
    """Đăng ký tài khoản mới."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/users/",
            json={
                "username": username,
                "email": email,
                "password": password
            },
            timeout=10
        )

        if response.status_code == 200:
            return True, response.json()

        return False, response.json().get("detail", "Đăng ký thất bại.")

    except requests.RequestException:
        return False, "Không thể kết nối đến máy chủ FastAPI."


def login(username, password, scopes=None):
    """Đăng nhập và nhận JWT."""
    if scopes is None:
        scopes = ["me", "transactions", "categories"]

    try:
        response = requests.post(
            f"{API_BASE_URL}/token",
            data={
                "username": username,
                "password": password,
                "scope": " ".join(scopes)
            },
            timeout=10
        )

        if response.status_code == 200:
            token_data = response.json()

            st.session_state["access_token"] = token_data["access_token"]
            st.session_state["token_type"] = token_data["token_type"]

            return True, "Đăng nhập thành công."

        return False, response.json().get(
            "detail", "Tên đăng nhập hoặc mật khẩu không chính xác."
        )

    except requests.RequestException:
        return False, "Không thể kết nối đến máy chủ FastAPI."


def get_headers():
    """Tạo Header chứa JWT."""
    token = st.session_state.get("access_token")

    if not token:
        return {}

    return {
        "Authorization": f"Bearer {token}"
    }


def get_current_user():
    """Lấy thông tin người dùng hiện tại."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/users/me",
            headers=get_headers(),
            timeout=10
        )

        if response.status_code == 200:
            return response.json()

        return None

    except requests.RequestException:
        return None


def get_transactions_api():
    """Lấy danh sách giao dịch từ FastAPI."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/transactions",
            headers=get_headers(),
            timeout=10
        )

        if response.status_code == 200:
            return response.json()

        return None

    except requests.RequestException:
        return None


def logout():
    """Đăng xuất khỏi phiên Streamlit."""
    st.session_state.pop("access_token", None)
    st.session_state.pop("token_type", None)
