import sqlite3

conn = sqlite3.connect('bi_chatbot.db')
cursor = conn.cursor()

# Check if translation_dictionary table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='translation_dictionary';")
result = cursor.fetchone()

if result:
    print("translation_dictionary table exists")
    cursor.execute("SELECT * FROM translation_dictionary LIMIT 5;")
    rows = cursor.fetchall()
    print("Sample data:", rows)
else:
    print("translation_dictionary table does not exist")

# Check the structure of existing CSV data tables
print("\nExisting data tables:")
for table_name in ['ClientsBot2025', 'ItemsBot2025', 'OrdersBot2025', 'SalesBot2025']:
    print(f"\n{table_name}:")
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row}")

conn.close()