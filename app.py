"""Streamlit application bootstrap and page router."""

import streamlit as st

from api_client import get_current_user, logout as api_logout
from components.notifications import flush_notifications
from utils.session import (
    initialize_session,
    is_logged_in,
    restore_authenticated_session,
)
from utils.ui_helpers import load_css
from components.sidebar import render as render_sidebar
from pages import auth, dashboard, transactions, categories, budget
from pages import statistics, export, profile

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

st.set_page_config(
    page_title="Quản lý chi tiêu cá nhân",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _logout():
    api_logout()
    st.session_state["user"] = None
    st.session_state["logged_in"] = False
    st.session_state["access_token"] = None
    st.rerun()


def render_authenticated_app():
    from utils.session import get_user_value

    username = get_user_value("username") or "Người dùng"
    menu = render_sidebar(username, _logout)
    style = PAGE_STYLES.get(menu)
    if style:
        load_css([style])

    if menu == "Tổng quan":
        dashboard.show_dashboard()
    elif menu == "Giao dịch":
        transactions.show_transactions()
    elif menu == "Thu nhập":
        transactions.show_transactions("income")
    elif menu == "Chi tiêu":
        transactions.show_transactions("expense")
    elif menu == "Danh mục":
        categories.show_categories()
    elif menu == "Ngân sách":
        budget.render()
    elif menu == "Thống kê":
        statistics.show_statistics()
    elif menu == "Xuất dữ liệu":
        export.show_export()
    elif menu == "Hồ sơ cá nhân":
        profile.show_profile()


def run_app():
    """Render the authenticated page or the login/register screen."""
    initialize_session()
    restore_authenticated_session(get_current_user, api_logout)

    if is_logged_in():
        load_css([PAGE_STYLES.get(
            st.session_state.get("main_navigation", "Tổng quan"),
        )])
    else:
        load_css(["auth.css"])

    flush_notifications()

    if is_logged_in():
        render_authenticated_app()
    else:
        auth.show_auth_page()


if __name__ == "__main__":
    run_app()
