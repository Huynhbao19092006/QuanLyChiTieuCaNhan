
import streamlit as st
import pandas as pd

from datetime import date
from decimal import Decimal
from io import BytesIO, StringIO

from database import create_db_and_tables, get_session
from api_client import (
    register as api_register,
    login as api_login,
    get_current_user,
    logout as api_logout,
)

from services.transaction_service import (
    get_transactions,
    add_transaction,
    update_transaction,
    delete_transaction,
)

from services.category_service import (
    get_categories,
    add_category,
    delete_category,
)


# =====================================================
# 1. CẤU HÌNH ỨNG DỤNG
# =====================================================

st.set_page_config(
    page_title="Quản lý chi tiêu cá nhân",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

create_db_and_tables()


# =====================================================
# 2. CSS - GIAO DIỆN
# =====================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Be Vietnam Pro', sans-serif;
}

.stApp {
    background: #f2f5fa;
    color: #243247;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}

section[data-testid="stSidebar"] {
    background: #17283f;
}

section[data-testid="stSidebar"] * {
    color: #f3f6fc !important;
}

section[data-testid="stSidebar"] .stRadio label {
    background: transparent;
    border-radius: 10px;
    padding: 8px 12px;
}

section[data-testid="stSidebar"] .stRadio label:hover {
    background: #263d59;
}

h1, h2, h3 {
    color: #1c2d45;
    font-weight: 700;
}

.metric-card {
    background: #ffffff;
    padding: 23px;
    border-radius: 17px;
    border: 1px solid #e7ecf3;
    box-shadow: 0 5px 18px rgba(31, 48, 73, 0.045);
    min-height: 135px;
}

.metric-label {
    color: #7b8798;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 12px;
}

.metric-value {
    color: #1c2d45;
    font-size: 25px;
    font-weight: 800;
}

.metric-icon {
    font-size: 22px;
    margin-bottom: 10px;
}

.dashboard-banner {
    background: linear-gradient(120deg, #172d49, #246b78);
    color: white;
    padding: 30px;
    border-radius: 20px;
    margin-bottom: 25px;
    box-shadow: 0 8px 25px rgba(24, 58, 82, 0.12);
}

.dashboard-banner h2 {
    color: white;
    margin-bottom: 8px;
}

.dashboard-banner p {
    color: #d9e9ee;
    margin-bottom: 0;
}

.content-card {
    background: white;
    border: 1px solid #e7ecf3;
    border-radius: 16px;
    padding: 22px;
    margin-bottom: 20px;
}

.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    min-height: 42px;
    border: none;
}

.stButton > button[kind="primary"] {
    background: #187b83;
    color: white;
}

.stButton > button[kind="primary"]:hover {
    background: #12656d;
}

.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stSelectbox div[data-baseweb="select"] {
    border-radius: 9px;
}

div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. KHỞI TẠO SESSION VÀ KHÔI PHỤC ĐĂNG NHẬP
# =====================================================

if "user" not in st.session_state:
    st.session_state.user = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if st.session_state.access_token and not st.session_state.user:
    current_user = get_current_user()

    if current_user:
        st.session_state.user = current_user
        st.session_state.logged_in = True
    else:
        api_logout()
        st.session_state.user = None
        st.session_state.logged_in = False


# =====================================================
# 4. HÀM HỖ TRỢ
# =====================================================

def format_money(value):
    """Định dạng số tiền thành VNĐ."""
    try:
        value = float(value)
        return f"{value:,.0f} đ"
    except (ValueError, TypeError):
        return "0 đ"


def get_user_value(field):
    """Lấy thông tin người dùng từ dictionary hoặc object."""
    user = st.session_state.get("user")

    if user is None:
        return None

    if isinstance(user, dict):
        return user.get(field)

    return getattr(user, field, None)


def get_user_id():
    """Lấy ID người dùng đang đăng nhập."""
    return get_user_value("id")


def load_data():
    """Lấy giao dịch và danh mục của người dùng hiện tại."""
    user_id = get_user_id()

    if user_id is None:
        return [], []

    with get_session() as session:
        transactions = get_transactions(session, user_id)
        categories = get_categories(session, user_id)

    return transactions, categories


def category_name(category_id, categories):
    """Tìm tên danh mục theo ID."""
    for category in categories:
        if category.id == category_id:
            return category.name

    return "Không xác định"


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
                item.category_id, categories
            ),
            "Số tiền": float(item.amount),
            "Mô tả": item.description or ""
        })

    return pd.DataFrame(
        rows,
        columns=["Ngày", "Loại", "Danh mục", "Số tiền", "Mô tả"]
    )


def get_category_options(categories, transaction_type=None):
    """Lấy danh mục phù hợp với loại giao dịch."""
    if transaction_type is None:
        return categories

    return [
        category for category in categories
        if category.category_type == transaction_type
    ]


def show_page_title(title, description):
    st.title(title)
    st.caption(description)
    st.divider()


# =====================================================
# 5. ĐĂNG NHẬP VÀ ĐĂNG KÝ QUA FASTAPI
# =====================================================

def show_auth_page():

    st.markdown("""
    <div style="
        max-width: 650px;
        margin: 20px auto 10px auto;
        text-align: center;
    ">
        <div style="font-size: 42px;">💳</div>
        <h1 style="margin-bottom: 5px;">
            Quản lý chi tiêu cá nhân
        </h1>
        <p style="color: #78869a;">
            Quản lý tài chính thông minh, đơn giản và hiệu quả.
        </p>
    </div>
    """, unsafe_allow_html=True)

    left, center, right = st.columns([1, 1.4, 1])

    with center:

        st.markdown(
            '<div class="content-card">',
            unsafe_allow_html=True
        )

        tab_login, tab_register = st.tabs([
            "Đăng nhập",
            "Đăng ký"
        ])

        # -------------------------------------------------
        # ĐĂNG NHẬP
        # -------------------------------------------------

        with tab_login:

            st.subheader("Chào mừng trở lại")
            st.caption("Đăng nhập để tiếp tục quản lý tài chính.")

            username = st.text_input(
                "Tên đăng nhập",
                key="login_username",
                placeholder="Nhập tên đăng nhập"
            )

            password = st.text_input(
                "Mật khẩu",
                type="password",
                key="login_password",
                placeholder="Nhập mật khẩu"
            )

            if st.button(
                "Đăng nhập",
                type="primary",
                use_container_width=True
            ):

                if not username.strip() or not password:
                    st.warning("Vui lòng nhập tên đăng nhập và mật khẩu.")

                else:
                    api_logout()

                    success, message = api_login(
                        username.strip(),
                        password
                    )

                    if success:
                        current_user = get_current_user()

                        if current_user:
                            st.session_state.user = current_user
                            st.session_state.logged_in = True
                            st.success("Đăng nhập thành công.")
                            st.rerun()
                        else:
                            api_logout()
                            st.session_state.user = None
                            st.session_state.logged_in = False
                            st.error(
                                "Không lấy được thông tin người dùng. "
                                "Vui lòng đăng nhập lại."
                            )
                    else:
                        st.error(message)

        # -------------------------------------------------
        # ĐĂNG KÝ
        # -------------------------------------------------

        with tab_register:

            st.subheader("Tạo tài khoản mới")
            st.caption("Đăng ký để bắt đầu sử dụng hệ thống.")

            new_username = st.text_input(
                "Tên đăng nhập",
                key="register_username"
            )

            new_email = st.text_input(
                "Email",
                key="register_email"
            )

            new_password = st.text_input(
                "Mật khẩu",
                type="password",
                key="register_password"
            )

            confirm_password = st.text_input(
                "Xác nhận mật khẩu",
                type="password",
                key="confirm_password"
            )

            if st.button(
                "Tạo tài khoản",
                type="primary",
                use_container_width=True
            ):

                if not new_username.strip():
                    st.error("Vui lòng nhập tên đăng nhập.")

                elif not new_email.strip():
                    st.error("Vui lòng nhập email.")

                elif not new_password:
                    st.error("Vui lòng nhập mật khẩu.")

                elif new_password != confirm_password:
                    st.error("Mật khẩu xác nhận không khớp.")

                else:
                    success, result = api_register(
                        new_username.strip(),
                        new_email.strip(),
                        new_password
                    )

                    if success:
                        st.success("Đăng ký tài khoản thành công.")
                        st.info(
                            "Bạn có thể chuyển sang tab Đăng nhập."
                        )
                    else:
                        st.error(result)

        st.markdown('</div>', unsafe_allow_html=True)


# =====================================================
# 6. TRANG TỔNG QUAN
# =====================================================

def show_dashboard():

    transactions, categories = load_data()

    show_page_title(
        "Tổng quan tài chính",
        "Theo dõi tình hình thu nhập và chi tiêu của bạn."
    )

    username = get_user_value("username") or "Bạn"

    st.markdown(f"""
    <div class="dashboard-banner">
        <h2>Xin chào, {username} 👋</h2>
        <p>
            Đây là tổng quan tình hình tài chính cá nhân của bạn.
            Hãy theo dõi thu nhập và chi tiêu thường xuyên nhé!
        </p>
    </div>
    """, unsafe_allow_html=True)

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
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">💰</div>
            <div class="metric-label">TỔNG THU NHẬP</div>
            <div class="metric-value" style="color:#15966b;">
                {format_money(total_income)}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">💸</div>
            <div class="metric-label">TỔNG CHI TIÊU</div>
            <div class="metric-value" style="color:#df6868;">
                {format_money(total_expense)}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        balance_color = "#15966b" if balance >= 0 else "#df6868"

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">📊</div>
            <div class="metric-label">SỐ DƯ HIỆN TẠI</div>
            <div class="metric-value" style="color:{balance_color};">
                {format_money(balance)}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    left, right = st.columns([1.5, 1])

    with left:

        st.markdown(
            '<div class="content-card">',
            unsafe_allow_html=True
        )
        st.subheader("Biến động thu và chi")

        if transactions:

            df = transaction_dataframe(
                transactions, categories
            )

            df["Tháng"] = pd.to_datetime(
                df["Ngày"]
            ).dt.to_period("M").astype(str)

            monthly = df.pivot_table(
                index="Tháng",
                columns="Loại",
                values="Số tiền",
                aggfunc="sum",
                fill_value=0
            )

            st.bar_chart(monthly)

        else:
            st.info("Chưa có dữ liệu giao dịch để hiển thị.")

        st.markdown('</div>', unsafe_allow_html=True)

    with right:

        st.markdown(
            '<div class="content-card">',
            unsafe_allow_html=True
        )
        st.subheader("Tình hình chi tiêu")

        if total_income > 0:
            expense_ratio = total_expense / total_income * 100
        else:
            expense_ratio = 0

        st.metric(
            "Tỷ lệ chi tiêu trên thu nhập",
            f"{expense_ratio:.1f}%"
        )

        st.progress(min(expense_ratio / 100, 1.0))

        if total_income == 0 and total_expense == 0:
            st.info("Hãy thêm giao dịch để xem phân tích.")
        elif expense_ratio > 100:
            st.error("Chi tiêu đang vượt quá tổng thu nhập.")
        elif expense_ratio >= 80:
            st.warning("Bạn nên chú ý kiểm soát chi tiêu.")
        else:
            st.success(
                "Tình hình chi tiêu đang trong mức hợp lý."
            )

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="content-card">',
        unsafe_allow_html=True
    )
    st.subheader("Giao dịch gần đây")

    if transactions:

        recent = sorted(
            transactions,
            key=lambda item: item.transaction_date,
            reverse=True
        )[:5]

        recent_df = transaction_dataframe(
            recent, categories
        )

        st.dataframe(
            recent_df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("Bạn chưa có giao dịch nào.")

    st.markdown('</div>', unsafe_allow_html=True)


# =====================================================
# 7. QUẢN LÝ GIAO DỊCH
# =====================================================

def show_transactions():

    show_page_title(
        "Quản lý giao dịch",
        "Thêm, chỉnh sửa, xóa và tìm kiếm các khoản thu chi."
    )

    transactions, categories = load_data()

    tab_add, tab_list, tab_import = st.tabs([
        "➕ Thêm giao dịch",
        "📋 Danh sách giao dịch",
        "📥 Nhập CSV"
    ])

    # -------------------------------------------------
    # THÊM GIAO DỊCH
    # -------------------------------------------------

    with tab_add:

        st.subheader("Tạo giao dịch mới")

        with st.form("add_transaction_form"):

            transaction_type = st.selectbox(
                "Loại giao dịch",
                ["expense", "income"],
                format_func=lambda x: (
                    "Chi tiêu" if x == "expense"
                    else "Thu nhập"
                )
            )

            available_categories = get_category_options(
                categories,
                transaction_type
            )

            if available_categories:

                category_map = {
                    item.name: item.id
                    for item in available_categories
                }

                selected_category = st.selectbox(
                    "Danh mục",
                    list(category_map.keys())
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
                step=10000
            )

            description = st.text_input(
                "Mô tả",
                placeholder="Ví dụ: Ăn sáng, tiền lương..."
            )

            transaction_date = st.date_input(
                "Ngày giao dịch",
                value=date.today()
            )

            submitted = st.form_submit_button(
                "Lưu giao dịch",
                type="primary",
                use_container_width=True
            )

            if submitted:

                if not available_categories:
                    st.error("Bạn cần tạo danh mục trước.")

                elif amount <= 0:
                    st.error("Số tiền phải lớn hơn 0.")

                else:

                    category_id = category_map[selected_category]

                    with get_session() as session:
                        success, message = add_transaction(
                            session,
                            get_user_id(),
                            category_id,
                            transaction_type,
                            Decimal(str(amount)),
                            description,
                            transaction_date
                        )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    # -------------------------------------------------
    # DANH SÁCH VÀ CHỈNH SỬA GIAO DỊCH
    # -------------------------------------------------

    with tab_list:

        st.subheader("Danh sách giao dịch")

        search_text = st.text_input(
            "Tìm kiếm theo mô tả hoặc danh mục",
            placeholder="Nhập nội dung cần tìm..."
        )

        filter_type = st.selectbox(
            "Lọc theo loại",
            ["Tất cả", "Thu nhập", "Chi tiêu"]
        )

        filtered = transactions

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

        if search_text:
            keyword = search_text.lower()

            filtered = [
                item for item in filtered
                if keyword in (item.description or "").lower()
                or keyword in category_name(
                    item.category_id, categories
                ).lower()
            ]

        if filtered:

            df = transaction_dataframe(
                filtered, categories
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.divider()
            st.subheader("Chỉnh sửa hoặc xóa giao dịch")

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
                list(transaction_map.keys())
            )

            selected_transaction = transaction_map[selected_label]

            edit_categories = get_category_options(
                categories,
                selected_transaction.transaction_type
            )

            with st.form("edit_transaction_form"):

                category_labels = {
                    item.name: item.id
                    for item in edit_categories
                }

                current_category = category_name(
                    selected_transaction.category_id,
                    categories
                )

                category_names = list(category_labels.keys())

                default_category_index = (
                    category_names.index(current_category)
                    if current_category in category_names
                    else 0
                )

                new_category = st.selectbox(
                    "Danh mục",
                    category_names,
                    index=default_category_index
                )

                new_amount = st.number_input(
                    "Số tiền",
                    min_value=1,
                    value=int(selected_transaction.amount)
                )

                new_description = st.text_input(
                    "Mô tả",
                    value=selected_transaction.description or ""
                )

                new_date = st.date_input(
                    "Ngày giao dịch",
                    value=selected_transaction.transaction_date
                )

                save_edit = st.form_submit_button(
                    "Lưu thay đổi",
                    type="primary"
                )

                if save_edit:

                    with get_session() as session:
                        success, message = update_transaction(
                            session,
                            get_user_id(),
                            selected_transaction.id,
                            category_labels[new_category],
                            selected_transaction.transaction_type,
                            Decimal(str(new_amount)),
                            new_description,
                            new_date
                        )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

            if st.button(
                "🗑️ Xóa giao dịch này",
                type="secondary"
            ):

                with get_session() as session:
                    success, message = delete_transaction(
                        session,
                        get_user_id(),
                        selected_transaction.id
                    )

                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

        else:
            st.info("Không tìm thấy giao dịch phù hợp.")

    # -------------------------------------------------
    # NHẬP CSV
    # -------------------------------------------------

    with tab_import:

        st.subheader("Nhập giao dịch từ CSV")

        st.caption(
            "File CSV cần có các cột: "
            "Ngày, Loại, Danh mục, Số tiền, Mô tả."
        )

        uploaded_file = st.file_uploader(
            "Chọn file CSV",
            type=["csv"]
        )

        if uploaded_file is not None:

            try:
                content = uploaded_file.getvalue().decode(
                    "utf-8-sig"
                )

                imported_df = pd.read_csv(StringIO(content))

                st.write("Xem trước dữ liệu:")
                st.dataframe(
                    imported_df.head(),
                    use_container_width=True
                )

                if st.button(
                    "Tiến hành nhập dữ liệu",
                    type="primary"
                ):

                    required_columns = [
                        "Ngày",
                        "Loại",
                        "Danh mục",
                        "Số tiền",
                        "Mô tả"
                    ]

                    if not all(
                        column in imported_df.columns
                        for column in required_columns
                    ):
                        st.error(
                            "File CSV thiếu một hoặc nhiều cột bắt buộc."
                        )

                    else:

                        success_count = 0
                        error_count = 0

                        category_lookup = {
                            (
                                item.name.lower(),
                                item.category_type
                            ): item.id
                            for item in categories
                        }

                        for _, row in imported_df.iterrows():

                            try:
                                raw_type = str(
                                    row["Loại"]
                                ).strip().lower()

                                if raw_type in ["chi tiêu", "expense"]:
                                    transaction_type = "expense"

                                elif raw_type in ["thu nhập", "income"]:
                                    transaction_type = "income"

                                else:
                                    raise ValueError(
                                        "Loại giao dịch không hợp lệ"
                                    )

                                category_key = (
                                    str(row["Danh mục"]).strip().lower(),
                                    transaction_type
                                )

                                category_id = category_lookup.get(
                                    category_key
                                )

                                if category_id is None:
                                    raise ValueError(
                                        "Không tìm thấy danh mục"
                                    )

                                transaction_date = pd.to_datetime(
                                    row["Ngày"]
                                ).date()

                                amount = Decimal(str(row["Số tiền"]))

                                if amount <= 0:
                                    raise ValueError(
                                        "Số tiền không hợp lệ"
                                    )

                                description = str(row["Mô tả"])

                                with get_session() as session:
                                    success, message = add_transaction(
                                        session,
                                        get_user_id(),
                                        category_id,
                                        transaction_type,
                                        amount,
                                        description,
                                        transaction_date
                                    )

                                if success:
                                    success_count += 1
                                else:
                                    error_count += 1

                            except Exception:
                                error_count += 1

                        st.success(
                            f"Đã nhập thành công {success_count} giao dịch."
                        )

                        if error_count:
                            st.warning(
                                f"Có {error_count} dòng chưa được nhập."
                            )

                        st.rerun()

            except Exception as error:
                st.error(f"Không thể đọc file CSV: {error}")


# =====================================================
# 8. QUẢN LÝ DANH MỤC
# =====================================================

def show_categories():

    show_page_title(
        "Quản lý danh mục",
        "Phân loại các khoản thu nhập và chi tiêu."
    )

    categories = load_data()[1]

    tab_add, tab_list = st.tabs([
        "➕ Thêm danh mục",
        "📋 Danh sách danh mục"
    ])

    with tab_add:

        st.subheader("Tạo danh mục mới")

        with st.form("add_category_form"):

            name = st.text_input(
                "Tên danh mục",
                placeholder="Ví dụ: Ăn uống, Lương, Di chuyển..."
            )

            category_type = st.selectbox(
                "Loại danh mục",
                ["expense", "income"],
                format_func=lambda x: (
                    "Chi tiêu" if x == "expense"
                    else "Thu nhập"
                )
            )

            submitted = st.form_submit_button(
                "Thêm danh mục",
                type="primary"
            )

            if submitted:

                with get_session() as session:
                    success, message = add_category(
                        session,
                        get_user_id(),
                        name,
                        category_type
                    )

                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

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
                    )
                }
                for item in categories
            ])

            st.dataframe(
                category_df,
                use_container_width=True,
                hide_index=True
            )

            st.divider()
            st.subheader("Xóa danh mục")

            selected_category = st.selectbox(
                "Chọn danh mục cần xóa",
                categories,
                format_func=lambda x: (
                    f"{x.name} - "
                    f"{'Thu nhập' if x.category_type == 'income' else 'Chi tiêu'}"
                )
            )

            if st.button("Xóa danh mục"):

                transactions = load_data()[0]

                is_used = any(
                    item.category_id == selected_category.id
                    for item in transactions
                )

                if is_used:
                    st.error(
                        "Không thể xóa danh mục đang có giao dịch. "
                        "Hãy chỉnh sửa hoặc xóa giao dịch liên quan trước."
                    )

                else:
                    with get_session() as session:
                        success, message = delete_category(
                            session,
                            get_user_id(),
                            selected_category.id
                        )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        else:
            st.info("Bạn chưa có danh mục nào.")


# =====================================================
# 9. THỐNG KÊ VÀ PHÂN TÍCH
# =====================================================

def show_statistics():

    show_page_title(
        "Thống kê và phân tích",
        "Phân tích thu nhập, chi tiêu theo thời gian và danh mục."
    )

    transactions, categories = load_data()

    if not transactions:
        st.info("Chưa có dữ liệu để thống kê.")
        return

    df = transaction_dataframe(transactions, categories)
    df["Ngày"] = pd.to_datetime(df["Ngày"])

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Từ ngày",
            value=min(df["Ngày"]).date()
        )

    with col2:
        end_date = st.date_input(
            "Đến ngày",
            value=max(df["Ngày"]).date()
        )

    if start_date > end_date:
        st.error("Ngày bắt đầu không được lớn hơn ngày kết thúc.")
        return

    filtered_df = df[
        (df["Ngày"].dt.date >= start_date)
        & (df["Ngày"].dt.date <= end_date)
    ].copy()

    if filtered_df.empty:
        st.warning("Không có giao dịch trong khoảng thời gian này.")
        return

    income = filtered_df.loc[
        filtered_df["Loại"] == "Thu nhập",
        "Số tiền"
    ].sum()

    expense = filtered_df.loc[
        filtered_df["Loại"] == "Chi tiêu",
        "Số tiền"
    ].sum()

    balance = income - expense

    col1, col2, col3 = st.columns(3)

    col1.metric("Tổng thu nhập", format_money(income))
    col2.metric("Tổng chi tiêu", format_money(expense))
    col3.metric("Chênh lệch", format_money(balance))

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
            fill_value=0
        )

        st.bar_chart(monthly)

    with right:

        st.subheader("Chi tiêu theo danh mục")

        expense_df = filtered_df[
            filtered_df["Loại"] == "Chi tiêu"
        ]

        if not expense_df.empty:

            category_stats = (
                expense_df.groupby("Danh mục")["Số tiền"]
                .sum()
                .sort_values(ascending=False)
            )

            st.bar_chart(category_stats)

        else:
            st.info("Chưa có khoản chi tiêu nào.")

    st.divider()
    st.subheader("Nhận xét tài chính")

    if income > 0:

        ratio = expense / income * 100

        st.write(
            f"Tỷ lệ chi tiêu trên thu nhập: **{ratio:.1f}%**"
        )

        if ratio > 100:
            st.error(
                "Bạn đang chi tiêu nhiều hơn thu nhập trong "
                "khoảng thời gian đã chọn."
            )

        elif ratio >= 80:
            st.warning(
                "Mức chi tiêu khá cao. Bạn nên cân nhắc "
                "giảm những khoản chưa cần thiết."
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


# =====================================================
# 10. XUẤT DỮ LIỆU
# =====================================================

def show_export():

    show_page_title(
        "Xuất dữ liệu",
        "Tải xuống dữ liệu giao dịch để lưu trữ và báo cáo."
    )

    transactions, categories = load_data()

    if not transactions:
        st.info("Chưa có dữ liệu để xuất.")
        return

    df = transaction_dataframe(transactions, categories)

    st.subheader("Xem trước dữ liệu")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        csv_data = df.to_csv(
            index=False,
            encoding="utf-8-sig"
        )

        st.download_button(
            label="📄 Tải xuống CSV",
            data=csv_data,
            file_name="giao_dich_ca_nhan.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col2:

        excel_buffer = BytesIO()

        with pd.ExcelWriter(
            excel_buffer,
            engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                sheet_name="Giao dịch",
                index=False
            )

            summary = pd.DataFrame([
                {
                    "Chỉ tiêu": "Tổng thu nhập",
                    "Số tiền": df.loc[
                        df["Loại"] == "Thu nhập",
                        "Số tiền"
                    ].sum()
                },
                {
                    "Chỉ tiêu": "Tổng chi tiêu",
                    "Số tiền": df.loc[
                        df["Loại"] == "Chi tiêu",
                        "Số tiền"
                    ].sum()
                }
            ])

            summary.to_excel(
                writer,
                sheet_name="Tổng quan",
                index=False
            )

        st.download_button(
            label="📊 Tải xuống Excel",
            data=excel_buffer.getvalue(),
            file_name="bao_cao_chi_tieu.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True
        )


# =====================================================
# 11. GIAO DIỆN SAU KHI ĐĂNG NHẬP
# =====================================================

def show_main_app():

    user = st.session_state.user
    username = get_user_value("username") or "Người dùng"

    with st.sidebar:

        st.markdown("""
        <div style="padding: 15px 5px 25px 5px;">
            <div style="
                font-size: 30px;
                font-weight: 800;
                color: white;
            ">
                💳 Expense Manager
            </div>
            <div style="
                color: #a8bbcf;
                font-size: 11px;
                letter-spacing: 2px;
                margin-top: 5px;
            ">
                PERSONAL FINANCE
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### TÀI CHÍNH CÁ NHÂN")

        menu = st.radio(
            "Điều hướng",
            [
                "Tổng quan",
                "Quản lý giao dịch",
                "Quản lý danh mục",
                "Thống kê",
                "Xuất dữ liệu"
            ],
            label_visibility="collapsed"
        )

        st.markdown("---")

        st.markdown(f"""
        <div style="
            background: #263d59;
            padding: 15px;
            border-radius: 12px;
            margin-top: 15px;
        ">
            <div style="font-size: 23px;">👤</div>
            <div style="
                font-weight: 700;
                margin-top: 7px;
            ">
                {username}
            </div>
            <div style="
                color: #a8bbcf;
                font-size: 12px;
            ">
                Tài khoản cá nhân
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")

        if st.button(
            "Đăng xuất",
            use_container_width=True
        ):

            api_logout()
            st.session_state.user = None
            st.session_state.logged_in = False
            st.rerun()

        st.markdown("""
        <div style="
            position: relative;
            margin-top: 35px;
            color: #8fa3b9;
            font-size: 11px;
            text-align: center;
        ">
            Personal Expense Management
            <br>
            Version 1.0
        </div>
        """, unsafe_allow_html=True)

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


# =====================================================
# 12. CHẠY ỨNG DỤNG
# =====================================================

if st.session_state.logged_in and st.session_state.user:
    show_main_app()
else:
    show_auth_page()
