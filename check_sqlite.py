
import sqlite3
from pathlib import Path
from sqlalchemy import inspect, text
from database import engine

sqlite_path = Path("data/expenses.db")
backup_path = Path("data/expenses_backup_before_neon.db")

print("=== KIỂM TRA FILE SAO LƯU ===")
print("Có file backup:", backup_path.exists())

print("\n=== SQLITE CŨ ===")
conn = sqlite3.connect(sqlite_path)

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
    if table not in inspector.get_table_names():
        print(f"{table}: CHƯA CÓ BẢNG")
        continue

    with engine.connect() as connection:
        count = connection.execute(
            text(f'SELECT COUNT(*) FROM "{table}"')
        ).scalar_one()

    print(f"{table}: {count} bản ghi")

print("\n=== HOÀN TẤT KIỂM TRA ===")
