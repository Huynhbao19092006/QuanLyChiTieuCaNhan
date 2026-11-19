import streamlit as st


def initialize_session():
    """Initialize authentication keys once without overwriting existing state."""
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("access_token", None)
    st.session_state.setdefault("token_type", None)
    st.session_state.setdefault("main_navigation", "Tổng quan")
    st.session_state.setdefault("flash_notifications", [])


def is_logged_in():
    return bool(
        st.session_state.get("logged_in", False)
        and st.session_state.get("user") is not None
    )


def get_user_value(field):
    user = st.session_state.get("user")
    if user is None:
        return None
    if isinstance(user, dict):
        return user.get(field)
    return getattr(user, field, None)


def get_user_id():
    return get_user_value("id")


def restore_authenticated_session(get_current_user, logout):
    """Restore the user after a Streamlit rerun when a token exists."""
    initialize_session()

    token = st.session_state.get("access_token")
    user = st.session_state.get("user")

    if not token:
        st.session_state["logged_in"] = False
        st.session_state["user"] = None
        return

    if user is not None:
        st.session_state["logged_in"] = True
        return

    try:
        current_user = get_current_user()
    except Exception:
        logout()
        st.session_state["user"] = None
        st.session_state["logged_in"] = False
        st.session_state["access_token"] = None
        return

    if current_user:
        st.session_state["user"] = current_user
        st.session_state["logged_in"] = True
        return

    logout()
    st.session_state["user"] = None
    st.session_state["logged_in"] = False
    st.session_state["access_token"] = None



