"""
Remove organization_id and description columns from Ships table
"""
import sqlite3

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("REMOVING COLUMNS FROM SHIPS TABLE")
print("="*70)

# Check current row count
cursor.execute("SELECT COUNT(*) FROM Ships")
total_rows = cursor.fetchone()[0]
print(f"\nCurrent rows: {total_rows}")

print("\n1. Creating new table structure...")
cursor.execute("""
    CREATE TABLE Ships_new (
        ship_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        registry VARCHAR(50),
        class VARCHAR(50),
        type VARCHAR(50),
        launched_year INTEGER,
        status VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

print("2. Copying data from old table...")
cursor.execute("""
    INSERT INTO Ships_new 
    (ship_id, name, registry, class, type, launched_year, status, created_at, updated_at)
    SELECT ship_id, name, registry, class, type, launched_year, status, created_at, updated_at
    FROM Ships
""")

copied_rows = cursor.rowcount
print(f"   Copied {copied_rows} rows")

print("3. Dropping old table...")
cursor.execute("DROP TABLE Ships")

print("4. Renaming new table...")
cursor.execute("ALTER TABLE Ships_new RENAME TO Ships")

# Verify
cursor.execute("SELECT COUNT(*) FROM Ships")
final_count = cursor.fetchone()[0]

print(f"\n✓ Migration complete!")
print(f"  Final row count: {final_count}")

# Show sample
print("\nSample rows:")
cursor.execute("""
    SELECT ship_id, name, registry, class, type, launched_year, status
    FROM Ships
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}, {row[2] or 'N/A'}, {row[3] or 'N/A'}, type={row[4] or 'NULL'}, year={row[5] or 'NULL'}, {row[6] or 'N/A'}")

conn.commit()
conn.close()

print("\n" + "="*70)
print("Removed columns: organization_id, description")
print("Remember to update schema.sql to match the new structure!")
print("="*70)
