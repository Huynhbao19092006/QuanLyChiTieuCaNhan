"""Nạp CSS dùng chung và CSS theo từng trang."""

from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
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


def apply_page_styles():
    """Nạp CSS phù hợp với trạng thái đăng nhập và trang hiện tại."""
    if st.session_state.logged_in:
        current_page = st.session_state.get(
            "main_navigation",
            "Tổng quan",
        )
        page_style = PAGE_STYLES.get(current_page)
        load_css([page_style] if page_style else [])
    else:
        load_css(["auth.css"])
