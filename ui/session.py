"""Khởi tạo và khôi phục session đăng nhập."""

import streamlit as st

from api_client import (
    get_current_user,
    logout as api_logout,
)


def init_session():
    """Khởi tạo session và khôi phục người dùng khi tải lại trang.

    Phải gọi ở mỗi lần Streamlit chạy lại script (không đặt ở mức module,
    vì module chỉ được import một lần).
    """
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
