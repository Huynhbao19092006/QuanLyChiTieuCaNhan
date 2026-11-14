
import html
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO, StringIO
from types import SimpleNamespace

import pandas as pd
import streamlit as st

from api_client import (
    register as api_register,
    login as api_login,
    get_current_user,
    logout as api_logout,
    get_categories_api,
    create_category_api,
    delete_category_api,
    get_transactions_api,
    create_transaction_api,
    update_transaction_api,
    delete_transaction_api,
)


# =========================================================
# 1. CẤU HÌNH GIAO DIỆN
# =========================================================

st.set_page_config(
    page_title="Quản lý chi tiêu cá nhân",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --primary: #087f8c;
        --primary-dark: #066570;
        --background: #f5f7fb;
        --text: #1e293b;
        --muted: #64748b;
        --border: #d9e1ec;
    }

    html, body, [class*="css"] {
        font-family: Arial, sans-serif;
    }

    .stApp {
        background: var(--background);
        color: var(--text);
    }

    .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4, h5 {
        color: #172b45 !important;
        font-weight: 700 !important;
    }

    .stApp p,
    .stApp li,
    .stApp label {
        color: var(--text);
    }

    [data-testid="stCaptionContainer"] {
        color: var(--muted) !important;
    }

    section[data-testid="stSidebar"] {
        background: #edf2f8;
        border-right: 1px solid #d5deea;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #1e293b !important;
    }

    section[data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding: 9px 10px;
        border-radius: 9px;
        font-weight: 600;
    }

    section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: #dce7f3;
    }

    section[data-testid="stSidebar"] .stButton button {
        background: #ffffff;
        color: #172b45 !important;
        border: 1px solid #cbd5e1;
        font-weight: 700;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        background: #e1edf5;
        border-color: #9fb4ca;
    }

    .metric-card {
        background: #ffffff;
        padding: 23px;
        border-radius: 16px;
        border: 1px solid var(--border);
        box-shadow: 0 4px 14px rgba(31,48,73,.06);
        min-height: 140px;
    }

    .metric-icon {
        font-size: 24px;
        margin-bottom: 12px;
    }

    .metric-label {
        color: #526174 !important;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: .5px;
        margin-bottom: 10px;
    }

    .metric-value {
        color: #172b45;
        font-size: 24px;
        font-weight: 800;
        overflow-wrap: anywhere;
    }

    .dashboard-banner {
        background: linear-gradient(120deg, #183653, #087f8c);
        color: #ffffff;
        padding: 28px;
        border-radius: 18px;
        margin-bottom: 24px;
    }

    .dashboard-banner h2 {
        color: #ffffff !important;
    }

    .dashboard-banner p {
        color: #f0fdfa !important;
    }

    .content-card {
        background: #ffffff;
        color: #1e293b;
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 18px;
    }

    .stButton > button,
    .stDownloadButton > button,
    .stFormSubmitButton > button {
        border-radius: 9px;
        font-weight: 600;
        min-height: 42px;
    }

    .stButton > button[kind="primary"],
    .stFormSubmitButton > button[kind="primary"] {
        background: var(--primary);
        color: #ffffff !important;
        border: 1px solid var(--primary);
    }

    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button[kind="primary"]:hover {
        background: var(--primary-dark);
    }

    .stTextInput input,
    .stNumberInput input,
    .stDateInput input,
    .stTextArea textarea {
        background: #ffffff !important;
        color: #172b45 !important;
        border: 1px solid #b8c5d6 !important;
        border-radius: 8px !important;
        -webkit-text-fill-color: #172b45 !important;
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #68788c !important;
        opacity: 1;
    }

    .stSelectbox div[data-baseweb="select"],
    .stMultiSelect div[data-baseweb="select"] {
        background: #ffffff !important;
        color: #172b45 !important;
    }

    div[data-baseweb="popover"],
    div[data-baseweb="menu"],
    ul[role="listbox"] {
        background: #ffffff !important;
    }

    li[role="option"],
    div[role="option"] {
        color: #1e293b !important;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid var(--border);
    }

    .stTabs [data-baseweb="tab"] {
        color: #334155 !important;
    }

    .stTabs [aria-selected="true"] {
        color: #087f8c !important;
    }

    [data-testid="stMetricLabel"] {
        color: #526174 !important;
    }

    [data-testid="stMetricValue"] {
        color: #172b45 !important;
    }

    [data-testid="stAlert"] {
        border-radius: 9px;
    }

    hr {
        border-color: #d9e1ec;
    }

    #MainMenu, footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
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

    except Exception:
        api_logout()
        st.session_state.user = None
        st.session_state.logged_in = False


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
        transaction_date=parse_api_date(
            item["transaction_date"]
        ),
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

    if raw_transactions is None or raw_categories is None:
        st.error(
            "Không thể tải dữ liệu từ FastAPI. "
            "Hãy kiểm tra máy chủ API."
        )
        return [], []

    try:
        transactions = [
            convert_transaction(item)
            for item in raw_transactions
        ]

        categories = [
            convert_category(item)
            for item in raw_categories
        ]

        return transactions, categories

    except (KeyError, TypeError, ValueError, InvalidOperation) as error:
        st.error(f"Dữ liệu API không hợp lệ: {error}")
        return [], []


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
            "Danh mục": category_name(
                item.category_id,
                categories
            ),
            "Số tiền": float(item.amount),
            "Mô tả": item.description or "",
        })

    return pd.DataFrame(
        rows,
        columns=[
            "Ngày",
            "Loại",
            "Danh mục",
            "Số tiền",
            "Mô tả",
        ],
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

    st.markdown(
        """
        <div style="
            max-width:650px;
            margin:20px auto 10px auto;
            text-align:center;
        ">
            <div style="font-size:46px;">💳</div>
            <h1 style="margin-bottom:5px;">
                Quản lý chi tiêu cá nhân
            </h1>
            <p style="color:#718096;">
                Quản lý tài chính thông minh,
                đơn giản và hiệu quả.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 1.5, 1])

    with center:

        st.markdown(
            '<div class="content-card">',
            unsafe_allow_html=True,
        )

        tab_login, tab_register = st.tabs([
            "Đăng nhập",
            "Đăng ký",
        ])

        # -----------------------------
        # ĐĂNG NHẬP
        # -----------------------------

        with tab_login:

            st.subheader("Chào mừng trở lại")
            st.caption(
                "Đăng nhập để tiếp tục quản lý tài chính."
            )

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
                use_container_width=True,
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

                                st.success(
                                    "Đăng nhập thành công."
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
                        st.error(
                            f"Không thể đăng nhập: {error}"
                        )

        # -----------------------------
        # ĐĂNG KÝ
        # -----------------------------

        with tab_register:

            st.subheader("Tạo tài khoản mới")

            st.caption(
                "Đăng ký để bắt đầu sử dụng hệ thống."
            )

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
                use_container_width=True,
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
                    st.error(
                        "Mật khẩu nên có ít nhất 8 ký tự."
                    )

                elif new_password != confirm_password:
                    st.error(
                        "Mật khẩu xác nhận không khớp."
                    )

                else:

                    try:
                        success, result = api_register(
                            new_username.strip(),
                            new_email.strip(),
                            new_password,
                        )

                        if success:
                            st.success(
                                "Đăng ký tài khoản thành công."
                            )

                            st.info(
                                "Bạn có thể chuyển sang tab Đăng nhập."
                            )

                        else:
                            st.error(get_api_error(result))

                    except Exception as error:
                        st.error(
                            f"Không thể đăng ký: {error}"
                        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


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
                <div class="metric-value" style="color:#15966b;">
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
                <div class="metric-value" style="color:#df6868;">
                    {format_money(total_expense)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:

        balance_color = (
            "#15966b"
            if balance >= 0
            else "#df6868"
        )

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-icon">📊</div>
                <div class="metric-label">SỐ DƯ HIỆN TẠI</div>
                <div class="metric-value"
                     style="color:{balance_color};">
                    {format_money(balance)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    left, right = st.columns([1.5, 1])

    with left:

        st.markdown(
            '<div class="content-card">',
            unsafe_allow_html=True,
        )

        st.subheader("Biến động thu và chi")

        if transactions:

            df = transaction_dataframe(
                transactions,
                categories,
            )

            df["Ngày"] = pd.to_datetime(
                df["Ngày"],
                errors="coerce",
            )

            df = df.dropna(subset=["Ngày"])

            if not df.empty:

                df["Tháng"] = (
                    df["Ngày"]
                    .dt.to_period("M")
                    .astype(str)
                )

                monthly = df.pivot_table(
                    index="Tháng",
                    columns="Loại",
                    values="Số tiền",
                    aggfunc="sum",
                    fill_value=0,
                )

                st.bar_chart(monthly)

            else:
                st.info(
                    "Không có dữ liệu ngày hợp lệ."
                )

        else:
            st.info(
                "Chưa có dữ liệu giao dịch để hiển thị."
            )

        st.markdown("</div>", unsafe_allow_html=True)

    with right:

        st.markdown(
            '<div class="content-card">',
            unsafe_allow_html=True,
        )

        st.subheader("Tình hình chi tiêu")

        if total_income > 0:
            expense_ratio = (
                total_expense / total_income * 100
            )
        else:
            expense_ratio = 0

        st.metric(
            "Tỷ lệ chi tiêu trên thu nhập",
            f"{expense_ratio:.1f}%",
        )

        st.progress(
            min(max(expense_ratio / 100, 0), 1)
        )

        if total_income == 0 and total_expense == 0:
            st.info(
                "Hãy thêm giao dịch để xem phân tích."
            )

        elif total_income == 0:
            st.warning(
                "Bạn chưa có thu nhập được ghi nhận."
            )

        elif expense_ratio > 100:
            st.error(
                "Chi tiêu đang vượt quá tổng thu nhập."
            )

        elif expense_ratio >= 80:
            st.warning(
                "Bạn nên chú ý kiểm soát chi tiêu."
            )

        else:
            st.success(
                "Tình hình chi tiêu đang trong mức hợp lý."
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="content-card">',
        unsafe_allow_html=True,
    )

    st.subheader("Giao dịch gần đây")

    if transactions:

        recent = sorted(
            transactions,
            key=lambda item: item.transaction_date,
            reverse=True,
        )[:5]

        recent_df = transaction_dataframe(
            recent,
            categories,
        )

        st.dataframe(
            recent_df,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info("Bạn chưa có giao dịch nào.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# 6. QUẢN LÝ GIAO DỊCH
# =========================================================

def show_transactions():

    show_page_title(
        "Quản lý giao dịch",
        "Thêm, chỉnh sửa, xóa và tìm kiếm các khoản thu chi.",
    )

    transactions, categories = load_data()

    tab_add, tab_list, tab_import = st.tabs([
        "➕ Thêm giao dịch",
        "📋 Danh sách giao dịch",
        "📥 Nhập CSV",
    ])

    # -----------------------------------------------------
    # THÊM GIAO DỊCH
    # -----------------------------------------------------

    with tab_add:

        st.subheader("Tạo giao dịch mới")

        with st.form("add_transaction_form"):

            transaction_type = st.selectbox(
                "Loại giao dịch",
                ["expense", "income"],
                format_func=lambda value: (
                    "Chi tiêu"
                    if value == "expense"
                    else "Thu nhập"
                ),
            )

            available_categories = get_category_options(
                categories,
                transaction_type,
            )

            category_map = {
                item.name: item.id
                for item in available_categories
            }

            if available_categories:

                selected_category = st.selectbox(
                    "Danh mục",
                    list(category_map.keys()),
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
                use_container_width=True,
            )

            if submitted:

                if not available_categories:
                    st.error(
                        "Bạn cần tạo danh mục phù hợp trước."
                    )

                elif amount <= 0:
                    st.error(
                        "Số tiền phải lớn hơn 0."
                    )

                else:

                    try:

                        category_id = category_map[
                            selected_category
                        ]

                        success, result = create_transaction_api(
                            category_id=category_id,
                            transaction_type=transaction_type,
                            amount=parse_amount(amount),
                            description=description.strip(),
                            transaction_date=transaction_date,
                        )

                        if success:
                            st.success(
                                "Đã thêm giao dịch thành công."
                            )
                            st.rerun()

                        else:
                            st.error(get_api_error(result))

                    except Exception as error:
                        st.error(
                            f"Không thể lưu giao dịch: {error}"
                        )

    # -----------------------------------------------------
    # DANH SÁCH, SỬA VÀ XÓA GIAO DỊCH
    # -----------------------------------------------------

    with tab_list:

        st.subheader("Danh sách giao dịch")

        search_text = st.text_input(
            "Tìm kiếm theo mô tả hoặc danh mục",
            placeholder="Nhập nội dung cần tìm...",
            key="transaction_search",
        )

        filter_type = st.selectbox(
            "Lọc theo loại",
            ["Tất cả", "Thu nhập", "Chi tiêu"],
        )

        filtered = list(transactions)

        if filter_type == "Thu nhập":

            filtered = [
                item
                for item in filtered
                if item.transaction_type == "income"
            ]

        elif filter_type == "Chi tiêu":

            filtered = [
                item
                for item in filtered
                if item.transaction_type == "expense"
            ]

        if search_text.strip():

            keyword = search_text.strip().casefold()

            filtered = [
                item
                for item in filtered
                if keyword in (
                    item.description or ""
                ).casefold()
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

            df = transaction_dataframe(
                filtered,
                categories,
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

            st.divider()

            st.subheader(
                "Chỉnh sửa hoặc xóa giao dịch"
            )

            transaction_map = {
                (
                    f"#{item.id} - "
                    f"{item.transaction_date} - "
                    f"{item.description or 'Không có mô tả'}"
                ): item
                for item in filtered
            }

            selected_label = st.selectbox(
                "Chọn giao dịch",
                list(transaction_map.keys()),
            )

            selected_transaction = transaction_map[
                selected_label
            ]

            edit_categories = get_category_options(
                categories,
                selected_transaction.transaction_type,
            )

            if not edit_categories:

                st.warning(
                    "Không có danh mục phù hợp để chỉnh sửa."
                )

            else:

                with st.form("edit_transaction_form"):

                    category_labels = {
                        item.name: item.id
                        for item in edit_categories
                    }

                    current_category = category_name(
                        selected_transaction.category_id,
                        categories,
                    )

                    category_names = list(
                        category_labels.keys()
                    )

                    if current_category in category_names:
                        default_index = category_names.index(
                            current_category
                        )
                    else:
                        default_index = 0

                    new_category = st.selectbox(
                        "Danh mục",
                        category_names,
                        index=default_index,
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
                    )

                    save_edit = st.form_submit_button(
                        "Lưu thay đổi",
                        type="primary",
                    )

                    if save_edit:

                        try:

                            # API hiện tại yêu cầu gửi đầy đủ
                            # các trường khi cập nhật giao dịch.

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
                                st.success(
                                    "Đã cập nhật giao dịch thành công."
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
                        st.success(
                            "Đã xóa giao dịch thành công."
                        )
                        st.rerun()

                    else:
                        st.error(get_api_error(result))

                except Exception as error:
                    st.error(
                        f"Không thể xóa giao dịch: {error}"
                    )

        else:

            st.info(
                "Không tìm thấy giao dịch phù hợp."
            )

    # -----------------------------------------------------
    # NHẬP GIAO DỊCH TỪ CSV
    # -----------------------------------------------------

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
            key="transaction_csv_upload",
        )

        if uploaded_file is not None:

            try:

                content = uploaded_file.getvalue().decode(
                    "utf-8-sig"
                )

                imported_df = pd.read_csv(
                    StringIO(content)
                )

                required_columns = [
                    "Ngày",
                    "Loại",
                    "Danh mục",
                    "Số tiền",
                    "Mô tả",
                ]

                missing_columns = [
                    column
                    for column in required_columns
                    if column not in imported_df.columns
                ]

                if missing_columns:

                    st.error(
                        "File CSV thiếu cột: "
                        + ", ".join(missing_columns)
                    )

                elif imported_df.empty:

                    st.warning(
                        "File CSV không có dữ liệu."
                    )

                else:

                    st.write("Xem trước dữ liệu:")

                    st.dataframe(
                        imported_df.head(10),
                        use_container_width=True,
                        hide_index=True,
                    )

                    if st.button(
                        "Tiến hành nhập dữ liệu",
                        type="primary",
                        key="import_csv_button",
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

                                if raw_type in [
                                    "chi tiêu",
                                    "expense",
                                ]:

                                    transaction_type = "expense"

                                elif raw_type in [
                                    "thu nhập",
                                    "income",
                                ]:

                                    transaction_type = "income"

                                else:

                                    raise ValueError(
                                        "Loại giao dịch không hợp lệ."
                                    )

                                category_key = (
                                    str(row["Danh mục"]).strip().casefold(),
                                    transaction_type,
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

                                amount = parse_amount(
                                    row["Số tiền"]
                                )

                                description = (
                                    ""
                                    if pd.isna(row["Mô tả"])
                                    else str(row["Mô tả"]).strip()
                                )

                                success, result = create_transaction_api(
                                    category_id=category_id,
                                    transaction_type=transaction_type,
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

                        if success_count:
                            st.success(
                                f"Đã nhập thành công "
                                f"{success_count} giao dịch."
                            )

                        if error_count:

                            st.warning(
                                f"Có {error_count} dòng chưa được nhập."
                            )

                            with st.expander(
                                "Xem chi tiết các dòng bị lỗi"
                            ):

                                for detail in error_details[:30]:
                                    st.write(f"- {detail}")

                        if success_count:
                            st.rerun()

            except UnicodeDecodeError:

                st.error(
                    "Không đọc được bảng mã CSV. "
                    "Hãy lưu file với mã hóa UTF-8."
                )

            except Exception as error:

                st.error(
                    f"Không thể đọc file CSV: {error}"
                )


# =========================================================
# 7. QUẢN LÝ DANH MỤC
# =========================================================

def show_categories():

    show_page_title(
        "Quản lý danh mục",
        "Phân loại các khoản thu nhập và chi tiêu.",
    )

    categories = load_data()[1]

    tab_add, tab_list = st.tabs([
        "➕ Thêm danh mục",
        "📋 Danh sách danh mục",
    ])

    # -----------------------------------------------------
    # THÊM DANH MỤC
    # -----------------------------------------------------

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
                    "Chi tiêu"
                    if value == "expense"
                    else "Thu nhập"
                ),
            )

            submitted = st.form_submit_button(
                "Thêm danh mục",
                type="primary",
            )

            if submitted:

                if not name.strip():

                    st.error(
                        "Vui lòng nhập tên danh mục."
                    )

                elif any(
                    item.name.strip().casefold()
                    == name.strip().casefold()
                    and item.category_type == category_type
                    for item in categories
                ):

                    st.error(
                        "Danh mục này đã tồn tại."
                    )

                else:

                    try:

                        success, result = create_category_api(
                            name.strip(),
                            category_type,
                        )

                        if success:
                            st.success(
                                "Đã tạo danh mục thành công."
                            )
                            st.rerun()

                        else:
                            st.error(get_api_error(result))

                    except Exception as error:
                        st.error(
                            f"Không thể tạo danh mục: {error}"
                        )

    # -----------------------------------------------------
    # DANH SÁCH VÀ XÓA DANH MỤC
    # -----------------------------------------------------

    with tab_list:

        if categories:

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
                use_container_width=True,
                hide_index=True,
            )

            st.divider()

            st.subheader("Xóa danh mục")

            category_map = {
                (
                    f"#{item.id} - {item.name} - "
                    f"{'Thu nhập' if item.category_type == 'income' else 'Chi tiêu'}"
                ): item
                for item in categories
            }

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

                        st.success(
                            "Đã xóa danh mục thành công."
                        )

                        st.rerun()

                    else:

                        st.error(get_api_error(result))

                except Exception as error:

                    st.error(
                        f"Không thể xóa danh mục: {error}"
                    )

        else:

            st.info(
                "Bạn chưa có danh mục nào."
            )


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

        st.info(
            "Chưa có dữ liệu để thống kê."
        )

        return

    df = transaction_dataframe(
        transactions,
        categories,
    )

    df["Ngày"] = pd.to_datetime(
        df["Ngày"],
        errors="coerce",
    )

    df = df.dropna(subset=["Ngày"])

    if df.empty:

        st.warning(
            "Không có dữ liệu ngày hợp lệ để thống kê."
        )

        return

    col1, col2 = st.columns(2)

    with col1:

        start_date = st.date_input(
            "Từ ngày",
            value=min(df["Ngày"]).date(),
            key="statistics_start_date",
        )

    with col2:

        end_date = st.date_input(
            "Đến ngày",
            value=max(df["Ngày"]).date(),
            key="statistics_end_date",
        )

    if start_date > end_date:

        st.error(
            "Ngày bắt đầu không được lớn hơn ngày kết thúc."
        )

        return

    filtered_df = df[
        (df["Ngày"].dt.date >= start_date)
        & (df["Ngày"].dt.date <= end_date)
    ].copy()

    if filtered_df.empty:

        st.warning(
            "Không có giao dịch trong khoảng thời gian này."
        )

        return

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

    col1.metric(
        "Tổng thu nhập",
        format_money(income),
    )

    col2.metric(
        "Tổng chi tiêu",
        format_money(expense),
    )

    col3.metric(
        "Chênh lệch",
        format_money(balance),
    )

    st.divider()

    left, right = st.columns(2)

    with left:

        st.subheader("Thống kê theo tháng")

        filtered_df["Tháng"] = (
            filtered_df["Ngày"]
            .dt.to_period("M")
            .astype(str)
        )

        monthly = filtered_df.pivot_table(
            index="Tháng",
            columns="Loại",
            values="Số tiền",
            aggfunc="sum",
            fill_value=0,
        )

        st.bar_chart(monthly)

    with right:

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

            st.bar_chart(category_stats)

        else:

            st.info(
                "Chưa có khoản chi tiêu nào trong thời gian này."
            )

    st.divider()

    st.subheader("Nhận xét tài chính")

    if income > 0:

        ratio = expense / income * 100

        st.write(
            f"Tỷ lệ chi tiêu trên thu nhập: "
            f"**{ratio:.1f}%**"
        )

        if ratio > 100:

            st.error(
                "Bạn đang chi tiêu nhiều hơn thu nhập "
                "trong khoảng thời gian đã chọn."
            )

        elif ratio >= 80:

            st.warning(
                "Mức chi tiêu khá cao. "
                "Bạn nên cân nhắc giảm những khoản chưa cần thiết."
            )

        else:

            st.success(
                "Mức chi tiêu hiện tại đang thấp hơn thu nhập. "
                "Bạn có thể cân nhắc tiết kiệm phần còn lại."
            )

    else:

        st.info(
            "Chưa có thu nhập trong khoảng thời gian được chọn "
            "nên chưa thể tính tỷ lệ chi tiêu."
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

        st.info(
            "Chưa có dữ liệu để xuất."
        )

        return

    df = transaction_dataframe(
        transactions,
        categories,
    )

    st.subheader("Xem trước dữ liệu")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    col1, col2 = st.columns(2)

    # CSV
    with col1:

        csv_data = df.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            label="📄 Tải xuống CSV",
            data=csv_data,
            file_name="giao_dich_ca_nhan.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # EXCEL
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

            st.download_button(
                label="📊 Tải xuống Excel",
                data=excel_buffer.getvalue(),
                file_name="bao_cao_chi_tieu.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True,
            )

        except Exception as error:

            st.error(
                f"Không thể tạo file Excel: {error}"
            )


# =========================================================
# 10. GIAO DIỆN SAU KHI ĐĂNG NHẬP
# =========================================================

def show_main_app():

    username = (
        get_user_value("username")
        or "Người dùng"
    )

    with st.sidebar:

        st.markdown("## 💳 Expense Manager")

        st.caption("PERSONAL FINANCE")

        st.divider()

        st.markdown("**TÀI CHÍNH CÁ NHÂN**")

        menu = st.radio(
            "Điều hướng",
            [
                "Tổng quan",
                "Quản lý giao dịch",
                "Quản lý danh mục",
                "Thống kê",
                "Xuất dữ liệu",
            ],
            label_visibility="collapsed",
        )

        st.divider()

        with st.container(border=True):

            st.markdown("### 👤 Tài khoản")

            st.markdown(
                f"**{html.escape(str(username))}**"
            )

            st.caption("Tài khoản cá nhân")

        st.write("")

        if st.button(
            "Đăng xuất",
            use_container_width=True,
        ):

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

    elif menu == "Quản lý giao dịch":

        show_transactions()

    elif menu == "Quản lý danh mục":

        show_categories()

    elif menu == "Thống kê":

        show_statistics()

    elif menu == "Xuất dữ liệu":

        show_export()


# =========================================================
# 11. CHẠY ỨNG DỤNG
# =========================================================

if st.session_state.logged_in and st.session_state.user:

    show_main_app()

else:

    show_auth_page()
