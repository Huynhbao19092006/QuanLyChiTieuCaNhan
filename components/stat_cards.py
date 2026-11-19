"""Financial summary cards."""

import streamlit as st


def render(total_income, total_expense, balance, format_money):
    columns = st.columns(3)
    cards = (
        ("💰", "TỔNG THU NHẬP", total_income, "metric-value--income"),
        ("💸", "TỔNG CHI TIÊU", total_expense, "metric-value--expense"),
        (
            "📊",
            "SỐ DƯ HIỆN TẠI",
            balance,
            "metric-value--balance" if balance >= 0 else "metric-value--negative",
        ),
    )
    for column, (icon, label, amount, modifier) in zip(columns, cards):
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-label">{label}</div>
                    <div class="metric-value {modifier}">
                        {format_money(amount)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
