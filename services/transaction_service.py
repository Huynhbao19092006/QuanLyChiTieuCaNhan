from utils.validators import normalize_transaction_type


def filter_transactions_by_type(transactions, transaction_type):
    """Lọc giao dịch theo loại chuẩn hóa từ API."""
    if transaction_type not in ("income", "expense"):
        raise ValueError("Loại giao dịch không hợp lệ.")

    return [
        item
        for item in transactions
        if normalize_transaction_type(item.transaction_type)
        == transaction_type
    ]
