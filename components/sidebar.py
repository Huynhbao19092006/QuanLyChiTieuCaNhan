"""Navigation sidebar."""

import html

import streamlit as st


MENU_ITEMS = {
    "Tổng quan": "⌂  Tổng quan",
    "Giao dịch": "↔  Giao dịch",
    "Thu nhập": "↗  Thu nhập",
    "Chi tiêu": "↘  Chi tiêu",
    "Danh mục": "▦  Danh mục",
    "Ngân sách": "◷  Ngân sách",
    "Thống kê": "◒  Thống kê",
    "Xuất dữ liệu": "⇩  Xuất dữ liệu",
    "Hồ sơ cá nhân": "◉  Hồ sơ cá nhân",
}


def render(username, on_logout):
    with st.sidebar:
        st.markdown("## 💳 Expense Manager")
        st.caption("PERSONAL FINANCE")
        st.divider()
        menu = st.radio(
            "Điều hướng",
            list(MENU_ITEMS),
            format_func=MENU_ITEMS.get,
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
            on_logout()
        return menu
