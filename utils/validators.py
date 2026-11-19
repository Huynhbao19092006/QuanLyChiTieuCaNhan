from decimal import Decimal, InvalidOperation


def normalize_transaction_type(value):
    """Chuẩn hóa loại giao dịch/danh mục về income hoặc expense."""
    normalized = str(value).strip().casefold()
    aliases = {
        "income": "income",
        "thu nhập": "income",
        "thu nhap": "income",
        "expense": "expense",
        "chi tiêu": "expense",
        "chi tieu": "expense",
    }
    return aliases.get(normalized)

def parse_amount(value):
    """Kiểm tra số tiền hợp lệ."""
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValueError("Số tiền không hợp lệ.")

    if not amount.is_finite():
        raise ValueError("Số tiền không hợp lệ.")

    if amount <= 0:
        raise ValueError("Số tiền phải lớn hơn 0.")

    return amount
