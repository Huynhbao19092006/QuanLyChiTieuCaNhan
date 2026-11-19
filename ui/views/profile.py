"""Hồ sơ cá nhân."""

import html
import re

import streamlit as st

from api_client import (
    update_profile_api,
    change_password_api,
    logout as api_logout,
)
from ui.helpers import get_api_error, get_user_value, show_page_title
from ui.notifications import queue_notification, show_notification


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
