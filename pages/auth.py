from utils.page_context import *


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
                                st.session_state["user"] = current_user
                                st.session_state["logged_in"] = True
                                queue_notification(
                                    "success",
                                    "Đăng nhập thành công!",
                                )
                                st.rerun()
                            else:
                                api_logout()
                                st.session_state["user"] = None
                                st.session_state["logged_in"] = False
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
