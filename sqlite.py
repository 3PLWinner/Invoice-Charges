import sqlite3
import pandas as pd

conn = sqlite3.connect('warehouse_system.db')

# Show first 10 work orders
df = pd.read_sql_query("SELECT * FROM work_orders LIMIT 30", conn)
print(df)

# Show pending orders
pending = pd.read_sql_query("SELECT id, system_id, customer_name FROM work_orders WHERE veracore_synced = 0", conn)
print(pending)

# Check if 'system_id' column exists
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(work_orders)")
columns = [col[1] for col in cursor.fetchall()]
print("Columns in work_orders:", columns)

conn.close()
