"""Sidebar điều hướng và định tuyến các trang sau khi đăng nhập."""

import html

import streamlit as st

from api_client import (
    logout as api_logout,
)
from ui.helpers import get_user_value
from ui.views.categories import show_categories
from ui.views.dashboard import show_dashboard
from ui.views.export import show_export
from ui.views.profile import show_profile
from ui.views.statistics import show_statistics
from ui.views.transactions import show_transactions


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
