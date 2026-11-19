import pandas as pd

from services.category_service import category_name


def transaction_dataframe(transactions, categories):
    """Chuyển giao dịch thành DataFrame."""
    rows = []

    for item in transactions:
        rows.append({
            "Ngày": item.transaction_date,
            "Loại": (
                "Thu nhập"
                if item.transaction_type == "income"
                else "Chi tiêu"
            ),
            "Danh mục": category_name(item.category_id, categories),
            "Số tiền": float(item.amount),
            "Mô tả": item.description or "",
        })

    return pd.DataFrame(
        rows,
        columns=["Ngày", "Loại", "Danh mục", "Số tiền", "Mô tả"],
    )
