from types import SimpleNamespace
from decimal import Decimal, InvalidOperation

import streamlit as st

from api_client import (
    get_categories_api,
    get_transactions_api,
)
from utils.formatters import parse_api_date
from utils.validators import normalize_transaction_type


def convert_category(item):
    """Chuyển dữ liệu danh mục API thành object."""
    category_type = normalize_transaction_type(
        item["category_type"]
    )
    if category_type is None:
        raise ValueError(
            f"Loại danh mục không hợp lệ: {item['category_type']}"
        )

    return SimpleNamespace(
        id=int(item["id"]),
        name=str(item["name"]),
        category_type=category_type,
    )

def convert_transaction(item):
    """Chuyển dữ liệu giao dịch API thành object."""
    transaction_type = normalize_transaction_type(
        item["transaction_type"]
    )
    if transaction_type is None:
        raise ValueError(
            f"Loại giao dịch không hợp lệ: {item['transaction_type']}"
        )

    return SimpleNamespace(
        id=int(item["id"]),
        category_id=int(item["category_id"]),
        transaction_type=transaction_type,
        amount=Decimal(str(item["amount"])),
        description=item.get("description") or "",
        transaction_date=parse_api_date(item["transaction_date"]),
    )

def load_data():
    """
    Lấy giao dịch và danh mục thông qua FastAPI.
    Không truy cập SQLite trực tiếp từ Streamlit.
    """
    if not st.session_state.get("access_token"):
        return [], []

    raw_transactions = get_transactions_api()
    raw_categories = get_categories_api()

    transaction_error = None
    category_error = None

    if raw_transactions is None:
        transaction_error = (
            "Không thể tải giao dịch từ API. "
            "Vui lòng kiểm tra kết nối và đăng nhập lại nếu cần."
        )
        transactions = []
    else:
        try:
            transactions = [
                convert_transaction(item)
                for item in raw_transactions
            ]
        except (KeyError, TypeError, ValueError, InvalidOperation) as error:
            transaction_error = f"Dữ liệu giao dịch không hợp lệ: {error}"
            transactions = []

    if raw_categories is None:
        category_error = (
            "Không thể tải danh mục từ API. "
            "Không thể xác định danh mục phù hợp cho giao dịch."
        )
        categories = []
    else:
        try:
            categories = [
                convert_category(item)
                for item in raw_categories
            ]
        except (KeyError, TypeError, ValueError, InvalidOperation) as error:
            category_error = f"Dữ liệu danh mục không hợp lệ: {error}"
            categories = []

    st.session_state["transactions"] = transactions
    st.session_state["categories"] = categories
    st.session_state["category_counts"] = {
        "income": sum(
            item.category_type == "income"
            for item in categories
        ),
        "expense": sum(
            item.category_type == "expense"
            for item in categories
        ),
    }
    st.session_state["transaction_load_error"] = transaction_error
    st.session_state["category_load_error"] = category_error

    if transaction_error:
        st.error(transaction_error)
    if category_error:
        st.error(category_error)

    return transactions, categories
