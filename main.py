"""Điểm khởi động ứng dụng Streamlit: streamlit run main.py"""

import streamlit as st

st.set_page_config(
    page_title="Quản lý chi tiêu cá nhân",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.layout import show_main_app  # noqa: E402
from ui.notifications import flush_notifications  # noqa: E402
from ui.session import init_session  # noqa: E402
from ui.styles import apply_page_styles  # noqa: E402
from ui.views.auth import show_auth_page  # noqa: E402


init_session()
apply_page_styles()
flush_notifications()

if st.session_state.logged_in and st.session_state.user:
    show_main_app()
else:
    show_auth_page()
