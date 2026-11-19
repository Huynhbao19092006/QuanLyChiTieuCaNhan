"""Quản lý giao dịch (tất cả / thu nhập / chi tiêu)."""

from datetime import date
from io import StringIO

import pandas as pd
import streamlit as st

from api_client import (
    create_transaction_api,
    update_transaction_api,
    delete_transaction_api,
)
from ui.helpers import (
    category_label,
    category_lookup_by_id_and_type,
    category_name,
    filter_transactions_by_type,
    format_money,
    get_api_error,
    get_category_options,
    load_data,
    normalize_transaction_type,
    parse_amount,
    show_page_title,
    transaction_dataframe,
)
from ui.notifications import queue_notification, show_notification


def show_transactions(transaction_type=None):
    if transaction_type not in (None, "income", "expense"):
        raise ValueError("Loại giao dịch không hợp lệ.")

    page_transaction_type = transaction_type
    is_filtered_page = page_transaction_type is not None
    page_label = (
        "Thu nhập"
        if page_transaction_type == "income"
        else "Chi tiêu"
        if page_transaction_type == "expense"
        else "Giao dịch"
    )
    show_page_title(
        page_label,
        (
            f"Quản lý các khoản {page_label.lower()}."
            if is_filtered_page
            else "Thêm, chỉnh sửa, xóa và tìm kiếm các khoản thu chi."
        ),
    )

    transactions, categories = load_data()
    if is_filtered_page:
        transactions = filter_transactions_by_type(
            transactions,
            page_transaction_type,
        )

        total_amount = sum(
            item.amount
            for item in transactions
        )
        st.metric(
            f"Tổng {page_label.lower()}",
            format_money(total_amount),
        )
        category_count = st.session_state.get(
            "category_counts",
            {},
        ).get(page_transaction_type, 0)
        st.caption(
            f"Danh mục {page_label.lower()} từ API: "
            f"{category_count} bản ghi."
        )

    tab_add, tab_list, tab_import = st.tabs([
        (
            "➕ Thêm thu nhập"
            if page_transaction_type == "income"
            else "➕ Thêm chi tiêu"
            if page_transaction_type == "expense"
            else "➕ Thêm giao dịch"
        ),
        "📋 Danh sách giao dịch",
        "📥 Nhập CSV",
    ])

    # THÊM GIAO DỊCH
    with tab_add:
        st.subheader("Tạo giao dịch mới")
        category_load_error = st.session_state.get(
            "category_load_error"
        )

        selected_transaction_type = page_transaction_type
        if not is_filtered_page:
            selected_transaction_type = st.selectbox(
                "Loại giao dịch",
                ["expense", "income"],
                format_func=lambda value: (
                    "Chi tiêu" if value == "expense" else "Thu nhập"
                ),
                key="all_add_transaction_type",
            )

        with st.form(
            f"add_{page_transaction_type or 'all'}_transaction_form"
        ):
            available_categories = get_category_options(
                categories,
                selected_transaction_type,
            )
            category_map = {
                category_label(item): item
                for item in available_categories
            }

            if category_load_error:
                selected_category = None
                st.error(category_load_error)
            elif available_categories:
                selected_category = st.selectbox(
                    "Danh mục",
                    list(category_map.keys()),
                    key=(
                        f"add_category_{selected_transaction_type}"
                        if is_filtered_page
                        else f"all_add_category_{selected_transaction_type}"
                    ),
                )
            else:
                selected_category = None
                if is_filtered_page:
                    category_count = st.session_state.get(
                        "category_counts",
                        {},
                    ).get(page_transaction_type, 0)
                    if categories and category_count == 0:
                        st.error(
                            "API đã tải danh mục nhưng không có danh mục "
                            f"loại {page_label.lower()}."
                        )
                    else:
                        st.warning(
                            "Chưa có danh mục "
                            f"{page_label.lower()} phù hợp. "
                            "Hãy tạo danh mục trước."
                        )
                else:
                    st.warning(
                        "Bạn chưa có danh mục phù hợp. "
                        "Hãy tạo danh mục trước."
                    )

            amount = st.number_input(
                "Số tiền (VNĐ)",
                min_value=0,
                step=10000,
            )
            description = st.text_input(
                "Mô tả",
                placeholder="Ví dụ: Ăn sáng, tiền lương...",
            )
            transaction_date = st.date_input(
                "Ngày giao dịch",
                value=date.today(),
            )

            submitted = st.form_submit_button(
                "Lưu giao dịch",
                type="primary",
                width="stretch",
            )

            if submitted:
                if category_load_error:
                    st.error(
                        "Không thể lưu giao dịch khi danh mục chưa tải được."
                    )
                elif not available_categories:
                    st.error(
                        "Bạn cần tạo danh mục phù hợp trước. "
                        "Danh mục thu nhập và chi tiêu được tách riêng."
                    )
                elif amount <= 0:
                    st.error("Số tiền phải lớn hơn 0.")
                else:
                    try:
                        selected_category_item = category_map[
                            selected_category
                        ]
                        if (
                            selected_category_item.category_type
                            != selected_transaction_type
                        ):
                            raise ValueError(
                                "Danh mục không phù hợp với loại giao dịch."
                            )

                        category_id = selected_category_item.id
                        success, result = create_transaction_api(
                            category_id=category_id,
                            transaction_type=selected_transaction_type,
                            amount=parse_amount(amount),
                            description=description.strip(),
                            transaction_date=transaction_date,
                        )

                        if success:
                            queue_notification(
                                "success",
                                "Thêm giao dịch thành công!",
                            )
                            st.rerun()
                        else:
                            st.error(get_api_error(result))
                    except Exception as error:
                        st.error(f"Không thể lưu giao dịch: {error}")

    # DANH SÁCH, SỬA VÀ XÓA GIAO DỊCH
    with tab_list:
        st.subheader("Danh sách giao dịch")

        search_text = st.text_input(
            "Tìm kiếm theo mô tả hoặc danh mục",
            placeholder="Nhập nội dung cần tìm...",
            key=f"{page_transaction_type or 'all'}_transaction_search",
        )
        if not is_filtered_page:
            filter_type = st.selectbox(
                "Lọc theo loại",
                ["Tất cả", "Thu nhập", "Chi tiêu"],
                key="all_transaction_type_filter",
            )
        else:
            filter_type = (
                "Thu nhập"
                if page_transaction_type == "income"
                else "Chi tiêu"
            )

        category_filter_categories = [
            category
            for category in categories
            if (
                not is_filtered_page
                or category.category_type == page_transaction_type
            )
            and any(
                item.category_id == category.id
                and (
                    not is_filtered_page
                    or item.transaction_type == page_transaction_type
                )
                for item in transactions
            )
        ]
        category_filter_map = {
            category_label(category): (
                category.id,
                category.category_type,
            )
            for category in category_filter_categories
        }
        category_filter_options = ["Tất cả"] + sorted(
            category_filter_map.keys()
        )
        selected_category_filter = st.selectbox(
            "Lọc theo danh mục",
            category_filter_options,
            key=f"{page_transaction_type or 'all'}_category_filter",
        )

        filter_start_date = None
        filter_end_date = None
        if transactions:
            transaction_dates = [
                item.transaction_date
                for item in transactions
            ]
            min_transaction_date = min(transaction_dates)
            max_transaction_date = max(transaction_dates)
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                filter_start_date = st.date_input(
                    "Từ ngày",
                    value=min_transaction_date,
                    min_value=min_transaction_date,
                    max_value=max_transaction_date,
                    key=f"{page_transaction_type or 'all'}_start_date",
                )
            with date_col2:
                filter_end_date = st.date_input(
                    "Đến ngày",
                    value=max_transaction_date,
                    min_value=min_transaction_date,
                    max_value=max_transaction_date,
                    key=f"{page_transaction_type or 'all'}_end_date",
                )

        filtered = [
            item
            for item in (
                filter_transactions_by_type(
                    transactions,
                    page_transaction_type,
                )
                if is_filtered_page
                else transactions
            )
        ]

        if not is_filtered_page and filter_type == "Thu nhập":
            filtered = [
                item for item in filtered
                if item.transaction_type == "income"
            ]
        elif not is_filtered_page and filter_type == "Chi tiêu":
            filtered = [
                item for item in filtered
                if item.transaction_type == "expense"
            ]

        if selected_category_filter != "Tất cả":
            selected_category_key = category_filter_map[
                selected_category_filter
            ]
            filtered = [
                item
                for item in filtered
                if (
                    item.category_id,
                    item.transaction_type,
                ) == selected_category_key
            ]

        if filter_start_date and filter_end_date:
            if filter_start_date > filter_end_date:
                st.error("Ngày bắt đầu không được lớn hơn ngày kết thúc.")
                filtered = []
            else:
                filtered = [
                    item
                    for item in filtered
                    if filter_start_date
                    <= item.transaction_date
                    <= filter_end_date
                ]

        if search_text.strip():
            keyword = search_text.strip().casefold()
            filtered = [
                item for item in filtered
                if keyword in (item.description or "").casefold()
                or keyword in category_name(
                    item.category_id,
                    categories,
                ).casefold()
            ]

        if filtered:
            filtered = sorted(
                filtered,
                key=lambda item: item.transaction_date,
                reverse=True,
            )
            df = transaction_dataframe(filtered, categories)
            st.dataframe(
                df,
                width="stretch",
                hide_index=True,
            )

            st.divider()
            st.subheader("Chỉnh sửa hoặc xóa giao dịch")

            transaction_map = {
                (
                    f"#{item.id} - {item.transaction_date} - "
                    f"{item.description or 'Không có mô tả'}"
                ): item
                for item in filtered
            }
            selected_label = st.selectbox(
                "Chọn giao dịch",
                list(transaction_map.keys()),
                key=f"{page_transaction_type or 'all'}_transaction_select",
            )
            selected_transaction = transaction_map[selected_label]

            edit_categories = get_category_options(
                categories,
                selected_transaction.transaction_type,
            )
            edit_transaction_type = normalize_transaction_type(
                selected_transaction.transaction_type
            )

            if not edit_categories:
                st.warning(
                    "Không có danh mục phù hợp để chỉnh sửa."
                )
            else:
                with st.form(
                    (
                        f"edit_{page_transaction_type or 'all'}_"
                        f"transaction_{selected_transaction.id}_"
                        f"{edit_transaction_type}_form"
                    )
                ):
                    category_labels = {
                        category_label(item): item
                        for item in edit_categories
                    }
                    current_category_key = (
                        selected_transaction.category_id,
                        selected_transaction.transaction_type,
                    )
                    category_by_id_and_type = (
                        category_lookup_by_id_and_type(edit_categories)
                    )
                    current_category = category_by_id_and_type.get(
                        current_category_key
                    )
                    category_names = list(category_labels.keys())

                    default_index = (
                        category_names.index(category_label(current_category))
                        if current_category is not None
                        and category_label(current_category)
                        in category_names
                        else 0
                    )

                    new_category = st.selectbox(
                        "Danh mục",
                        category_names,
                        index=default_index,
                        key=(
                            f"edit_category_{selected_transaction.id}_"
                            f"{edit_transaction_type}"
                        ),
                    )
                    new_amount = st.number_input(
                        "Số tiền",
                        min_value=1,
                        value=max(
                            1,
                            int(selected_transaction.amount),
                        ),
                    )
                    new_description = st.text_input(
                        "Mô tả",
                        value=selected_transaction.description or "",
                    )
                    new_date = st.date_input(
                        "Ngày giao dịch",
                        value=selected_transaction.transaction_date,
                        key=(
                            f"edit_date_{selected_transaction.id}_"
                            f"{edit_transaction_type}"
                        ),
                    )
                    save_edit = st.form_submit_button(
                        "Lưu thay đổi",
                        type="primary",
                    )

                    if save_edit:
                        try:
                            selected_edit_category = category_labels[
                                new_category
                            ]
                            if (
                                selected_edit_category.category_type
                                != edit_transaction_type
                            ):
                                raise ValueError(
                                    "Danh mục không phù hợp với loại "
                                    "giao dịch đang sửa."
                                )

                            success, result = update_transaction_api(
                                transaction_id=selected_transaction.id,
                                category_id=selected_edit_category.id,
                                transaction_type=(
                                    edit_transaction_type
                                ),
                                amount=parse_amount(new_amount),
                                description=new_description.strip(),
                                transaction_date=new_date,
                            )

                            if success:
                                queue_notification(
                                    "success",
                                    "Cập nhật giao dịch thành công!",
                                )
                                st.rerun()
                            else:
                                st.error(get_api_error(result))
                        except Exception as error:
                            st.error(
                                f"Không thể cập nhật giao dịch: {error}"
                            )

            st.divider()
            confirm_delete = st.checkbox(
                "Tôi xác nhận muốn xóa giao dịch đã chọn.",
                key=(
                    f"{page_transaction_type or 'all'}"
                    "_confirm_delete_transaction"
                ),
            )

            if st.button(
                "🗑️ Xóa giao dịch này",
                disabled=not confirm_delete,
            ):
                try:
                    success, result = delete_transaction_api(
                        selected_transaction.id
                    )

                    if success:
                        queue_notification(
                            "success",
                            "Xóa giao dịch thành công!",
                        )
                        st.rerun()
                    else:
                        st.error(get_api_error(result))
                except Exception as error:
                    st.error(f"Không thể xóa giao dịch: {error}")
        else:
            st.info("Không tìm thấy giao dịch phù hợp.")

    # NHẬP GIAO DỊCH TỪ CSV
    with tab_import:
        st.subheader("Nhập giao dịch từ CSV")
        st.caption(
            "File CSV cần có các cột: "
            "Ngày, Loại, Danh mục, Số tiền, Mô tả."
        )
        st.info(
            "Loại giao dịch có thể ghi: "
            "Thu nhập, Chi tiêu, income hoặc expense."
        )

        uploaded_file = st.file_uploader(
            "Chọn file CSV",
            type=["csv"],
            key=f"{page_transaction_type or 'all'}_transaction_csv_upload",
        )

        if uploaded_file is not None:
            try:
                content = uploaded_file.getvalue().decode("utf-8-sig")
                imported_df = pd.read_csv(StringIO(content))

                required_columns = [
                    "Ngày",
                    "Loại",
                    "Danh mục",
                    "Số tiền",
                    "Mô tả",
                ]
                missing_columns = [
                    column for column in required_columns
                    if column not in imported_df.columns
                ]

                if missing_columns:
                    st.error(
                        "File CSV thiếu cột: "
                        + ", ".join(missing_columns)
                    )
                elif imported_df.empty:
                    st.warning("File CSV không có dữ liệu.")
                else:
                    st.write("Xem trước dữ liệu:")
                    st.dataframe(
                        imported_df.head(10),
                        width="stretch",
                        hide_index=True,
                    )

                    if st.button(
                        "Tiến hành nhập dữ liệu",
                        type="primary",
                        key=f"{page_transaction_type or 'all'}_import_csv_button",
                    ):
                        success_count = 0
                        error_count = 0
                        error_details = []

                        category_lookup = {
                            (
                                item.name.strip().casefold(),
                                item.category_type,
                            ): item.id
                            for item in categories
                        }
                        category_id_lookup = (
                            category_lookup_by_id_and_type(categories)
                        )

                        for index, row in imported_df.iterrows():
                            try:
                                raw_type = str(
                                    row["Loại"]
                                ).strip().casefold()

                                if raw_type in ["chi tiêu", "expense"]:
                                    row_transaction_type = "expense"
                                elif raw_type in ["thu nhập", "income"]:
                                    row_transaction_type = "income"
                                else:
                                    raise ValueError(
                                        "Loại giao dịch không hợp lệ."
                                    )

                                if (
                                    is_filtered_page
                                    and row_transaction_type
                                    != page_transaction_type
                                ):
                                    raise ValueError(
                                        "Dòng dữ liệu không thuộc trang "
                                        f"{page_label.lower()}."
                                    )

                                raw_category_id = row.get("Danh mục ID")
                                if (
                                    raw_category_id is not None
                                    and not pd.isna(raw_category_id)
                                ):
                                    category_id = int(raw_category_id)
                                    if (
                                        category_id,
                                        row_transaction_type,
                                    ) not in category_id_lookup:
                                        raise ValueError(
                                            "ID danh mục không phù hợp "
                                            "với loại giao dịch."
                                        )
                                else:
                                    category_key = (
                                        str(row["Danh mục"])
                                        .strip()
                                        .casefold(),
                                        row_transaction_type,
                                    )
                                    category_id = category_lookup.get(
                                        category_key
                                    )

                                if category_id is None:
                                    raise ValueError(
                                        "Không tìm thấy danh mục phù hợp."
                                    )

                                transaction_date = pd.to_datetime(
                                    row["Ngày"],
                                    errors="raise",
                                ).date()
                                amount = parse_amount(row["Số tiền"])
                                description = (
                                    ""
                                    if pd.isna(row["Mô tả"])
                                    else str(row["Mô tả"]).strip()
                                )

                                success, result = create_transaction_api(
                                    category_id=category_id,
                                    transaction_type=row_transaction_type,
                                    amount=amount,
                                    description=description,
                                    transaction_date=transaction_date,
                                )

                                if success:
                                    success_count += 1
                                else:
                                    error_count += 1
                                    error_details.append(
                                        f"Dòng {index + 2}: "
                                        f"{get_api_error(result)}"
                                    )

                            except Exception as error:
                                error_count += 1
                                error_details.append(
                                    f"Dòng {index + 2}: {error}"
                                )

                        total_count = len(imported_df)

                        if success_count and not error_count:
                            queue_notification(
                                "success",
                                (
                                    f"Nhập CSV thành công: "
                                    f"{success_count}/{total_count} dòng."
                                ),
                            )
                            st.rerun()

                        if success_count:
                            show_notification(
                                "success",
                                (
                                    f"Đã nhập thành công {success_count}/"
                                    f"{total_count} dòng."
                                ),
                            )

                        if error_count:
                            notification_kind = (
                                "error"
                                if not success_count
                                else "warning"
                            )
                            show_notification(
                                notification_kind,
                                (
                                    f"Nhập thất bại {error_count}/"
                                    f"{total_count} dòng."
                                ),
                            )
                            with st.expander(
                                "Xem chi tiết các dòng bị lỗi"
                            ):
                                for detail in error_details[:30]:
                                    st.write(f"- {detail}")

            except UnicodeDecodeError:
                st.error(
                    "Không đọc được bảng mã CSV. "
                    "Hãy lưu file với mã hóa UTF-8."
                )
            except Exception as error:
                st.error(f"Không thể đọc file CSV: {error}")
