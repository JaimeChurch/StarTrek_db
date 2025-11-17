"""
Remove the word 'Writers' from the writer column
"""
import sqlite3

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

# Remove 'Writers, ' prefix and keep the actual names
cursor.execute("""
    UPDATE Episodes 
    SET writer = SUBSTR(writer, 10)
    WHERE writer LIKE 'Writers, %'
""")

prefix_count = cursor.rowcount
conn.commit()

print(f"✓ Removed 'Writers, ' prefix from {prefix_count} episodes")

# Set writer to NULL where it equals just 'Writers'
cursor.execute("""
    UPDATE Episodes 
    SET writer = NULL 
    WHERE writer = 'Writers'
""")

exact_count = cursor.rowcount
conn.commit()
conn.close()

print(f"✓ Removed 'Writers' from {exact_count} episodes")
print(f"Total fixed: {prefix_count + exact_count}")
