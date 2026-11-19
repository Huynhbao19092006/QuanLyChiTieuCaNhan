"""Pure financial statistics used by pages and future API endpoints."""


def summarize_transactions(transactions):
    income = sum(
        item.amount for item in transactions if item.transaction_type == "income"
    )
    expense = sum(
        item.amount for item in transactions if item.transaction_type == "expense"
    )
    return {
        "income": income,
        "expense": expense,
        "balance": income - expense,
    }
