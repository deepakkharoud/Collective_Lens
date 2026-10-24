import sqlite3
from pathlib import Path

db_path = Path("samples/collective_lens_capture.sqlite")

if not db_path.exists():
    raise FileNotFoundError(
        f"Database not found: {db_path.resolve()}"
    )

connection = sqlite3.connect(str(db_path))

tables = [
    row[0]
    for row in connection.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' ORDER BY name"
    )
]

print("Database tables:")
for table in tables:
    print(" -", table)

print("\nTables containing 'KERNEL':")
for table in tables:
    if "KERNEL" in table.upper():
        print(" -", table)

connection.close()
