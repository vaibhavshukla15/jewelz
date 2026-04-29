import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

columns = [col[1] for col in c.execute("PRAGMA table_info(products)")]

if "deleted" not in columns:
    c.execute("ALTER TABLE products ADD COLUMN deleted INTEGER DEFAULT 0")

conn.commit()
conn.close()

print("Done")