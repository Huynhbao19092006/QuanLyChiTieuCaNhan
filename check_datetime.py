import sqlite3
from sqlalchemy import text
from database import engine

conn = sqlite3.connect("data/expenses.db")
conn.row_factory = sqlite3.Row

checks = [
    ("user", "created_at"),
    ("category", "created_at"),
    ("transaction", "transaction_date"),
    ("transaction", "created_at"),
]

for table, column in checks:
    print(f"\n=== {table}.{column} ===")

    old = conn.execute(
        f'SELECT id, "{column}" FROM "{table}" ORDER BY id LIMIT 1'
    ).fetchone()

    with engine.connect() as db:
        new = db.execute(
            text(f'SELECT id, "{column}" FROM "{table}" ORDER BY id LIMIT 1')
        ).mappings().first()

    print("SQLite:", repr(old[column]), type(old[column]).__name__)
    print("Neon:  ", repr(new[column]), type(new[column]).__name__)

conn.close()
