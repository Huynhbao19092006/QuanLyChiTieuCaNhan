import sqlite3
from pathlib import Path
from sqlalchemy import inspect, text
from database import engine

print("=== FILE SAO LƯU ===")
print("Có backup:", Path("data/expenses_backup_before_neon.db").exists())

print("\n=== SQLITE CU ===")
conn = sqlite3.connect("data/expenses.db")

for table in ["user", "category", "transaction"]:
    count = conn.execute(
        f'SELECT COUNT(*) FROM "{table}"'
    ).fetchone()[0]
    print(f"{table}: {count} bản ghi")

conn.close()

print("\n=== NEON POSTGRESQL ===")
print("Database:", engine.dialect.name)

inspector = inspect(engine)

for table in ["user", "category", "transaction"]:
    if table in inspector.get_table_names():
        with engine.connect() as connection:
            count = connection.execute(
                text(f'SELECT COUNT(*) FROM "{table}"')
            ).scalar_one()
        print(f"{table}: {count} bản ghi")
    else:
        print(f"{table}: Chưa có bảng")

print("\n=== HOAN TAT ===")
