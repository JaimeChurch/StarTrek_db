"""
Rename nationality column to birth_place in Actors table
"""

import sqlite3

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("RENAMING nationality TO birth_place IN Actors TABLE")
print("="*70)

# SQLite doesn't support RENAME COLUMN directly in older versions
# Need to recreate the table

# Step 1: Create new table with correct column name
cursor.execute("""
    CREATE TABLE Actors_new (
        actor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        birth_date DATE,
        birth_place VARCHAR(100),
        bio TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Step 2: Copy data
cursor.execute("""
    INSERT INTO Actors_new (actor_id, first_name, last_name, birth_date, birth_place, bio, created_at, updated_at)
    SELECT actor_id, first_name, last_name, birth_date, nationality, bio, created_at, updated_at
    FROM Actors
""")

# Step 3: Drop old table
cursor.execute("DROP TABLE Actors")

# Step 4: Rename new table
cursor.execute("ALTER TABLE Actors_new RENAME TO Actors")

# Step 5: Recreate indexes
cursor.execute("CREATE INDEX idx_actors_name ON Actors(first_name, last_name)")

conn.commit()
conn.close()

print("✓ Successfully renamed nationality to birth_place")
print("="*70)
