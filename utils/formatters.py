from datetime import date, datetime
from decimal import InvalidOperation


def format_money(value):
    """Định dạng tiền Việt Nam."""
    try:
        return f"{float(value):,.0f} đ"
    except (ValueError, TypeError, InvalidOperation):
        return "0 đ"

def parse_api_date(value):
    """Chuyển ngày từ API thành datetime.date."""
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    value = str(value)

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).date()
    except ValueError:
        return date.fromisoformat(value[:10])
