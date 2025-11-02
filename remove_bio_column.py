"""
Remove bio column from Characters table
"""
import sqlite3

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("REMOVING BIO COLUMN FROM CHARACTERS TABLE")
print("="*70)

# Check current row count
cursor.execute("SELECT COUNT(*) FROM Characters")
total_rows = cursor.fetchone()[0]
print(f"\nCurrent rows: {total_rows}")

print("\n1. Creating new table structure without bio column...")
cursor.execute("""
    CREATE TABLE Characters_new (
        character_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        rank VARCHAR(50),
        title VARCHAR(100),
        species_id INTEGER,
        birth_year INTEGER,
        death_year INTEGER,
        gender VARCHAR(20),
        occupation VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (species_id) REFERENCES Species(species_id)
    )
""")

print("2. Copying data from old table...")
cursor.execute("""
    INSERT INTO Characters_new 
    (character_id, name, rank, title, species_id, birth_year, death_year, 
     gender, occupation, created_at, updated_at)
    SELECT character_id, name, rank, title, species_id, birth_year, death_year,
           gender, occupation, created_at, updated_at
    FROM Characters
""")

copied_rows = cursor.rowcount
print(f"   Copied {copied_rows} rows")

print("3. Dropping old table...")
cursor.execute("DROP TABLE Characters")

print("4. Renaming new table...")
cursor.execute("ALTER TABLE Characters_new RENAME TO Characters")

# Verify
cursor.execute("SELECT COUNT(*) FROM Characters")
final_count = cursor.fetchone()[0]

print(f"\n✓ Migration complete!")
print(f"  Final row count: {final_count}")

# Show sample
print("\nSample rows:")
cursor.execute("""
    SELECT character_id, name, rank, title
    FROM Characters
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}, rank={row[2] or 'NULL'}, title={row[3] or 'NULL'}")

conn.commit()
conn.close()

print("\n" + "="*70)
print("Remember to update schema.sql to match the new structure!")
print("="*70)
