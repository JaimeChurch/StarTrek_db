"""
Fetch ALL characters from STAPI with full details and update database
Uses pagination to get every character, then fetches full details for each
"""

import sqlite3
import requests
import time

BASE_URL = "http://stapi.co/api/v1/rest"

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("UPDATING CHARACTERS WITH FULL STAPI DATA")
print("="*70)

# Get species mapping
cursor.execute("SELECT species_id, name FROM Species")
species_map = {name.lower(): sid for sid, name in cursor.fetchall()}

updated_count = 0
page = 0
total_chars = 0

while True:
    # Fetch character search page
    search_url = f"{BASE_URL}/character/search"
    params = {'pageNumber': page, 'pageSize': 50}
    
    print(f"\nFetching page {page}...")
    
    try:
        r = requests.get(search_url, params=params, timeout=30)
        data = r.json()
        characters = data.get('characters', [])
        page_info = data.get('page', {})
        
        if not characters:
            break
        
        print(f"  Processing {len(characters)} characters...")
        
        for char in characters:
            uid = char.get('uid')
            name = char.get('name')
            
            if not uid or not name:
                continue
            
            # Fetch full character details
            detail_url = f"{BASE_URL}/character?uid={uid}"
            try:
                r2 = requests.get(detail_url, timeout=30)
                detail = r2.json().get('character', {})
                
                # Find character in database by name
                cursor.execute("SELECT character_id FROM Characters WHERE name = ?", (name,))
                result = cursor.fetchone()
                
                if not result:
                    continue
                
                character_id = result[0]
                
                # Extract data from STAPI
                gender = detail.get('gender')
                birth_year = detail.get('yearOfBirth')
                death_year = detail.get('yearOfDeath')
                
                # Get species (it's an array)
                species_id = None
                char_species = detail.get('characterSpecies', [])
                if char_species:
                    species_name = char_species[0].get('name', '').lower()
                    species_id = species_map.get(species_name)
                
                # Get occupation (it's an array)
                occupation = None
                occupations = detail.get('occupations', [])
                if occupations:
                    occupation = occupations[0].get('name')
                
                # Update database
                cursor.execute("""
                    UPDATE Characters
                    SET gender = COALESCE(?, gender),
                        species_id = COALESCE(?, species_id),
                        birth_year = COALESCE(?, birth_year),
                        death_year = COALESCE(?, death_year),
                        occupation = COALESCE(?, occupation)
                    WHERE character_id = ?
                """, (gender, species_id, birth_year, death_year, occupation, character_id))
                
                if gender or species_id or birth_year or death_year or occupation:
                    updated_count += 1
                
                total_chars += 1
                
                time.sleep(0.1)  # Rate limit
                
            except Exception as e:
                print(f"    Error fetching details for {name}: {e}")
        
        # Check if there are more pages
        total_pages = page_info.get('totalPages', 0)
        if page >= total_pages - 1:
            break
        
        page += 1
        time.sleep(0.5)
        
    except Exception as e:
        print(f"  Error fetching page {page}: {e}")
        break

conn.commit()

print("\n" + "="*70)
print(f"Processed {total_chars} characters")
print(f"✓ Updated {updated_count} with additional data")
print("="*70)

# Show statistics
cursor.execute('SELECT COUNT(*) FROM Characters WHERE species_id IS NOT NULL')
species_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM Characters WHERE occupation IS NOT NULL')
occupation_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM Characters WHERE gender IS NOT NULL')
gender_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM Characters')
total = cursor.fetchone()[0]

print(f"\nFinal statistics:")
print(f"  Species: {species_count}/{total} ({species_count*100/total:.1f}%)")
print(f"  Gender: {gender_count}/{total} ({gender_count*100/total:.1f}%)")
print(f"  Occupation: {occupation_count}/{total} ({occupation_count*100/total:.1f}%)")

conn.close()
