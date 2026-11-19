import altair as alt
import pandas as pd

from services.category_service import category_name
from components.transaction_table import transaction_dataframe
from utils.formatters import parse_api_date


def build_monthly_cashflow_chart(transactions, categories):
    """Tạo biểu đồ cột nhóm thu nhập và chi tiêu theo tháng."""
    df = transaction_dataframe(transactions, categories)
    df["Ngày"] = pd.to_datetime(df["Ngày"], errors="coerce")
    df = df.dropna(subset=["Ngày"])

    if df.empty:
        return None

    df["Tháng"] = df["Ngày"].dt.to_period("M").astype(str)
    monthly = (
        df.groupby(["Tháng", "Loại"], as_index=False)["Số tiền"]
        .sum()
    )
    month_order = sorted(monthly["Tháng"].unique().tolist())

    return (
        alt.Chart(monthly)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(
                "Tháng:N",
                sort=month_order,
                title="Tháng",
            ),
            xOffset=alt.XOffset(
                "Loại:N",
                sort=["Thu nhập", "Chi tiêu"],
            ),
            y=alt.Y(
                "Số tiền:Q",
                title="Số tiền (VNĐ)",
                axis=alt.Axis(format=",.0f"),
            ),
            color=alt.Color(
                "Loại:N",
                title="Loại giao dịch",
                scale=alt.Scale(
                    domain=["Thu nhập", "Chi tiêu"],
                    range=["#0f9d8a", "#e76f51"],
                ),
            ),
            tooltip=[
                alt.Tooltip("Tháng:N", title="Tháng"),
                alt.Tooltip("Loại:N", title="Loại"),
                alt.Tooltip(
                    "Số tiền:Q",
                    title="Số tiền",
                    format=",.0f",
                ),
            ],
        )
        .properties(
            height=330,
            title="Thu nhập và chi tiêu theo tháng",
        )
        .configure_view(stroke=None)
    )
