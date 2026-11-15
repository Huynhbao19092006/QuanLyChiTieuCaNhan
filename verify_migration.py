import sqlite3
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import text
from database import engine

TABLES = ["user", "category", "transaction"]

def normalize(value, column):
    if value is None:
        return None

    if column == "amount":
        return Decimal(str(value)).normalize()

    if column == "transaction_date":
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return date.fromisoformat(str(value)).isoformat()

    if column == "created_at":
        if isinstance(value, str):
            value = datetime.fromisoformat(value)

        if isinstance(value, datetime):
            if value.tzinfo is not None:
                value = value.astimezone(timezone.utc).replace(tzinfo=None)
            return value.isoformat()

    return value


conn = sqlite3.connect("data/expenses.db")
conn.row_factory = sqlite3.Row

print("===== DOI CHIEU SQLITE VA NEON =====")

all_match = True

for table in TABLES:
    query = f'SELECT * FROM "{table}" ORDER BY id'

    sqlite_rows = conn.execute(query).fetchall()

    with engine.connect() as connection:
        neon_rows = connection.execute(text(query)).mappings().all()

    print(f"\nBang: {table}")
    print("SQLite:", len(sqlite_rows), "ban ghi")
    print("Neon:", len(neon_rows), "ban ghi")

    sqlite_data = {row["id"]: dict(row) for row in sqlite_rows}
    neon_data = {row["id"]: dict(row) for row in neon_rows}

    if set(sqlite_data) != set(neon_data):
        print("KHONG KHOP ID")
        all_match = False
        continue

    table_match = True

    for record_id in sqlite_data:
        old = sqlite_data[record_id]
        new = neon_data[record_id]

        for column in old:
            old_value = normalize(old[column], column)
            new_value = normalize(new[column], column)

            if old_value != new_value:
                print(f"ID {record_id}: cot {column} KHONG KHOP")
                table_match = False

    if table_match:
        print("KET QUA: DU LIEU KHOP")
    else:
        all_match = False

conn.close()

print("\n===== KET LUAN =====")

if all_match:
    print("TAT CA DU LIEU SQLITE VA NEON KHOP NHAU")
else:
    print("CO DU LIEU KHONG KHOP, CAN KIEM TRA LAI")
