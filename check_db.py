import sqlite3
import json
conn = sqlite3.connect('portfolio.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', cursor.fetchall())
for table in ['skills', 'projects', 'profile']:
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"\n=== {table} ===")
    print("Columns:", columns)
    print("Rows:", json.dumps(rows, indent=2, default=str))

conn.close()