"""
Remove classification and description columns from Species table
"""
import sqlite3

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("REMOVING CLASSIFICATION AND DESCRIPTION FROM SPECIES TABLE")
print("="*70)

# Check current state
cursor.execute("SELECT COUNT(*) FROM Species")
current_count = cursor.fetchone()[0]
print(f"\nCurrent rows in Species: {current_count}")

# Create new table without classification and description
print("\nCreating new Species table without classification and description...")
cursor.execute("""
    CREATE TABLE Species_new (
        species_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        homeworld TEXT,
        warp_capable INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Copy data
print("Copying data to new table...")
cursor.execute("""
    INSERT INTO Species_new (species_id, name, homeworld, warp_capable, created_at, updated_at)
    SELECT species_id, name, homeworld, warp_capable, created_at, updated_at
    FROM Species
""")

copied_count = cursor.rowcount
print(f"Copied {copied_count} rows")

# Drop old table and rename new one
print("Replacing old table with new table...")
cursor.execute("DROP TABLE Species")
cursor.execute("ALTER TABLE Species_new RENAME TO Species")

conn.commit()

# Verify
cursor.execute("SELECT COUNT(*) FROM Species")
final_count = cursor.fetchone()[0]
print(f"\nFinal row count: {final_count}")

# Show sample
print("\nSample records:")
cursor.execute("SELECT * FROM Species LIMIT 5")
for row in cursor.fetchall():
    print(f"  {row[0]}, {row[1]}, homeworld={row[2] or 'NULL'}, warp={row[3]}")

print("\n" + "="*70)
print("COMPLETE - Removed classification and description columns")
print("="*70)

conn.close()
