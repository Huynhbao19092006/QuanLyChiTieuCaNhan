"""Thống kê và phân tích."""

import altair as alt
import pandas as pd
import streamlit as st

from ui.helpers import (
    format_money,
    load_data,
    show_page_title,
    transaction_dataframe,
)


def show_statistics():
    show_page_title(
        "Thống kê và phân tích",
        "Phân tích thu nhập, chi tiêu theo thời gian và danh mục.",
    )

    transactions, categories = load_data()

    if not transactions:
        st.info("Chưa có dữ liệu để thống kê.")
        return

    df = transaction_dataframe(transactions, categories)
    df["Ngày"] = pd.to_datetime(df["Ngày"], errors="coerce")
    df = df.dropna(subset=["Ngày"])

    if df.empty:
        st.warning("Không có dữ liệu ngày hợp lệ để thống kê.")
        return

    # -----------------------------------------------------
    # Bộ lọc thời gian
    # -----------------------------------------------------

    st.subheader("Khoảng thời gian thống kê")
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Từ ngày",
            value=df["Ngày"].min().date(),
            key="statistics_start_date",
        )

    with col2:
        end_date = st.date_input(
            "Đến ngày",
            value=df["Ngày"].max().date(),
            key="statistics_end_date",
        )

    if start_date > end_date:
        st.error("Ngày bắt đầu không được lớn hơn ngày kết thúc.")
        return

    filtered_df = df[
        (df["Ngày"].dt.date >= start_date)
        & (df["Ngày"].dt.date <= end_date)
    ].copy()

    if filtered_df.empty:
        st.warning(
            "Không có giao dịch trong khoảng thời gian này. "
            "Hãy chọn khoảng thời gian khác."
        )
        return

    # -----------------------------------------------------
    # Các chỉ số tổng quan
    # -----------------------------------------------------

    income = filtered_df.loc[
        filtered_df["Loại"] == "Thu nhập",
        "Số tiền",
    ].sum()

    expense = filtered_df.loc[
        filtered_df["Loại"] == "Chi tiêu",
        "Số tiền",
    ].sum()

    balance = income - expense

    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng thu nhập", format_money(income))
    col2.metric("Tổng chi tiêu", format_money(expense))
    col3.metric("Chênh lệch thu - chi", format_money(balance))

    st.divider()

    # -----------------------------------------------------
    # BIỂU ĐỒ 1: THU NHẬP VÀ CHI TIÊU THEO THÁNG
    # -----------------------------------------------------

    st.subheader("Thu nhập và chi tiêu theo tháng")
    st.caption(
        "So sánh tổng thu nhập và chi tiêu trong từng tháng "
        "thuộc khoảng thời gian đã chọn."
    )

    # Tạo đầy đủ các tháng trong phạm vi lọc.
    # Tháng không có giao dịch sẽ được điền giá trị 0.
    start_period = pd.Period(start_date, freq="M")
    end_period = pd.Period(end_date, freq="M")
    all_months = pd.period_range(
        start=start_period,
        end=end_period,
        freq="M",
    )

    filtered_df["Tháng"] = filtered_df["Ngày"].dt.to_period("M")

    monthly = filtered_df.pivot_table(
        index="Tháng",
        columns="Loại",
        values="Số tiền",
        aggfunc="sum",
        fill_value=0,
    )

    monthly = monthly.reindex(
        columns=["Thu nhập", "Chi tiêu"],
        fill_value=0,
    )
    monthly = monthly.reindex(all_months, fill_value=0)

    month_labels = [
        f"Tháng {period.month:02d}/{period.year}"
        for period in all_months
    ]

    monthly.index = month_labels
    monthly.index.name = "Tháng"

    chart_df = (
        monthly
        .reset_index()
        .melt(
            id_vars="Tháng",
            var_name="Loại",
            value_name="Số tiền",
        )
    )

    monthly_chart = (
        alt.Chart(chart_df)
        .mark_bar(
            size=25,
            cornerRadiusTopLeft=4,
            cornerRadiusTopRight=4,
        )
        .encode(
            x=alt.X(
                "Tháng:N",
                sort=month_labels,
                title="Thời gian",
                axis=alt.Axis(
                    labelAngle=-35,
                    labelLimit=140,
                ),
            ),
            xOffset=alt.XOffset("Loại:N"),
            y=alt.Y(
                "Số tiền:Q",
                title="Số tiền (VNĐ)",
                scale=alt.Scale(zero=True),
                axis=alt.Axis(format=",.0f"),
            ),
            color=alt.Color(
                "Loại:N",
                title="Loại giao dịch",
                scale=alt.Scale(
                    domain=["Thu nhập", "Chi tiêu"],
                    range=["#15966b", "#df6868"],
                ),
            ),
            tooltip=[
                alt.Tooltip("Tháng:N", title="Tháng"),
                alt.Tooltip("Loại:N", title="Loại giao dịch"),
                alt.Tooltip(
                    "Số tiền:Q",
                    title="Số tiền",
                    format=",.0f",
                ),
            ],
        )
        .properties(height=380)
        .configure_view(strokeOpacity=0)
        .configure_axis(
            gridColor="#e8edf3",
            domain=False,
            tickColor="#d9e1ec",
        )
        .configure_legend(
            orient="top",
            title=None,
        )
    )

    st.altair_chart(
        monthly_chart,
        use_container_width=True,
    )

    with st.expander("Xem số liệu thu chi từng tháng"):
        display_monthly = monthly.copy()
        display_monthly["Chênh lệch"] = (
            display_monthly["Thu nhập"]
            - display_monthly["Chi tiêu"]
        )
        display_monthly = display_monthly.reset_index()
        display_monthly = display_monthly.rename(
            columns={
                "Thu nhập": "Tổng thu nhập (VNĐ)",
                "Chi tiêu": "Tổng chi tiêu (VNĐ)",
                "Chênh lệch": "Chênh lệch (VNĐ)",
            }
        )
        st.dataframe(
            display_monthly,
            width="stretch",
            hide_index=True,
        )

    st.divider()

    # -----------------------------------------------------
    # BIỂU ĐỒ 2: CHI TIÊU THEO DANH MỤC
    # -----------------------------------------------------

    st.subheader("Chi tiêu theo danh mục")

    expense_df = filtered_df[
        filtered_df["Loại"] == "Chi tiêu"
    ]

    if not expense_df.empty:
        category_stats = (
            expense_df
            .groupby("Danh mục")["Số tiền"]
            .sum()
            .sort_values(ascending=False)
        )

        category_chart_df = (
            category_stats
            .rename_axis("Danh mục")
            .reset_index(name="Số tiền")
        )

        category_chart = (
            alt.Chart(category_chart_df)
            .mark_bar(
                color="#087f8c",
                cornerRadiusEnd=5,
            )
            .encode(
                x=alt.X(
                    "Số tiền:Q",
                    title="Số tiền (VNĐ)",
                    axis=alt.Axis(format=",.0f"),
                ),
                y=alt.Y(
                    "Danh mục:N",
                    sort="-x",
                    title="Danh mục",
                ),
                tooltip=[
                    alt.Tooltip("Danh mục:N"),
                    alt.Tooltip("Số tiền:Q", format=",.0f"),
                ],
            )
            .properties(height=300)
        )

        st.altair_chart(
            category_chart,
            use_container_width=True,
        )
    else:
        st.info(
            "Chưa có khoản chi tiêu nào trong thời gian này."
        )

    st.divider()

    # -----------------------------------------------------
    # NHẬN XÉT TÀI CHÍNH
    # -----------------------------------------------------

    st.subheader("Nhận xét tài chính")

    if income > 0:
        ratio = expense / income * 100

        st.metric(
            "Tỷ lệ chi tiêu trên thu nhập",
            f"{ratio:.1f}%",
        )
        st.progress(min(ratio / 100, 1.0))

        if ratio > 100:
            st.error(
                "Chi tiêu đang vượt quá thu nhập "
                "trong khoảng thời gian đã chọn."
            )
        elif ratio >= 80:
            st.warning(
                "Chi tiêu đang chiếm phần lớn thu nhập. "
                "Bạn nên cân nhắc kiểm soát các khoản chưa cần thiết."
            )
        else:
            st.success(
                "Chi tiêu đang thấp hơn thu nhập. "
                "Bạn có thể cân nhắc dành phần chênh lệch "
                "cho tiết kiệm hoặc các mục tiêu tài chính."
            )
    else:
        st.info(
            "Không có thu nhập trong khoảng thời gian này "
            "nên chưa thể đánh giá tỷ lệ chi tiêu trên thu nhập."
        )
