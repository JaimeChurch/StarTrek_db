"""
Remove founded_year, affiliation, and description columns from Organizations table
"""
import sqlite3

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("REMOVING COLUMNS FROM ORGANIZATIONS TABLE")
print("="*70)

# Check current row count
cursor.execute("SELECT COUNT(*) FROM Organizations")
total_rows = cursor.fetchone()[0]
print(f"\nCurrent rows: {total_rows}")

print("\n1. Creating new table structure...")
cursor.execute("""
    CREATE TABLE Organizations_new (
        organization_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL UNIQUE,
        type VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

print("2. Copying data from old table...")
cursor.execute("""
    INSERT INTO Organizations_new 
    (organization_id, name, type, created_at, updated_at)
    SELECT organization_id, name, type, created_at, updated_at
    FROM Organizations
""")

copied_rows = cursor.rowcount
print(f"   Copied {copied_rows} rows")

print("3. Dropping old table...")
cursor.execute("DROP TABLE Organizations")

print("4. Renaming new table...")
cursor.execute("ALTER TABLE Organizations_new RENAME TO Organizations")

# Verify
cursor.execute("SELECT COUNT(*) FROM Organizations")
final_count = cursor.fetchone()[0]

print(f"\n✓ Migration complete!")
print(f"  Final row count: {final_count}")

# Show sample
print("\nSample rows:")
cursor.execute("""
    SELECT organization_id, name, type
    FROM Organizations
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}, type={row[2] or 'NULL'}")

conn.commit()
conn.close()

print("\n" + "="*70)
print("Removed columns: founded_year, affiliation, description")
print("Remember to update schema.sql to match the new structure!")
print("="*70)
