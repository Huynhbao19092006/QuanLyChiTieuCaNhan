
import html
import re
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO, StringIO
from types import SimpleNamespace

import altair as alt
import pandas as pd
import streamlit as st

from api_client import (
    register as api_register,
    login as api_login,
    get_current_user,
    update_profile_api,
    change_password_api,
    logout as api_logout,
    get_categories_api,
    create_category_api,
    update_category_api,
    delete_category_api,
    get_transactions_api,
    create_transaction_api,
    update_transaction_api,
    delete_transaction_api,
)


# =========================================================
# 1. CẤU HÌNH GIAO DIỆN VÀ CSS
# =========================================================

st.set_page_config(
    page_title="Quản lý chi tiêu cá nhân",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
STYLES_DIR = BASE_DIR / "styles"

PAGE_STYLES = {
    "Tổng quan": "dashboard.css",
    "Giao dịch": "transactions.css",
    "Thu nhập": "income.css",
    "Chi tiêu": "expense.css",
    "Danh mục": "categories.css",
    "Thống kê": "statistics.css",
    "Xuất dữ liệu": "export.css",
    "Hồ sơ cá nhân": "profile.css",
}


def load_css(extra_styles=None):
    """Nạp CSS dùng chung và CSS của màn hình hiện tại."""
    style_files = ["style.css"]

    if extra_styles:
        style_files.extend(extra_styles)

    for style_file in style_files:
        style_path = STYLES_DIR / style_file

        if not style_path.exists():
            st.warning(f"Không tìm thấy file styles/{style_file}")
            continue

        try:
            css = style_path.read_text(encoding="utf-8")
        except OSError as error:
            st.error(
                f"Không thể đọc file styles/{style_file}: {error}"
            )
            continue

        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True,
        )


def _render_notification(kind, message):
    renderers = {
        "success": st.success,
        "error": st.error,
        "warning": st.warning,
        "info": st.info,
    }
    renderers.get(kind, st.info)(message)


def queue_notification(kind, message):
    """Lưu thông báo để hiển thị đúng một lần sau lần rerun kế tiếp."""
    notifications = st.session_state.setdefault(
        "flash_notifications",
        [],
    )
    notifications.append({
        "kind": kind,
        "message": message,
    })


def show_notification(kind, message, persist=False):
    """Hiển thị ngay hoặc giữ thông báo qua lần rerun."""
    if persist:
        queue_notification(kind, message)
    else:
        _render_notification(kind, message)


def flush_notifications():
    """Hiển thị rồi xóa các thông báo đã chờ."""
    notifications = st.session_state.pop(
        "flash_notifications",
        [],
    )
    for notification in notifications:
        _render_notification(
            notification["kind"],
            notification["message"],
        )


# =========================================================
# 2. KHỞI TẠO SESSION
# =========================================================

if "user" not in st.session_state:
    st.session_state.user = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "access_token" not in st.session_state:
    st.session_state.access_token = None


# Khôi phục thông tin người dùng khi tải lại trang
if st.session_state.access_token and not st.session_state.user:
    try:
        current_user = get_current_user()

        if current_user:
            st.session_state.user = current_user
            st.session_state.logged_in = True
        else:
            api_logout()
            st.session_state.user = None
            st.session_state.logged_in = False
            st.session_state.access_token = None
    except Exception:
        api_logout()
        st.session_state.user = None
        st.session_state.logged_in = False
        st.session_state.access_token = None


if st.session_state.logged_in:
    current_page = st.session_state.get(
        "main_navigation",
        "Tổng quan",
    )
    page_style = PAGE_STYLES.get(current_page)
    load_css([page_style] if page_style else [])
else:
    load_css(["auth.css"])

flush_notifications()


# =========================================================
# 3. HÀM HỖ TRỢ
# =========================================================

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


def convert_category(item):
    """Chuyển dữ liệu danh mục API thành object."""
    return SimpleNamespace(
        id=int(item["id"]),
        name=str(item["name"]),
        category_type=str(item["category_type"]),
    )


def convert_transaction(item):
    """Chuyển dữ liệu giao dịch API thành object."""
    return SimpleNamespace(
        id=int(item["id"]),
        category_id=int(item["category_id"]),
        transaction_type=str(item["transaction_type"]),
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


def get_category_options(categories, transaction_type=None):
    """Lọc danh mục theo loại giao dịch."""
    if transaction_type is None:
        return categories

    return [
        category
        for category in categories
        if category.category_type == transaction_type
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


# =========================================================
# 4. ĐĂNG NHẬP VÀ ĐĂNG KÝ
# =========================================================

def show_auth_page():
    left, right = st.columns([0.9, 1.1], gap="large")

    with left:
        st.markdown(
            """
            <div class="auth-showcase">
                <div class="auth-logo">💳</div>
                <p class="auth-eyebrow">PERSONAL FINANCE</p>
                <h1>Kiểm soát chi tiêu,<br>làm chủ tương lai.</h1>
                <p class="auth-lead">
                    Theo dõi thu nhập, chi tiêu và mục tiêu tài chính
                    trong một không gian rõ ràng, riêng tư.
                </p>
                <div class="auth-benefits">
                    <div><span>✓</span> Quản lý giao dịch tập trung</div>
                    <div><span>✓</span> Phân tích tài chính trực quan</div>
                    <div><span>✓</span> Dữ liệu cá nhân an toàn</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        tab_login, tab_register = st.tabs([
            "Đăng nhập",
            "Đăng ký",
        ])

        with tab_login:
            st.subheader("Chào mừng trở lại")
            st.caption("Đăng nhập để tiếp tục quản lý tài chính.")

            username = st.text_input(
                "Tên đăng nhập",
                key="login_username",
                placeholder="Nhập tên đăng nhập",
            )
            password = st.text_input(
                "Mật khẩu",
                type="password",
                key="login_password",
                placeholder="Nhập mật khẩu",
            )

            if st.button(
                "Đăng nhập",
                type="primary",
                width="stretch",
            ):
                if not username.strip() or not password:
                    st.warning(
                        "Vui lòng nhập tên đăng nhập và mật khẩu."
                    )
                else:
                    try:
                        api_logout()
                        success, message = api_login(
                            username.strip(),
                            password,
                        )

                        if success:
                            current_user = get_current_user()

                            if current_user:
                                st.session_state.user = current_user
                                st.session_state.logged_in = True
                                queue_notification(
                                    "success",
                                    "Đăng nhập thành công!",
                                )
                                st.rerun()
                            else:
                                api_logout()
                                st.session_state.user = None
                                st.session_state.logged_in = False
                                st.error(
                                    "Không lấy được thông tin người dùng. "
                                    "Vui lòng thử lại."
                                )
                        else:
                            st.error(get_api_error(message))

                    except Exception as error:
                        st.error(f"Không thể đăng nhập: {error}")

        with tab_register:
            st.subheader("Tạo tài khoản mới")
            st.caption("Đăng ký để bắt đầu sử dụng hệ thống.")

            new_username = st.text_input(
                "Tên đăng nhập",
                key="register_username",
                placeholder="Nhập tên đăng nhập",
            )
            new_email = st.text_input(
                "Email",
                key="register_email",
                placeholder="Nhập email",
            )
            new_password = st.text_input(
                "Mật khẩu",
                type="password",
                key="register_password",
                placeholder="Tạo mật khẩu",
            )
            confirm_password = st.text_input(
                "Xác nhận mật khẩu",
                type="password",
                key="confirm_password",
                placeholder="Nhập lại mật khẩu",
            )

            if st.button(
                "Tạo tài khoản",
                type="primary",
                width="stretch",
            ):
                if not new_username.strip():
                    st.error("Vui lòng nhập tên đăng nhập.")
                elif not new_email.strip():
                    st.error("Vui lòng nhập email.")
                elif "@" not in new_email or "." not in new_email:
                    st.error("Email không đúng định dạng.")
                elif not new_password:
                    st.error("Vui lòng nhập mật khẩu.")
                elif len(new_password) < 8:
                    st.error("Mật khẩu nên có ít nhất 8 ký tự.")
                elif new_password != confirm_password:
                    st.error("Mật khẩu xác nhận không khớp.")
                else:
                    try:
                        success, result = api_register(
                            new_username.strip(),
                            new_email.strip(),
                            new_password,
                        )

                        if success:
                            show_notification(
                                "success",
                                "Đăng ký tài khoản thành công!",
                            )
                            st.info(
                                "Bạn có thể chuyển sang tab Đăng nhập."
                            )
                        else:
                            st.error(get_api_error(result))

                    except Exception as error:
                        st.error(f"Không thể đăng ký: {error}")


# =========================================================

# 5. TRANG TỔNG QUAN
# =========================================================

def show_dashboard():
    transactions, categories = load_data()

    show_page_title(
        "Tổng quan tài chính",
        "Theo dõi tình hình thu nhập và chi tiêu của bạn.",
    )

    username = get_user_value("username") or "Bạn"
    safe_username = html.escape(str(username))

    st.markdown(
        f"""
        <div class="dashboard-banner">
            <h2>Xin chào, {safe_username} 👋</h2>
            <p>
                Đây là tổng quan tình hình tài chính cá nhân của bạn.
                Hãy theo dõi thu nhập và chi tiêu thường xuyên nhé!
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_income = sum(
        float(item.amount)
        for item in transactions
        if item.transaction_type == "income"
    )
    total_expense = sum(
        float(item.amount)
        for item in transactions
        if item.transaction_type == "expense"
    )
    balance = total_income - total_expense

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-icon">💰</div>
                <div class="metric-label">TỔNG THU NHẬP</div>
                <div class="metric-value metric-value--income">
                    {format_money(total_income)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-icon">💸</div>
                <div class="metric-label">TỔNG CHI TIÊU</div>
                <div class="metric-value metric-value--expense">
                    {format_money(total_expense)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-icon">📊</div>
                <div class="metric-label">SỐ DƯ HIỆN TẠI</div>
                <div class="metric-value {
                    'metric-value--balance'
                    if balance >= 0
                    else 'metric-value--negative'
                }">
                    {format_money(balance)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    left, right = st.columns([1.5, 1])

    with left:
        st.subheader("Biến động thu và chi")
        st.caption(
            "So sánh tổng thu nhập và chi tiêu theo từng tháng."
        )

        if transactions:
            chart = build_monthly_cashflow_chart(
                transactions,
                categories,
            )

            if chart is not None:
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Không có dữ liệu ngày hợp lệ.")
        else:
            st.info("Chưa có dữ liệu giao dịch để hiển thị.")

    with right:
        st.subheader("Tình hình chi tiêu")

        expense_ratio = (
            total_expense / total_income * 100
            if total_income > 0
            else 0
        )

        st.metric(
            "Tỷ lệ chi tiêu trên thu nhập",
            f"{expense_ratio:.1f}%",
        )
        st.progress(min(max(expense_ratio / 100, 0), 1))

        if total_income == 0 and total_expense == 0:
            st.info("Hãy thêm giao dịch để xem phân tích.")
        elif total_income == 0:
            st.warning("Bạn chưa có thu nhập được ghi nhận.")
        elif expense_ratio > 100:
            st.error("Chi tiêu đang vượt quá tổng thu nhập.")
        elif expense_ratio >= 80:
            st.warning("Bạn nên chú ý kiểm soát chi tiêu.")
        else:
            st.success(
                "Tình hình chi tiêu đang trong mức hợp lý."
            )

    st.subheader("Giao dịch gần đây")

    if transactions:
        recent = sorted(
            transactions,
            key=lambda item: item.transaction_date,
            reverse=True,
        )[:5]
        recent_df = transaction_dataframe(recent, categories)
        st.dataframe(
            recent_df,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Bạn chưa có giao dịch nào.")


# =========================================================
# 6. QUẢN LÝ GIAO DỊCH
# =========================================================

def show_transactions(transaction_type=None):
    if transaction_type not in (None, "income", "expense"):
        raise ValueError("Loại giao dịch không hợp lệ.")

    is_filtered_page = transaction_type is not None
    page_label = (
        "Thu nhập"
        if transaction_type == "income"
        else "Chi tiêu"
        if transaction_type == "expense"
        else "Giao dịch"
    )
    show_page_title(
        page_label,
        (
            f"Quản lý các khoản {page_label.lower()}."
            if is_filtered_page
            else "Thêm, chỉnh sửa, xóa và tìm kiếm các khoản thu chi."
        ),
    )

    transactions, categories = load_data()
    if is_filtered_page:
        transactions = [
            item
            for item in transactions
            if item.transaction_type == transaction_type
        ]

        total_amount = sum(
            item.amount
            for item in transactions
        )
        st.metric(
            f"Tổng {page_label.lower()}",
            format_money(total_amount),
        )

    tab_add, tab_list, tab_import = st.tabs([
        (
            "➕ Thêm thu nhập"
            if transaction_type == "income"
            else "➕ Thêm chi tiêu"
            if transaction_type == "expense"
            else "➕ Thêm giao dịch"
        ),
        "📋 Danh sách giao dịch",
        "📥 Nhập CSV",
    ])

    # THÊM GIAO DỊCH
    with tab_add:
        st.subheader("Tạo giao dịch mới")
        category_load_error = st.session_state.get(
            "category_load_error"
        )

        with st.form(
            f"add_{transaction_type or 'all'}_transaction_form"
        ):
            selected_transaction_type = transaction_type
            if not is_filtered_page:
                selected_transaction_type = st.selectbox(
                    "Loại giao dịch",
                    ["expense", "income"],
                    format_func=lambda value: (
                        "Chi tiêu" if value == "expense" else "Thu nhập"
                    ),
                )

            available_categories = get_category_options(
                categories,
                selected_transaction_type,
            )
            category_map = {
                item.name: item.id
                for item in available_categories
            }

            if category_load_error:
                selected_category = None
                st.error(category_load_error)
            elif available_categories:
                selected_category = st.selectbox(
                    "Danh mục",
                    list(category_map.keys()),
                    key=(
                        f"{transaction_type}_add_category"
                        if is_filtered_page
                        else "all_add_category"
                    ),
                )
            else:
                selected_category = None
                st.warning(
                    "Bạn chưa có danh mục phù hợp. "
                    "Hãy tạo danh mục trước."
                )

            amount = st.number_input(
                "Số tiền (VNĐ)",
                min_value=0,
                step=10000,
            )
            description = st.text_input(
                "Mô tả",
                placeholder="Ví dụ: Ăn sáng, tiền lương...",
            )
            transaction_date = st.date_input(
                "Ngày giao dịch",
                value=date.today(),
            )

            submitted = st.form_submit_button(
                "Lưu giao dịch",
                type="primary",
                width="stretch",
            )

            if submitted:
                if category_load_error:
                    st.error(
                        "Không thể lưu giao dịch khi danh mục chưa tải được."
                    )
                elif not available_categories:
                    st.error(
                        "Bạn cần tạo danh mục phù hợp trước. "
                        "Danh mục thu nhập và chi tiêu được tách riêng."
                    )
                elif amount <= 0:
                    st.error("Số tiền phải lớn hơn 0.")
                else:
                    try:
                        category_id = category_map[selected_category]
                        success, result = create_transaction_api(
                            category_id=category_id,
                            transaction_type=selected_transaction_type,
                            amount=parse_amount(amount),
                            description=description.strip(),
                            transaction_date=transaction_date,
                        )

                        if success:
                            queue_notification(
                                "success",
                                "Thêm giao dịch thành công!",
                            )
                            st.rerun()
                        else:
                            st.error(get_api_error(result))
                    except Exception as error:
                        st.error(f"Không thể lưu giao dịch: {error}")

    # DANH SÁCH, SỬA VÀ XÓA GIAO DỊCH
    with tab_list:
        st.subheader("Danh sách giao dịch")

        search_text = st.text_input(
            "Tìm kiếm theo mô tả hoặc danh mục",
            placeholder="Nhập nội dung cần tìm...",
            key=f"{transaction_type or 'all'}_transaction_search",
        )
        if not is_filtered_page:
            filter_type = st.selectbox(
                "Lọc theo loại",
                ["Tất cả", "Thu nhập", "Chi tiêu"],
                key="all_transaction_type_filter",
            )
        else:
            filter_type = (
                "Thu nhập"
                if transaction_type == "income"
                else "Chi tiêu"
            )

        category_filter_options = ["Tất cả"] + sorted({
            category_name(item.category_id, categories)
            for item in transactions
        })
        selected_category_filter = st.selectbox(
            "Lọc theo danh mục",
            category_filter_options,
            key=f"{transaction_type or 'all'}_category_filter",
        )

        filter_start_date = None
        filter_end_date = None
        if transactions:
            transaction_dates = [
                item.transaction_date
                for item in transactions
            ]
            min_transaction_date = min(transaction_dates)
            max_transaction_date = max(transaction_dates)
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                filter_start_date = st.date_input(
                    "Từ ngày",
                    value=min_transaction_date,
                    min_value=min_transaction_date,
                    max_value=max_transaction_date,
                    key=f"{transaction_type or 'all'}_start_date",
                )
            with date_col2:
                filter_end_date = st.date_input(
                    "Đến ngày",
                    value=max_transaction_date,
                    min_value=min_transaction_date,
                    max_value=max_transaction_date,
                    key=f"{transaction_type or 'all'}_end_date",
                )

        filtered = list(transactions)

        if filter_type == "Thu nhập":
            filtered = [
                item for item in filtered
                if item.transaction_type == "income"
            ]
        elif filter_type == "Chi tiêu":
            filtered = [
                item for item in filtered
                if item.transaction_type == "expense"
            ]

        if selected_category_filter != "Tất cả":
            filtered = [
                item
                for item in filtered
                if category_name(item.category_id, categories)
                == selected_category_filter
            ]

        if filter_start_date and filter_end_date:
            if filter_start_date > filter_end_date:
                st.error("Ngày bắt đầu không được lớn hơn ngày kết thúc.")
                filtered = []
            else:
                filtered = [
                    item
                    for item in filtered
                    if filter_start_date
                    <= item.transaction_date
                    <= filter_end_date
                ]

        if search_text.strip():
            keyword = search_text.strip().casefold()
            filtered = [
                item for item in filtered
                if keyword in (item.description or "").casefold()
                or keyword in category_name(
                    item.category_id,
                    categories,
                ).casefold()
            ]

        if filtered:
            filtered = sorted(
                filtered,
                key=lambda item: item.transaction_date,
                reverse=True,
            )
            df = transaction_dataframe(filtered, categories)
            st.dataframe(
                df,
                width="stretch",
                hide_index=True,
            )

            st.divider()
            st.subheader("Chỉnh sửa hoặc xóa giao dịch")

            transaction_map = {
                (
                    f"#{item.id} - {item.transaction_date} - "
                    f"{item.description or 'Không có mô tả'}"
                ): item
                for item in filtered
            }
            selected_label = st.selectbox(
                "Chọn giao dịch",
                list(transaction_map.keys()),
            )
            selected_transaction = transaction_map[selected_label]

            edit_categories = get_category_options(
                categories,
                selected_transaction.transaction_type,
            )

            if not edit_categories:
                st.warning(
                    "Không có danh mục phù hợp để chỉnh sửa."
                )
            else:
                with st.form(
                    f"edit_{transaction_type or 'all'}_transaction_form"
                ):
                    category_labels = {
                        item.name: item.id
                        for item in edit_categories
                    }
                    current_category = category_name(
                        selected_transaction.category_id,
                        categories,
                    )
                    category_names = list(category_labels.keys())

                    default_index = (
                        category_names.index(current_category)
                        if current_category in category_names
                        else 0
                    )

                    new_category = st.selectbox(
                        "Danh mục",
                        category_names,
                        index=default_index,
                        key=f"{transaction_type or 'all'}_edit_category",
                    )
                    new_amount = st.number_input(
                        "Số tiền",
                        min_value=1,
                        value=max(
                            1,
                            int(selected_transaction.amount),
                        ),
                    )
                    new_description = st.text_input(
                        "Mô tả",
                        value=selected_transaction.description or "",
                    )
                    new_date = st.date_input(
                        "Ngày giao dịch",
                        value=selected_transaction.transaction_date,
                        key=f"{transaction_type or 'all'}_edit_date",
                    )
                    save_edit = st.form_submit_button(
                        "Lưu thay đổi",
                        type="primary",
                    )

                    if save_edit:
                        try:
                            success, result = update_transaction_api(
                                transaction_id=selected_transaction.id,
                                category_id=category_labels[new_category],
                                transaction_type=(
                                    selected_transaction.transaction_type
                                ),
                                amount=parse_amount(new_amount),
                                description=new_description.strip(),
                                transaction_date=new_date,
                            )

                            if success:
                                queue_notification(
                                    "success",
                                    "Cập nhật giao dịch thành công!",
                                )
                                st.rerun()
                            else:
                                st.error(get_api_error(result))
                        except Exception as error:
                            st.error(
                                f"Không thể cập nhật giao dịch: {error}"
                            )

            st.divider()
            confirm_delete = st.checkbox(
                "Tôi xác nhận muốn xóa giao dịch đã chọn.",
                key="confirm_delete_transaction",
            )

            if st.button(
                "🗑️ Xóa giao dịch này",
                disabled=not confirm_delete,
            ):
                try:
                    success, result = delete_transaction_api(
                        selected_transaction.id
                    )

                    if success:
                        queue_notification(
                            "success",
                            "Xóa giao dịch thành công!",
                        )
                        st.rerun()
                    else:
                        st.error(get_api_error(result))
                except Exception as error:
                    st.error(f"Không thể xóa giao dịch: {error}")
        else:
            st.info("Không tìm thấy giao dịch phù hợp.")

    # NHẬP GIAO DỊCH TỪ CSV
    with tab_import:
        st.subheader("Nhập giao dịch từ CSV")
        st.caption(
            "File CSV cần có các cột: "
            "Ngày, Loại, Danh mục, Số tiền, Mô tả."
        )
        st.info(
            "Loại giao dịch có thể ghi: "
            "Thu nhập, Chi tiêu, income hoặc expense."
        )

        uploaded_file = st.file_uploader(
            "Chọn file CSV",
            type=["csv"],
            key=f"{transaction_type or 'all'}_transaction_csv_upload",
        )

        if uploaded_file is not None:
            try:
                content = uploaded_file.getvalue().decode("utf-8-sig")
                imported_df = pd.read_csv(StringIO(content))

                required_columns = [
                    "Ngày",
                    "Loại",
                    "Danh mục",
                    "Số tiền",
                    "Mô tả",
                ]
                missing_columns = [
                    column for column in required_columns
                    if column not in imported_df.columns
                ]

                if missing_columns:
                    st.error(
                        "File CSV thiếu cột: "
                        + ", ".join(missing_columns)
                    )
                elif imported_df.empty:
                    st.warning("File CSV không có dữ liệu.")
                else:
                    st.write("Xem trước dữ liệu:")
                    st.dataframe(
                        imported_df.head(10),
                        width="stretch",
                        hide_index=True,
                    )

                    if st.button(
                        "Tiến hành nhập dữ liệu",
                        type="primary",
                        key=f"{transaction_type or 'all'}_import_csv_button",
                    ):
                        success_count = 0
                        error_count = 0
                        error_details = []

                        category_lookup = {
                            (
                                item.name.strip().casefold(),
                                item.category_type,
                            ): item.id
                            for item in categories
                        }

                        for index, row in imported_df.iterrows():
                            try:
                                raw_type = str(
                                    row["Loại"]
                                ).strip().casefold()

                                if raw_type in ["chi tiêu", "expense"]:
                                    row_transaction_type = "expense"
                                elif raw_type in ["thu nhập", "income"]:
                                    row_transaction_type = "income"
                                else:
                                    raise ValueError(
                                        "Loại giao dịch không hợp lệ."
                                    )

                                if (
                                    is_filtered_page
                                    and row_transaction_type
                                    != transaction_type
                                ):
                                    raise ValueError(
                                        "Dòng dữ liệu không thuộc trang "
                                        f"{page_label.lower()}."
                                    )

                                category_key = (
                                    str(row["Danh mục"]).strip().casefold(),
                                    row_transaction_type,
                                )
                                category_id = category_lookup.get(
                                    category_key
                                )

                                if category_id is None:
                                    raise ValueError(
                                        "Không tìm thấy danh mục phù hợp."
                                    )

                                transaction_date = pd.to_datetime(
                                    row["Ngày"],
                                    errors="raise",
                                ).date()
                                amount = parse_amount(row["Số tiền"])
                                description = (
                                    ""
                                    if pd.isna(row["Mô tả"])
                                    else str(row["Mô tả"]).strip()
                                )

                                success, result = create_transaction_api(
                                    category_id=category_id,
                                    transaction_type=row_transaction_type,
                                    amount=amount,
                                    description=description,
                                    transaction_date=transaction_date,
                                )

                                if success:
                                    success_count += 1
                                else:
                                    error_count += 1
                                    error_details.append(
                                        f"Dòng {index + 2}: "
                                        f"{get_api_error(result)}"
                                    )

                            except Exception as error:
                                error_count += 1
                                error_details.append(
                                    f"Dòng {index + 2}: {error}"
                                )

                        total_count = len(imported_df)

                        if success_count and not error_count:
                            queue_notification(
                                "success",
                                (
                                    f"Nhập CSV thành công: "
                                    f"{success_count}/{total_count} dòng."
                                ),
                            )
                            st.rerun()

                        if success_count:
                            show_notification(
                                "success",
                                (
                                    f"Đã nhập thành công {success_count}/"
                                    f"{total_count} dòng."
                                ),
                            )

                        if error_count:
                            notification_kind = (
                                "error"
                                if not success_count
                                else "warning"
                            )
                            show_notification(
                                notification_kind,
                                (
                                    f"Nhập thất bại {error_count}/"
                                    f"{total_count} dòng."
                                ),
                            )
                            with st.expander(
                                "Xem chi tiết các dòng bị lỗi"
                            ):
                                for detail in error_details[:30]:
                                    st.write(f"- {detail}")

            except UnicodeDecodeError:
                st.error(
                    "Không đọc được bảng mã CSV. "
                    "Hãy lưu file với mã hóa UTF-8."
                )
            except Exception as error:
                st.error(f"Không thể đọc file CSV: {error}")


# =========================================================


# 7. QUẢN LÝ DANH MỤC
# =========================================================

def show_categories():
    show_page_title(
        "Quản lý danh mục",
        "Phân loại các khoản thu nhập và chi tiêu.",
    )

    categories = load_data()[1]
    category_load_error = st.session_state.get(
        "category_load_error"
    )
    category_map = {
        (
            f"#{item.id} - {item.name} - "
            f"{'Thu nhập' if item.category_type == 'income' else 'Chi tiêu'}"
        ): item
        for item in categories
    }

    tab_add, tab_list = st.tabs([
        "➕ Thêm danh mục",
        "📋 Danh sách danh mục",
    ])

    with tab_add:
        st.subheader("Tạo danh mục mới")

        with st.form("add_category_form"):
            name = st.text_input(
                "Tên danh mục",
                placeholder="Ví dụ: Ăn uống, Lương, Di chuyển...",
            )
            category_type = st.selectbox(
                "Loại danh mục",
                ["expense", "income"],
                format_func=lambda value: (
                    "Chi tiêu" if value == "expense" else "Thu nhập"
                ),
            )
            submitted = st.form_submit_button(
                "Thêm danh mục",
                type="primary",
            )

            if submitted:
                if not name.strip():
                    st.error("Vui lòng nhập tên danh mục.")
                elif any(
                    item.name.strip().casefold() == name.strip().casefold()
                    and item.category_type == category_type
                    for item in categories
                ):
                    st.error("Danh mục này đã tồn tại.")
                else:
                    try:
                        success, result = create_category_api(
                            name.strip(),
                            category_type,
                        )
                        if success:
                            queue_notification(
                                "success",
                                "Thêm danh mục thành công!",
                            )
                            st.rerun()
                        else:
                            st.error(get_api_error(result))
                    except Exception as error:
                        st.error(f"Không thể tạo danh mục: {error}")

    with tab_list:
        if category_load_error:
            st.error(category_load_error)
        elif categories:
            category_df = pd.DataFrame([
                {
                    "ID": item.id,
                    "Tên danh mục": item.name,
                    "Loại": (
                        "Thu nhập"
                        if item.category_type == "income"
                        else "Chi tiêu"
                    ),
                }
                for item in categories
            ])
            st.dataframe(
                category_df,
                width="stretch",
                hide_index=True,
            )

            st.divider()
            st.subheader("Chỉnh sửa danh mục")

            edit_category = st.selectbox(
                "Chọn danh mục cần chỉnh sửa",
                list(category_map.keys()),
                key="edit_category_select",
            )
            selected_edit_category = category_map[edit_category]

            with st.form("edit_category_form"):
                edited_name = st.text_input(
                    "Tên danh mục mới",
                    value=selected_edit_category.name,
                )
                edited_type = st.selectbox(
                    "Loại danh mục mới",
                    ["expense", "income"],
                    index=(
                        0
                        if selected_edit_category.category_type == "expense"
                        else 1
                    ),
                    format_func=lambda value: (
                        "Chi tiêu"
                        if value == "expense"
                        else "Thu nhập"
                    ),
                )
                save_category = st.form_submit_button(
                    "Lưu danh mục",
                    type="primary",
                )

                if save_category:
                    if not edited_name.strip():
                        st.error("Vui lòng nhập tên danh mục.")
                    else:
                        try:
                            success, result = update_category_api(
                                selected_edit_category.id,
                                edited_name,
                                edited_type,
                            )
                            if success:
                                queue_notification(
                                    "success",
                                    "Cập nhật danh mục thành công!",
                                )
                                st.rerun()
                            else:
                                st.error(get_api_error(result))
                        except Exception as error:
                            st.error(
                                f"Không thể cập nhật danh mục: {error}"
                            )

            st.divider()
            st.subheader("Xóa danh mục")

            selected_label = st.selectbox(
                "Chọn danh mục cần xóa",
                list(category_map.keys()),
                key="delete_category_select",
            )
            selected_category = category_map[selected_label]

            confirm_delete = st.checkbox(
                "Tôi xác nhận muốn xóa danh mục này.",
                key="confirm_delete_category",
            )

            if st.button(
                "🗑️ Xóa danh mục",
                disabled=not confirm_delete,
            ):
                try:
                    success, result = delete_category_api(
                        selected_category.id
                    )
                    if success:
                        queue_notification(
                            "success",
                            "Xóa danh mục thành công!",
                        )
                        st.rerun()
                    else:
                        st.error(get_api_error(result))
                except Exception as error:
                    st.error(f"Không thể xóa danh mục: {error}")
        else:
            st.info("Bạn chưa có danh mục nào.")


# =========================================================
# 8. THỐNG KÊ VÀ PHÂN TÍCH
# =========================================================

def show_statistics():
    show_page_title(
        "Thống kê và phân tích",
        "Phân tích thu nhập, chi tiêu theo thời gian và danh mục.",
    )

    transactions, categories = load_data()

    if not transactions:
        st.info("Chưa có dữ liệu để thống kê.")
        return

    df = transaction_dataframe(transactions, categories)
    df["Ngày"] = pd.to_datetime(df["Ngày"], errors="coerce")
    df = df.dropna(subset=["Ngày"])

    if df.empty:
        st.warning("Không có dữ liệu ngày hợp lệ để thống kê.")
        return

    # -----------------------------------------------------
    # Bộ lọc thời gian
    # -----------------------------------------------------

    st.subheader("Khoảng thời gian thống kê")
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Từ ngày",
            value=df["Ngày"].min().date(),
            key="statistics_start_date",
        )

    with col2:
        end_date = st.date_input(
            "Đến ngày",
            value=df["Ngày"].max().date(),
            key="statistics_end_date",
        )

    if start_date > end_date:
        st.error("Ngày bắt đầu không được lớn hơn ngày kết thúc.")
        return

    filtered_df = df[
        (df["Ngày"].dt.date >= start_date)
        & (df["Ngày"].dt.date <= end_date)
    ].copy()

    if filtered_df.empty:
        st.warning(
            "Không có giao dịch trong khoảng thời gian này. "
            "Hãy chọn khoảng thời gian khác."
        )
        return

    # -----------------------------------------------------
    # Các chỉ số tổng quan
    # -----------------------------------------------------

    income = filtered_df.loc[
        filtered_df["Loại"] == "Thu nhập",
        "Số tiền",
    ].sum()

    expense = filtered_df.loc[
        filtered_df["Loại"] == "Chi tiêu",
        "Số tiền",
    ].sum()

    balance = income - expense

    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng thu nhập", format_money(income))
    col2.metric("Tổng chi tiêu", format_money(expense))
    col3.metric("Chênh lệch thu - chi", format_money(balance))

    st.divider()

    # -----------------------------------------------------
    # BIỂU ĐỒ 1: THU NHẬP VÀ CHI TIÊU THEO THÁNG
    # -----------------------------------------------------

    st.subheader("Thu nhập và chi tiêu theo tháng")
    st.caption(
        "So sánh tổng thu nhập và chi tiêu trong từng tháng "
        "thuộc khoảng thời gian đã chọn."
    )

    # Tạo đầy đủ các tháng trong phạm vi lọc.
    # Tháng không có giao dịch sẽ được điền giá trị 0.
    start_period = pd.Period(start_date, freq="M")
    end_period = pd.Period(end_date, freq="M")
    all_months = pd.period_range(
        start=start_period,
        end=end_period,
        freq="M",
    )

    filtered_df["Tháng"] = filtered_df["Ngày"].dt.to_period("M")

    monthly = filtered_df.pivot_table(
        index="Tháng",
        columns="Loại",
        values="Số tiền",
        aggfunc="sum",
        fill_value=0,
    )

    monthly = monthly.reindex(
        columns=["Thu nhập", "Chi tiêu"],
        fill_value=0,
    )
    monthly = monthly.reindex(all_months, fill_value=0)

    month_labels = [
        f"Tháng {period.month:02d}/{period.year}"
        for period in all_months
    ]

    monthly.index = month_labels
    monthly.index.name = "Tháng"

    chart_df = (
        monthly
        .reset_index()
        .melt(
            id_vars="Tháng",
            var_name="Loại",
            value_name="Số tiền",
        )
    )

    monthly_chart = (
        alt.Chart(chart_df)
        .mark_bar(
            size=25,
            cornerRadiusTopLeft=4,
            cornerRadiusTopRight=4,
        )
        .encode(
            x=alt.X(
                "Tháng:N",
                sort=month_labels,
                title="Thời gian",
                axis=alt.Axis(
                    labelAngle=-35,
                    labelLimit=140,
                ),
            ),
            xOffset=alt.XOffset("Loại:N"),
            y=alt.Y(
                "Số tiền:Q",
                title="Số tiền (VNĐ)",
                scale=alt.Scale(zero=True),
                axis=alt.Axis(format=",.0f"),
            ),
            color=alt.Color(
                "Loại:N",
                title="Loại giao dịch",
                scale=alt.Scale(
                    domain=["Thu nhập", "Chi tiêu"],
                    range=["#15966b", "#df6868"],
                ),
            ),
            tooltip=[
                alt.Tooltip("Tháng:N", title="Tháng"),
                alt.Tooltip("Loại:N", title="Loại giao dịch"),
                alt.Tooltip(
                    "Số tiền:Q",
                    title="Số tiền",
                    format=",.0f",
                ),
            ],
        )
        .properties(height=380)
        .configure_view(strokeOpacity=0)
        .configure_axis(
            gridColor="#e8edf3",
            domain=False,
            tickColor="#d9e1ec",
        )
        .configure_legend(
            orient="top",
            title=None,
        )
    )

    st.altair_chart(
        monthly_chart,
        use_container_width=True,
    )

    with st.expander("Xem số liệu thu chi từng tháng"):
        display_monthly = monthly.copy()
        display_monthly["Chênh lệch"] = (
            display_monthly["Thu nhập"]
            - display_monthly["Chi tiêu"]
        )
        display_monthly = display_monthly.reset_index()
        display_monthly = display_monthly.rename(
            columns={
                "Thu nhập": "Tổng thu nhập (VNĐ)",
                "Chi tiêu": "Tổng chi tiêu (VNĐ)",
                "Chênh lệch": "Chênh lệch (VNĐ)",
            }
        )
        st.dataframe(
            display_monthly,
            width="stretch",
            hide_index=True,
        )

    st.divider()

    # -----------------------------------------------------
    # BIỂU ĐỒ 2: CHI TIÊU THEO DANH MỤC
    # -----------------------------------------------------

    st.subheader("Chi tiêu theo danh mục")

    expense_df = filtered_df[
        filtered_df["Loại"] == "Chi tiêu"
    ]

    if not expense_df.empty:
        category_stats = (
            expense_df
            .groupby("Danh mục")["Số tiền"]
            .sum()
            .sort_values(ascending=False)
        )

        category_chart_df = (
            category_stats
            .rename_axis("Danh mục")
            .reset_index(name="Số tiền")
        )

        category_chart = (
            alt.Chart(category_chart_df)
            .mark_bar(
                color="#087f8c",
                cornerRadiusEnd=5,
            )
            .encode(
                x=alt.X(
                    "Số tiền:Q",
                    title="Số tiền (VNĐ)",
                    axis=alt.Axis(format=",.0f"),
                ),
                y=alt.Y(
                    "Danh mục:N",
                    sort="-x",
                    title="Danh mục",
                ),
                tooltip=[
                    alt.Tooltip("Danh mục:N"),
                    alt.Tooltip("Số tiền:Q", format=",.0f"),
                ],
            )
            .properties(height=300)
        )

        st.altair_chart(
            category_chart,
            use_container_width=True,
        )
    else:
        st.info(
            "Chưa có khoản chi tiêu nào trong thời gian này."
        )

    st.divider()

    # -----------------------------------------------------
    # NHẬN XÉT TÀI CHÍNH
    # -----------------------------------------------------

    st.subheader("Nhận xét tài chính")

    if income > 0:
        ratio = expense / income * 100

        st.metric(
            "Tỷ lệ chi tiêu trên thu nhập",
            f"{ratio:.1f}%",
        )
        st.progress(min(ratio / 100, 1.0))

        if ratio > 100:
            st.error(
                "Chi tiêu đang vượt quá thu nhập "
                "trong khoảng thời gian đã chọn."
            )
        elif ratio >= 80:
            st.warning(
                "Chi tiêu đang chiếm phần lớn thu nhập. "
                "Bạn nên cân nhắc kiểm soát các khoản chưa cần thiết."
            )
        else:
            st.success(
                "Chi tiêu đang thấp hơn thu nhập. "
                "Bạn có thể cân nhắc dành phần chênh lệch "
                "cho tiết kiệm hoặc các mục tiêu tài chính."
            )
    else:
        st.info(
            "Không có thu nhập trong khoảng thời gian này "
            "nên chưa thể đánh giá tỷ lệ chi tiêu trên thu nhập."
        )


# =========================================================


# 9. XUẤT DỮ LIỆU
# =========================================================

def show_export():
    show_page_title(
        "Xuất dữ liệu",
        "Tải xuống dữ liệu giao dịch để lưu trữ và báo cáo.",
    )

    transactions, categories = load_data()

    if not transactions:
        st.info("Chưa có dữ liệu để xuất.")
        return

    df = transaction_dataframe(transactions, categories)

    st.subheader("Xem trước dữ liệu")
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
    )

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        csv_data = df.to_csv(index=False).encode("utf-8-sig")
        st.caption("Nhấn nút để tải dữ liệu CSV về máy.")
        csv_downloaded = st.download_button(
            label="📄 Tải xuống CSV",
            data=csv_data,
            file_name="giao_dich_ca_nhan.csv",
            mime="text/csv",
            width="stretch",
        )
        if csv_downloaded:
            show_notification(
                "success",
                "File CSV đã sẵn sàng để tải xuống.",
            )

    with col2:
        try:
            excel_buffer = BytesIO()

            with pd.ExcelWriter(
                excel_buffer,
                engine="openpyxl",
            ) as writer:
                df.to_excel(
                    writer,
                    sheet_name="Giao dịch",
                    index=False,
                )

                summary = pd.DataFrame([
                    {
                        "Chỉ tiêu": "Tổng thu nhập",
                        "Số tiền": df.loc[
                            df["Loại"] == "Thu nhập",
                            "Số tiền",
                        ].sum(),
                    },
                    {
                        "Chỉ tiêu": "Tổng chi tiêu",
                        "Số tiền": df.loc[
                            df["Loại"] == "Chi tiêu",
                            "Số tiền",
                        ].sum(),
                    },
                ])

                summary.to_excel(
                    writer,
                    sheet_name="Tổng quan",
                    index=False,
                )

            st.caption("Nhấn nút để tải báo cáo Excel về máy.")
            excel_downloaded = st.download_button(
                label="📊 Tải xuống Excel",
                data=excel_buffer.getvalue(),
                file_name="bao_cao_chi_tieu.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                width="stretch",
            )
            if excel_downloaded:
                show_notification(
                    "success",
                    "File Excel đã sẵn sàng để tải xuống.",
                )

        except Exception as error:
            st.error(f"Không thể tạo file Excel: {error}")


# =========================================================

# 10. HỒ SƠ CÁ NHÂN
# =========================================================

def show_profile():
    show_page_title(
        "Hồ sơ cá nhân",
        "Quản lý thông tin tài khoản và bảo mật đăng nhập.",
    )

    username = get_user_value("username") or "Chưa xác định"
    email = get_user_value("email") or ""

    st.markdown(
        f"""
        <div class="profile-summary">
            <div class="profile-avatar">👤</div>
            <div>
                <p class="profile-eyebrow">TÀI KHOẢN ĐANG ĐĂNG NHẬP</p>
                <h2>{html.escape(str(username))}</h2>
                <p>{html.escape(str(email))}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Cập nhật email")
    with st.form("update_email_form"):
        st.text_input(
            "Email hiện tại",
            value=email,
            disabled=True,
        )
        new_email = st.text_input(
            "Email mới",
            value=email,
            placeholder="name@example.com",
        )

        if st.form_submit_button(
            "Lưu thay đổi",
            type="primary",
            width="stretch",
        ):
            new_email = new_email.strip().lower()

            if not re.fullmatch(
                r"[^@\s]+@[^@\s]+\.[^@\s]+",
                new_email,
            ):
                st.error("Email không đúng định dạng.")
            elif new_email == str(email).strip().lower():
                st.info("Email mới trùng với email hiện tại.")
            else:
                success, result = update_profile_api(new_email)

                if success:
                    st.session_state.user = result
                    show_notification(
                        "success",
                        "Cập nhật email thành công!",
                    )
                else:
                    st.error(get_api_error(result))

    st.subheader("Đổi mật khẩu")
    with st.form("change_password_form"):
        current_password = st.text_input(
            "Mật khẩu hiện tại",
            type="password",
        )
        new_password = st.text_input(
            "Mật khẩu mới",
            type="password",
            help="Mật khẩu phải có từ 8 đến 128 ký tự.",
        )
        confirm_password = st.text_input(
            "Nhập lại mật khẩu mới",
            type="password",
        )

        if st.form_submit_button(
            "Đổi mật khẩu",
            type="primary",
            width="stretch",
        ):
            if not current_password:
                st.error("Vui lòng nhập mật khẩu hiện tại.")
            elif len(new_password) < 8 or len(new_password) > 128:
                st.error(
                    "Mật khẩu mới phải có từ 8 đến 128 ký tự."
                )
            elif new_password != confirm_password:
                st.error("Mật khẩu xác nhận không khớp.")
            else:
                success, result = change_password_api(
                    current_password,
                    new_password,
                )

                if success:
                    api_logout()
                    queue_notification(
                        "success",
                        (
                            "Đổi mật khẩu thành công! "
                            "Vui lòng đăng nhập lại."
                        ),
                    )
                    st.rerun()
                else:
                    st.error(get_api_error(result))


# =========================================================

# 10. GIAO DIỆN SAU KHI ĐĂNG NHẬP
# =========================================================

def show_main_app():
    username = get_user_value("username") or "Người dùng"

    with st.sidebar:
        st.markdown("## 💳 Expense Manager")
        st.caption("PERSONAL FINANCE")
        st.divider()
        st.markdown("**TÀI CHÍNH CÁ NHÂN**")

        menu = st.radio(
            "Điều hướng",
            [
                "Tổng quan",
                "Giao dịch",
                "Thu nhập",
                "Chi tiêu",
                "Danh mục",
                "Thống kê",
                "Xuất dữ liệu",
                "Hồ sơ cá nhân",
            ],
            format_func=lambda value: {
                "Tổng quan": "⌂  Tổng quan",
                "Giao dịch": "↔  Giao dịch",
                "Thu nhập": "↗  Thu nhập",
                "Chi tiêu": "↘  Chi tiêu",
                "Danh mục": "▦  Danh mục",
                "Thống kê": "◒  Thống kê",
                "Xuất dữ liệu": "⇩  Xuất dữ liệu",
                "Hồ sơ cá nhân": "◉  Hồ sơ cá nhân",
            }[value],
            label_visibility="collapsed",
            key="main_navigation",
        )

        st.divider()

        with st.container(border=True):
            st.markdown("### 👤 Tài khoản")
            st.markdown(f"**{html.escape(str(username))}**")
            st.caption("Tài khoản cá nhân")

        st.write("")

        if st.button("Đăng xuất", width="stretch"):
            api_logout()
            st.session_state.user = None
            st.session_state.logged_in = False
            st.session_state.access_token = None
            st.rerun()

        st.divider()
        st.caption(
            "Personal Expense Management · Version 2.0"
        )

    if menu == "Tổng quan":
        show_dashboard()
    elif menu == "Giao dịch":
        show_transactions()
    elif menu == "Thu nhập":
        show_transactions("income")
    elif menu == "Chi tiêu":
        show_transactions("expense")
    elif menu == "Danh mục":
        show_categories()
    elif menu == "Thống kê":
        show_statistics()
    elif menu == "Xuất dữ liệu":
        show_export()
    elif menu == "Hồ sơ cá nhân":
        show_profile()


# =========================================================
# 11. CHẠY ỨNG DỤNG
# =========================================================

if st.session_state.logged_in and st.session_state.user:
    show_main_app()
else:
    show_auth_page()
