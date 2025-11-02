"""
Update character records with more complete data from STAPI
"""

import sqlite3
import requests
import time

BASE_URL = "http://stapi.co/api/v1/rest"

def fetch_characters(page_number=0, page_size=100):
    """Fetch characters from STAPI"""
    url = f"{BASE_URL}/character/search"
    params = {
        'pageNumber': page_number,
        'pageSize': page_size
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('characters', []), data.get('page', {})
    except Exception as e:
        print(f"Error fetching page {page_number}: {e}")
        return [], {}

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("UPDATING CHARACTER DATA FROM STAPI")
print("="*70)

updated_count = 0
page = 0
total_processed = 0

# Get species mapping
cursor.execute("SELECT species_id, name FROM Species")
species_map = {name.lower(): sid for sid, name in cursor.fetchall()}

while True:
    print(f"\nFetching page {page}...")
    characters, page_info = fetch_characters(page)
    
    if not characters:
        break
    
    print(f"  Processing {len(characters)} characters...")
    
    for character in characters:
        name = character.get('name', '')
        if not name:
            continue
        
        # Find character in database
        cursor.execute("SELECT character_id FROM Characters WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        if not result:
            continue
        
        character_id = result[0]
        
        # Get STAPI data
        gender = character.get('gender')
        birth_year = character.get('yearOfBirth')
        death_year = character.get('yearOfDeath')
        
        # Get species
        species_id = None
        char_species = character.get('characterSpecies', [])
        if char_species and len(char_species) > 0:
            species_name = char_species[0].get('name', '').lower()
            species_id = species_map.get(species_name)
        
        # Get title/occupation (STAPI doesn't have rank or occupation as separate fields)
        # These would need to come from other sources
        
        # Update character
        cursor.execute("""
            UPDATE Characters
            SET gender = COALESCE(?, gender),
                species_id = COALESCE(?, species_id),
                birth_year = COALESCE(?, birth_year),
                death_year = COALESCE(?, death_year)
            WHERE character_id = ?
        """, (gender, species_id, birth_year, death_year, character_id))
        
        if gender or species_id or birth_year or death_year:
            updated_count += 1
        
        total_processed += 1
    
    # Check if there are more pages
    total_pages = page_info.get('totalPages', 0)
    if page >= total_pages - 1:
        break
    
    page += 1
    time.sleep(0.5)  # Be nice to the API

conn.commit()

print("\n" + "="*70)
print(f"Processed {total_processed} characters from STAPI")
print(f"✓ Updated {updated_count} characters with additional data")
print("="*70)

# Show statistics
cursor.execute('SELECT COUNT(*) FROM Characters WHERE species_id IS NOT NULL')
species_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM Characters WHERE gender IS NOT NULL')
gender_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM Characters WHERE birth_year IS NOT NULL')
birth_count = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM Characters')
total = cursor.fetchone()[0]

print(f"\nUpdated statistics:")
print(f"  Characters with species: {species_count}/{total} ({species_count*100/total:.1f}%)")
print(f"  Characters with gender: {gender_count}/{total} ({gender_count*100/total:.1f}%)")
print(f"  Characters with birth year: {birth_count}/{total} ({birth_count*100/total:.1f}%)")

conn.close()
