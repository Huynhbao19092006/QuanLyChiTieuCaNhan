"""Hàm hỗ trợ: định dạng, chuyển đổi dữ liệu API, tải dữ liệu, biểu đồ."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from types import SimpleNamespace

import altair as alt
import pandas as pd
import streamlit as st

from api_client import (
    get_categories_api,
    get_transactions_api,
)


def format_money(value):
    """Định dạng tiền Việt Nam."""
    try:
        return f"{float(value):,.0f} đ"
    except (ValueError, TypeError, InvalidOperation):
        return "0 đ"


def get_user_value(field):
    """Lấy thông tin người dùng."""
    user = st.session_state.get("user")

    if user is None:
        return None

    if isinstance(user, dict):
        return user.get(field)

    return getattr(user, field, None)


def get_user_id():
    return get_user_value("id")


def parse_api_date(value):
    """Chuyển ngày từ API thành datetime.date."""
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    value = str(value)

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).date()
    except ValueError:
        return date.fromisoformat(value[:10])


def normalize_transaction_type(value):
    """Chuẩn hóa loại giao dịch/danh mục về income hoặc expense."""
    normalized = str(value).strip().casefold()
    aliases = {
        "income": "income",
        "thu nhập": "income",
        "thu nhap": "income",
        "expense": "expense",
        "chi tiêu": "expense",
        "chi tieu": "expense",
    }
    return aliases.get(normalized)


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


def get_api_error(result):
    """Lấy thông báo lỗi từ API."""
    if isinstance(result, dict):
        return result.get("detail", str(result))

    return str(result)


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


def category_name(category_id, categories):
    """Tìm tên danh mục theo ID."""
    for category in categories:
        if category.id == category_id:
            return category.name

    return "Không xác định"


def category_label(category):
    """Nhãn hiển thị có ID để phân biệt danh mục trùng tên."""
    category_type_label = (
        "Thu nhập"
        if category.category_type == "income"
        else "Chi tiêu"
    )
    return (
        f"{category.name} · {category_type_label} "
        f"(#{category.id})"
    )


def category_lookup_by_id_and_type(categories):
    """Lập ánh xạ danh mục theo cả ID và loại."""
    return {
        (category.id, category.category_type): category
        for category in categories
    }


def get_category_options(categories, transaction_type=None):
    """Lọc danh mục theo loại giao dịch."""
    if transaction_type is None:
        return categories

    return [
        category
        for category in categories
        if normalize_transaction_type(category.category_type)
        == transaction_type
    ]


def filter_transactions_by_type(transactions, transaction_type):
    """Lọc giao dịch theo loại chuẩn hóa từ API."""
    if transaction_type not in ("income", "expense"):
        raise ValueError("Loại giao dịch không hợp lệ.")

    return [
        item
        for item in transactions
        if normalize_transaction_type(item.transaction_type)
        == transaction_type
    ]


def transaction_dataframe(transactions, categories):
    """Chuyển giao dịch thành DataFrame."""
    rows = []

    for item in transactions:
        rows.append({
            "Ngày": item.transaction_date,
            "Loại": (
                "Thu nhập"
                if item.transaction_type == "income"
                else "Chi tiêu"
            ),
            "Danh mục": category_name(item.category_id, categories),
            "Số tiền": float(item.amount),
            "Mô tả": item.description or "",
        })

    return pd.DataFrame(
        rows,
        columns=["Ngày", "Loại", "Danh mục", "Số tiền", "Mô tả"],
    )


def build_monthly_cashflow_chart(transactions, categories):
    """Tạo biểu đồ cột nhóm thu nhập và chi tiêu theo tháng."""
    df = transaction_dataframe(transactions, categories)
    df["Ngày"] = pd.to_datetime(df["Ngày"], errors="coerce")
    df = df.dropna(subset=["Ngày"])

    if df.empty:
        return None

    df["Tháng"] = df["Ngày"].dt.to_period("M").astype(str)
    monthly = (
        df.groupby(["Tháng", "Loại"], as_index=False)["Số tiền"]
        .sum()
    )
    month_order = sorted(monthly["Tháng"].unique().tolist())

    return (
        alt.Chart(monthly)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(
                "Tháng:N",
                sort=month_order,
                title="Tháng",
            ),
            xOffset=alt.XOffset(
                "Loại:N",
                sort=["Thu nhập", "Chi tiêu"],
            ),
            y=alt.Y(
                "Số tiền:Q",
                title="Số tiền (VNĐ)",
                axis=alt.Axis(format=",.0f"),
            ),
            color=alt.Color(
                "Loại:N",
                title="Loại giao dịch",
                scale=alt.Scale(
                    domain=["Thu nhập", "Chi tiêu"],
                    range=["#0f9d8a", "#e76f51"],
                ),
            ),
            tooltip=[
                alt.Tooltip("Tháng:N", title="Tháng"),
                alt.Tooltip("Loại:N", title="Loại"),
                alt.Tooltip(
                    "Số tiền:Q",
                    title="Số tiền",
                    format=",.0f",
                ),
            ],
        )
        .properties(
            height=330,
            title="Thu nhập và chi tiêu theo tháng",
        )
        .configure_view(stroke=None)
    )


def parse_amount(value):
    """Kiểm tra số tiền hợp lệ."""
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValueError("Số tiền không hợp lệ.")

    if not amount.is_finite():
        raise ValueError("Số tiền không hợp lệ.")

    if amount <= 0:
        raise ValueError("Số tiền phải lớn hơn 0.")

    return amount


def show_page_title(title, description):
    st.title(title)
    st.caption(description)
    st.divider()
