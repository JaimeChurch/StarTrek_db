"""
Remove start_year, end_year, and role columns from Character_Organizations table
"""
import sqlite3

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("UPDATING CHARACTER_ORGANIZATIONS TABLE SCHEMA")
print("="*70)

# Check current row count
cursor.execute("SELECT COUNT(*) FROM Character_Organizations")
total_rows = cursor.fetchone()[0]
print(f"\nCurrent rows: {total_rows}")

# SQLite doesn't support DROP COLUMN directly, so we need to:
# 1. Create a new table without those columns
# 2. Copy data from old table
# 3. Drop old table
# 4. Rename new table

print("\n1. Creating new table structure...")
cursor.execute("""
    CREATE TABLE Character_Organizations_new (
        char_org_id INTEGER PRIMARY KEY AUTOINCREMENT,
        character_id INTEGER NOT NULL,
        organization_id INTEGER NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (character_id) REFERENCES Characters(character_id),
        FOREIGN KEY (organization_id) REFERENCES Organizations(organization_id)
    )
""")

print("2. Copying data from old table...")
cursor.execute("""
    INSERT INTO Character_Organizations_new 
    (char_org_id, character_id, organization_id, notes, created_at)
    SELECT char_org_id, character_id, organization_id, notes, created_at
    FROM Character_Organizations
""")

copied_rows = cursor.rowcount
print(f"   Copied {copied_rows} rows")

print("3. Dropping old table...")
cursor.execute("DROP TABLE Character_Organizations")

print("4. Renaming new table...")
cursor.execute("ALTER TABLE Character_Organizations_new RENAME TO Character_Organizations")

# Verify
cursor.execute("SELECT COUNT(*) FROM Character_Organizations")
final_count = cursor.fetchone()[0]

print(f"\n✓ Migration complete!")
print(f"  Final row count: {final_count}")

# Show sample
print("\nSample rows:")
cursor.execute("""
    SELECT co.char_org_id, c.name, o.name
    FROM Character_Organizations co
    JOIN Characters c ON co.character_id = c.character_id
    JOIN Organizations o ON co.organization_id = o.organization_id
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"  {row[1]} -> {row[2]}")

conn.commit()
conn.close()

print("\n" + "="*70)
print("Remember to update schema.sql to match the new structure!")
print("="*70)
