from utils.page_context import *


def show_dashboard():
    transactions, categories = load_data()

    show_page_title(
        "Tổng quan tài chính",
        "Theo dõi tình hình thu nhập và chi tiêu của bạn.",
    )

    username = get_user_value("username") or "Bạn"
    safe_username = html.escape(str(username))

    st.markdown(
        f"""
        <div class="dashboard-banner">
            <h2>Xin chào, {safe_username} 👋</h2>
            <p>
                Đây là tổng quan tình hình tài chính cá nhân của bạn.
                Hãy theo dõi thu nhập và chi tiêu thường xuyên nhé!
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_income = sum(
        float(item.amount)
        for item in transactions
        if item.transaction_type == "income"
    )
    total_expense = sum(
        float(item.amount)
        for item in transactions
        if item.transaction_type == "expense"
    )
    balance = total_income - total_expense

    from components.stat_cards import render as render_stat_cards

    render_stat_cards(total_income, total_expense, balance, format_money)

    st.write("")
    left, right = st.columns([1.5, 1])

    with left:
        st.subheader("Biến động thu và chi")
        st.caption(
            "So sánh tổng thu nhập và chi tiêu theo từng tháng."
        )

        if transactions:
            chart = build_monthly_cashflow_chart(
                transactions,
                categories,
            )

            if chart is not None:
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Không có dữ liệu ngày hợp lệ.")
        else:
            st.info("Chưa có dữ liệu giao dịch để hiển thị.")

    with right:
        st.subheader("Tình hình chi tiêu")

        expense_ratio = (
            total_expense / total_income * 100
            if total_income > 0
            else 0
        )

        st.metric(
            "Tỷ lệ chi tiêu trên thu nhập",
            f"{expense_ratio:.1f}%",
        )
        st.progress(min(max(expense_ratio / 100, 0), 1))

        if total_income == 0 and total_expense == 0:
            st.info("Hãy thêm giao dịch để xem phân tích.")
        elif total_income == 0:
            st.warning("Bạn chưa có thu nhập được ghi nhận.")
        elif expense_ratio > 100:
            st.error("Chi tiêu đang vượt quá tổng thu nhập.")
        elif expense_ratio >= 80:
            st.warning("Bạn nên chú ý kiểm soát chi tiêu.")
        else:
            st.success(
                "Tình hình chi tiêu đang trong mức hợp lý."
            )

    st.subheader("Giao dịch gần đây")

    if transactions:
        recent = sorted(
            transactions,
            key=lambda item: item.transaction_date,
            reverse=True,
        )[:5]
        recent_df = transaction_dataframe(recent, categories)
        st.dataframe(
            recent_df,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("Bạn chưa có giao dịch nào.")
