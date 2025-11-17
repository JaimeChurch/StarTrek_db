"""
Add imdb_id column to Episodes table
"""
import sqlite3

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE Episodes ADD COLUMN imdb_id VARCHAR(20)")
    print("✓ Added 'imdb_id' column to Episodes table")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e).lower():
        print("'imdb_id' column already exists")
    else:
        print(f"Error: {e}")

conn.commit()
conn.close()
