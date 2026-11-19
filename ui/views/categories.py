"""Quản lý danh mục."""

import pandas as pd
import streamlit as st

from api_client import (
    create_category_api,
    update_category_api,
    delete_category_api,
)
from ui.helpers import get_api_error, load_data, show_page_title
from ui.notifications import queue_notification


def show_categories():
    show_page_title(
        "Quản lý danh mục",
        "Phân loại các khoản thu nhập và chi tiêu.",
    )

    transactions, categories = load_data()
    category_load_error = st.session_state.get(
        "category_load_error"
    )
    transaction_load_error = st.session_state.get(
        "transaction_load_error"
    )
    category_map = {
        (
            f"#{item.id} - {item.name} - "
            f"{'Thu nhập' if item.category_type == 'income' else 'Chi tiêu'}"
        ): item
        for item in categories
    }

    tab_add, tab_list = st.tabs([
        "➕ Thêm danh mục",
        "📋 Danh sách danh mục",
    ])

    with tab_add:
        st.subheader("Tạo danh mục mới")

        with st.form("add_category_form"):
            name = st.text_input(
                "Tên danh mục",
                placeholder="Ví dụ: Ăn uống, Lương, Di chuyển...",
            )
            category_type = st.selectbox(
                "Loại danh mục",
                ["expense", "income"],
                format_func=lambda value: (
                    "Chi tiêu" if value == "expense" else "Thu nhập"
                ),
            )
            submitted = st.form_submit_button(
                "Thêm danh mục",
                type="primary",
            )

            if submitted:
                if not name.strip():
                    st.error("Vui lòng nhập tên danh mục.")
                elif any(
                    item.name.strip().casefold() == name.strip().casefold()
                    and item.category_type == category_type
                    for item in categories
                ):
                    st.error("Danh mục này đã tồn tại.")
                else:
                    try:
                        success, result = create_category_api(
                            name.strip(),
                            category_type,
                        )
                        if success:
                            queue_notification(
                                "success",
                                "Thêm danh mục thành công!",
                            )
                            st.rerun()
                        else:
                            st.error(get_api_error(result))
                    except Exception as error:
                        st.error(f"Không thể tạo danh mục: {error}")

    with tab_list:
        if category_load_error:
            st.error(category_load_error)
        elif categories:
            for category_type, title in (
                ("income", "Danh mục Thu nhập"),
                ("expense", "Danh mục Chi tiêu"),
            ):
                grouped_categories = [
                    item
                    for item in categories
                    if item.category_type == category_type
                ]
                st.subheader(title)
                if grouped_categories:
                    category_df = pd.DataFrame([
                        {
                            "ID": item.id,
                            "Tên danh mục": item.name,
                            "Loại": title.replace(
                                "Danh mục ",
                                "",
                            ),
                        }
                        for item in grouped_categories
                    ])
                    st.dataframe(
                        category_df,
                        width="stretch",
                        hide_index=True,
                    )
                else:
                    st.info("Chưa có danh mục thuộc nhóm này.")

            st.divider()
            st.subheader("Chỉnh sửa danh mục")

            edit_category = st.selectbox(
                "Chọn danh mục cần chỉnh sửa",
                list(category_map.keys()),
                key="edit_category_select",
            )
            selected_edit_category = category_map[edit_category]

            with st.form("edit_category_form"):
                edited_name = st.text_input(
                    "Tên danh mục mới",
                    value=selected_edit_category.name,
                )
                edited_type = st.selectbox(
                    "Loại danh mục mới",
                    ["expense", "income"],
                    index=(
                        0
                        if selected_edit_category.category_type == "expense"
                        else 1
                    ),
                    format_func=lambda value: (
                        "Chi tiêu"
                        if value == "expense"
                        else "Thu nhập"
                    ),
                )
                save_category = st.form_submit_button(
                    "Lưu danh mục",
                    type="primary",
                )

                if save_category:
                    if not edited_name.strip():
                        st.error("Vui lòng nhập tên danh mục.")
                    elif (
                        edited_type != selected_edit_category.category_type
                        and transaction_load_error
                    ):
                        st.error(
                            "Không thể đổi loại danh mục khi chưa tải "
                            "được các giao dịch liên quan."
                        )
                    elif (
                        edited_type != selected_edit_category.category_type
                        and any(
                            item.category_id == selected_edit_category.id
                            for item in transactions
                        )
                    ):
                        st.error(
                            "Không thể đổi loại danh mục đang được "
                            "giao dịch sử dụng."
                        )
                    else:
                        try:
                            success, result = update_category_api(
                                selected_edit_category.id,
                                edited_name,
                                edited_type,
                            )
                            if success:
                                queue_notification(
                                    "success",
                                    "Cập nhật danh mục thành công!",
                                )
                                st.rerun()
                            else:
                                st.error(get_api_error(result))
                        except Exception as error:
                            st.error(
                                f"Không thể cập nhật danh mục: {error}"
                            )

            st.divider()
            st.subheader("Xóa danh mục")

            selected_label = st.selectbox(
                "Chọn danh mục cần xóa",
                list(category_map.keys()),
                key="delete_category_select",
            )
            selected_category = category_map[selected_label]

            confirm_delete = st.checkbox(
                "Tôi xác nhận muốn xóa danh mục này.",
                key="confirm_delete_category",
            )

            if st.button(
                "🗑️ Xóa danh mục",
                disabled=not confirm_delete,
            ):
                try:
                    success, result = delete_category_api(
                        selected_category.id
                    )
                    if success:
                        queue_notification(
                            "success",
                            "Xóa danh mục thành công!",
                        )
                        st.rerun()
                    else:
                        st.error(get_api_error(result))
                except Exception as error:
                    st.error(f"Không thể xóa danh mục: {error}")
        else:
            st.info("Bạn chưa có danh mục nào.")
