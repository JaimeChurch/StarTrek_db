"""
Remove bio column from Characters table and populate rank/title from STAPI
"""
import sqlite3
import requests
import time

BASE_URL = "http://stapi.co/api/v1/rest"

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("STEP 1: REMOVING BIO COLUMN FROM CHARACTERS TABLE")
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

conn.commit()

print(f"\n✓ Bio column removed!")

print("\n" + "="*70)
print("STEP 2: POPULATING RANK AND TITLE FROM STAPI")
print("="*70)

# Build character UID cache
print("\n1. Building character UID cache...")
uid_cache = {}
page = 0
max_pages = 100

while page < max_pages:
    search_url = f"{BASE_URL}/character/search"
    params = {'pageNumber': page, 'pageSize': 100}
    
    try:
        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        characters = data.get('characters', [])
        if not characters:
            break
        
        for char in characters:
            char_name = char.get('name')
            char_uid = char.get('uid')
            if char_name and char_uid:
                uid_cache[char_name] = char_uid
        
        print(f"   Page {page}: cached {len(characters)} UIDs (total: {len(uid_cache)})")
        
        page_info = data.get('page', {})
        if page_info.get('lastPage', True):
            break
        
        page += 1
        time.sleep(0.3)
        
    except Exception as e:
        print(f"   Error fetching page {page}: {e}")
        break

print(f"\n   Total UIDs cached: {len(uid_cache)}")

# Now populate rank and title
print("\n2. Populating rank and title fields...")

cursor.execute("SELECT character_id, name FROM Characters")
all_characters = cursor.fetchall()

updated_count = 0
skipped_count = 0

for char_id, char_name in all_characters:
    char_uid = uid_cache.get(char_name)
    
    if not char_uid:
        skipped_count += 1
        continue
    
    # Get full character details
    try:
        detail_url = f"{BASE_URL}/character"
        response = requests.get(detail_url, params={'uid': char_uid}, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'character' in data:
            char_details = data['character']
            
            # Get titles field
            titles = char_details.get('titles', [])
            
            rank = None
            title = None
            
            if titles:
                # Separate military ranks from positions/titles
                for title_obj in titles:
                    title_name = title_obj.get('name')
                    is_military_rank = title_obj.get('militaryRank', False) or title_obj.get('fleetRank', False)
                    is_position = title_obj.get('position', False)
                    
                    if is_military_rank and not rank:
                        rank = title_name
                    elif is_position and not title:
                        title = title_name
                    elif not rank and not title:
                        # If unclear, put in title
                        title = title_name
            
            # Update character
            if rank or title:
                cursor.execute("""
                    UPDATE Characters
                    SET rank = ?, title = ?
                    WHERE character_id = ?
                """, (rank, title, char_id))
                
                if rank or title:
                    updated_count += 1
                    if updated_count % 50 == 0:
                        print(f"   Updated {updated_count} characters...")
                        conn.commit()
        
        time.sleep(0.5)  # Rate limiting
        
    except Exception as e:
        skipped_count += 1
        continue

conn.commit()

print("\n" + "="*70)
print(f"Updated {updated_count} characters with rank/title")
print(f"Skipped {skipped_count} (no UID or no titles)")
print("="*70)

# Show statistics
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN rank IS NOT NULL AND rank != '' THEN 1 ELSE 0 END) as with_rank,
        SUM(CASE WHEN title IS NOT NULL AND title != '' THEN 1 ELSE 0 END) as with_title
    FROM Characters
""")

result = cursor.fetchone()
print(f"\nFinal statistics:")
print(f"  Total characters: {result[0]}")
print(f"  With rank: {result[1]} ({result[1]*100/result[0]:.1f}%)")
print(f"  With title: {result[2]} ({result[2]*100/result[0]:.1f}%)")

# Show sample
cursor.execute("""
    SELECT name, rank, title
    FROM Characters
    WHERE rank IS NOT NULL OR title IS NOT NULL
    LIMIT 10
""")

print("\nSample updated records:")
for row in cursor.fetchall():
    print(f"  {row[0]}: rank={row[1] or 'N/A'}, title={row[2] or 'N/A'}")

conn.close()

print("\n" + "="*70)
print("Remember to update schema.sql to match the new structure!")
print("="*70)
