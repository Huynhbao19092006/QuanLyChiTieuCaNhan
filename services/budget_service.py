"""Budget domain service boundary.

This module is deliberately small until the backend exposes budget tables and
endpoints. Keeping the boundary now prevents UI code from coupling to storage.
"""


def validate_budget_amount(amount):
    if amount is None or amount <= 0:
        return False, "Ngân sách phải lớn hơn 0."
    return True, ""
