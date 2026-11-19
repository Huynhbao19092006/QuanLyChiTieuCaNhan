"""Thông báo hiển thị ngay hoặc giữ qua lần rerun."""

import streamlit as st


def _render_notification(kind, message):
    renderers = {
        "success": st.success,
        "error": st.error,
        "warning": st.warning,
        "info": st.info,
    }
    renderers.get(kind, st.info)(message)


def queue_notification(kind, message):
    """Lưu thông báo để hiển thị đúng một lần sau lần rerun kế tiếp."""
    notifications = st.session_state.setdefault(
        "flash_notifications",
        [],
    )
    notifications.append({
        "kind": kind,
        "message": message,
    })


def show_notification(kind, message, persist=False):
    """Hiển thị ngay hoặc giữ thông báo qua lần rerun."""
    if persist:
        queue_notification(kind, message)
    else:
        _render_notification(kind, message)


def flush_notifications():
    """Hiển thị rồi xóa các thông báo đã chờ."""
    notifications = st.session_state.pop(
        "flash_notifications",
        [],
    )
    for notification in notifications:
        _render_notification(
            notification["kind"],
            notification["message"],
        )
