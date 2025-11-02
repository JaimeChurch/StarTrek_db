"""
Update actor records with birth date and nationality from STAPI
"""

import sqlite3
import requests
import time

BASE_URL = "http://stapi.co/api/v1/rest"

def fetch_performers(page_number=0, page_size=100):
    """Fetch performers from STAPI"""
    url = f"{BASE_URL}/performer/search"
    params = {
        'pageNumber': page_number,
        'pageSize': page_size
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('performers', []), data.get('page', {})
    except Exception as e:
        print(f"Error fetching page {page_number}: {e}")
        return [], {}

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("UPDATING ACTOR DATA FROM STAPI")
print("="*70)

updated_count = 0
not_found_count = 0
page = 0
total_processed = 0

while True:
    print(f"\nFetching page {page}...")
    performers, page_info = fetch_performers(page)
    
    if not performers:
        break
    
    print(f"  Processing {len(performers)} performers...")
    
    for performer in performers:
        name = performer.get('name', '')
        if not name:
            continue
        
        # Split name
        name_parts = name.split(maxsplit=1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Get STAPI data
        date_of_birth = performer.get('dateOfBirth')
        place_of_birth = performer.get('placeOfBirth')
        
        # Find actor in database
        cursor.execute("""
            SELECT actor_id FROM Actors
            WHERE first_name = ? AND last_name = ?
        """, (first_name, last_name))
        
        result = cursor.fetchone()
        
        if result:
            actor_id = result[0]
            
            # Update with STAPI data
            cursor.execute("""
                UPDATE Actors
                SET birth_date = ?, nationality = ?
                WHERE actor_id = ?
            """, (date_of_birth, place_of_birth, actor_id))
            
            if date_of_birth or place_of_birth:
                updated_count += 1
        else:
            not_found_count += 1
        
        total_processed += 1
    
    # Check if there are more pages
    total_pages = page_info.get('totalPages', 0)
    if page >= total_pages - 1:
        break
    
    page += 1
    time.sleep(0.5)  # Be nice to the API

conn.commit()
conn.close()

print("\n" + "="*70)
print(f"Processed {total_processed} performers from STAPI")
print(f"✓ Updated {updated_count} actors with birth date/place")
print(f"⚠ {not_found_count} performers not found in database")
print("="*70)

# Show sample
conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()
cursor.execute("""
    SELECT first_name, last_name, birth_date, nationality 
    FROM Actors 
    WHERE birth_date IS NOT NULL OR nationality IS NOT NULL
    LIMIT 10
""")
print("\nSample updated actors:")
for first, last, birth, nation in cursor.fetchall():
    print(f"  {first} {last}: {birth or 'N/A'}, {nation or 'N/A'}")
conn.close()
