"""
Populate Character_Actors table with series, first_appearance, last_appearance, and episodes_count
Uses STAPI character details to get performer and episode information
"""

import sqlite3
import requests
import time
from collections import defaultdict

BASE_URL = "http://stapi.co/api/v1/rest"

def get_character_details(character_uid):
    """Get full character details from STAPI including performers and episodes"""
    url = f"{BASE_URL}/character"
    params = {'uid': character_uid}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('character', {})
    except Exception as e:
        print(f"    Error fetching details: {e}")
        return {}

def extract_series_from_performer(performer):
    """Extract series abbreviations from performer flags"""
    series_flags = {
        'ds9Performer': 'DS9',
        'disPerformer': 'DIS',
        'entPerformer': 'ENT',
        'filmPerformer': 'FILM',
        'tasPerformer': 'TAS',
        'tngPerformer': 'TNG',
        'tosPerformer': 'TOS',
        'voyPerformer': 'VOY'
    }
    
    series_list = []
    for flag, abbreviation in series_flags.items():
        if performer.get(flag) == True:
            series_list.append(abbreviation)
    
    return series_list

def extract_series_from_episodes(episodes):
    """Extract series abbreviation from episode data"""
    if episodes and len(episodes) > 0:
        series_title = episodes[0].get('series', {}).get('title', '')
        # Map series titles to abbreviations
        series_map = {
            'Star Trek: Deep Space Nine': 'DS9',
            'Star Trek: Discovery': 'DIS',
            'Star Trek: Enterprise': 'ENT',
            'Star Trek: The Next Generation': 'TNG',
            'Star Trek: The Original Series': 'TOS',
            'Star Trek: Voyager': 'VOY',
            'Star Trek: The Animated Series': 'TAS'
        }
        return series_map.get(series_title, '')
    return None

# Connect to database
conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("POPULATING CHARACTER_ACTORS FIELDS FROM STAPI")
print("="*70)

# First, we need to get character UIDs. We'll cache them from STAPI character search
print("\n1. Building character UID cache...")

# Get all characters from database that need updating
cursor.execute("""
    SELECT DISTINCT c.character_id, c.name
    FROM Characters c
    JOIN Character_Actors ca ON c.character_id = ca.character_id
    WHERE ca.series IS NULL OR ca.series = ''
""")
characters_to_update = cursor.fetchall()

print(f"   Found {len(characters_to_update)} characters to update")

# Build UID cache by searching STAPI
uid_cache = {}
print("\n2. Fetching character UIDs from STAPI...")

# We'll search in batches
page = 0
max_pages = 100  # Adjust as needed

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
        
        # Check if last page
        page_info = data.get('page', {})
        if page_info.get('lastPage', True):
            break
        
        page += 1
        time.sleep(0.3)  # Rate limiting
        
    except Exception as e:
        print(f"   Error fetching page {page}: {e}")
        break

print(f"\n   Total UIDs cached: {len(uid_cache)}")

# Now update Character_Actors records
print("\n3. Updating Character_Actors records...")

updated_count = 0
skipped_count = 0
error_count = 0

for char_id, char_name in characters_to_update:
    print(f"\n   Processing: {char_name} (ID: {char_id})")
    
    # Get UID from cache
    char_uid = uid_cache.get(char_name)
    
    if not char_uid:
        print(f"     UID not found in cache, skipping")
        skipped_count += 1
        continue
    
    # Get full character details
    char_details = get_character_details(char_uid)
    
    if not char_details:
        print(f"     Could not fetch details, skipping")
        error_count += 1
        continue
    
    # Get performers and episodes
    performers = char_details.get('performers', [])
    episodes = char_details.get('episodes', [])
    
    if not performers:
        print(f"     No performers found")
        skipped_count += 1
        continue
    
    # Process each performer
    for performer in performers:
        perf_name = performer.get('name', '')
        if not perf_name:
            continue
        
        # Split name
        name_parts = perf_name.split(maxsplit=1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Find actor in database
        cursor.execute("""
            SELECT actor_id FROM Actors
            WHERE first_name = ? AND last_name = ?
        """, (first_name, last_name))
        
        actor_result = cursor.fetchone()
        
        if not actor_result:
            print(f"     Actor not found: {perf_name}")
            continue
        
        actor_id = actor_result[0]
        
        # Determine series
        series_list = extract_series_from_performer(performer)
        
        # If no series from flags, try to get from episodes
        if not series_list and episodes:
            series_from_eps = extract_series_from_episodes(episodes)
            if series_from_eps:
                series_list = [series_from_eps]
        
        # Map series titles to abbreviations for filtering episodes
        series_title_map = {
            'Star Trek: Deep Space Nine': 'DS9',
            'Star Trek: Discovery': 'DIS',
            'Star Trek: Enterprise': 'ENT',
            'Star Trek: The Next Generation': 'TNG',
            'Star Trek: The Original Series': 'TOS',
            'Star Trek: Voyager': 'VOY',
            'Star Trek: The Animated Series': 'TAS'
        }
        
        # Update each series the actor appeared in
        if series_list:
            for series in series_list:
                # Filter episodes for this specific series
                series_episodes = [
                    ep for ep in episodes
                    if series_title_map.get(ep.get('series', {}).get('title', '')) == series
                ]
                
                # Calculate series-specific episode information
                first_appearance = None
                last_appearance = None
                episodes_count = len(series_episodes)
                
                if series_episodes:
                    # Sort episodes by air date
                    sorted_episodes = sorted(
                        series_episodes, 
                        key=lambda e: e.get('usAirDate', '') or ''
                    )
                    
                    if sorted_episodes:
                        first_ep = sorted_episodes[0]
                        last_ep = sorted_episodes[-1]
                        
                        first_appearance = first_ep.get('title')
                        last_appearance = last_ep.get('title')
                
                # Check if a row exists for this character-actor-series combination
                cursor.execute("""
                    SELECT character_actor_id FROM Character_Actors
                    WHERE character_id = ? AND actor_id = ? AND series = ?
                """, (char_id, actor_id, series))
                
                existing_row = cursor.fetchone()
                
                if existing_row:
                    # Update existing row
                    cursor.execute("""
                        UPDATE Character_Actors
                        SET first_appearance = ?,
                            last_appearance = ?,
                            episodes_count = ?
                        WHERE character_id = ? AND actor_id = ? AND series = ?
                    """, (first_appearance, last_appearance, episodes_count,
                          char_id, actor_id, series))
                    
                    if cursor.rowcount > 0:
                        updated_count += 1
                        print(f"     ✓ Updated: {perf_name} in {series} ({episodes_count} episodes)")
                else:
                    # Check if there's a row without series data (first series to be added)
                    cursor.execute("""
                        SELECT character_actor_id FROM Character_Actors
                        WHERE character_id = ? AND actor_id = ? 
                            AND (series IS NULL OR series = '')
                        LIMIT 1
                    """, (char_id, actor_id))
                    
                    blank_row = cursor.fetchone()
                    
                    if blank_row:
                        # Update the blank row with this series data
                        cursor.execute("""
                            UPDATE Character_Actors
                            SET series = ?,
                                first_appearance = ?,
                                last_appearance = ?,
                                episodes_count = ?
                            WHERE character_actor_id = ?
                        """, (series, first_appearance, last_appearance, 
                              episodes_count, blank_row[0]))
                        
                        updated_count += 1
                        print(f"     ✓ Updated blank row: {perf_name} in {series} ({episodes_count} episodes)")
                    else:
                        # Check if there are ANY rows for this character-actor pair
                        cursor.execute("""
                            SELECT COUNT(*) FROM Character_Actors
                            WHERE character_id = ? AND actor_id = ?
                        """, (char_id, actor_id))
                        
                        existing_count = cursor.fetchone()[0]
                        
                        if existing_count > 0:
                            # There are existing rows but none are blank and none match this series
                            # This means we need to insert a new row for this additional series
                            try:
                                cursor.execute("""
                                    INSERT INTO Character_Actors 
                                    (character_id, actor_id, series, first_appearance, last_appearance, episodes_count)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (char_id, actor_id, series, first_appearance, last_appearance, episodes_count))
                                
                                updated_count += 1
                                print(f"     ✓ Inserted additional series: {perf_name} in {series} ({episodes_count} episodes)")
                            except sqlite3.IntegrityError as e:
                                print(f"     ⚠ Could not insert {perf_name} in {series}: {e}")
                        else:
                            # No rows exist at all, something is wrong
                            print(f"     ⚠ No existing rows found for character {char_id} and actor {actor_id}")
        else:
            # No series info, but update episode counts anyway
            first_appearance = None
            last_appearance = None
            episodes_count = len(episodes)
            
            if episodes:
                sorted_episodes = sorted(
                    episodes, 
                    key=lambda e: e.get('usAirDate', '') or ''
                )
                
                if sorted_episodes:
                    first_ep = sorted_episodes[0]
                    last_ep = sorted_episodes[-1]
                    
                    first_appearance = first_ep.get('title')
                    last_appearance = last_ep.get('title')
            
            cursor.execute("""
                UPDATE Character_Actors
                SET first_appearance = ?,
                    last_appearance = ?,
                    episodes_count = ?
                WHERE character_id = ? AND actor_id = ?
                    AND (series IS NULL OR series = '')
            """, (first_appearance, last_appearance, 
                  episodes_count, char_id, actor_id))
            
            if cursor.rowcount > 0:
                updated_count += 1
                print(f"     ✓ Updated: {perf_name} (no series, {episodes_count} episodes)")
    
    # Commit periodically
    if (char_id % 10) == 0:
        conn.commit()
    
    time.sleep(0.5)  # Rate limiting

conn.commit()

print("\n" + "="*70)
print(f"Updated {updated_count} Character_Actors records")
print(f"Skipped {skipped_count} (no UID or no performers)")
print(f"Errors: {error_count}")
print("="*70)

# Show updated statistics
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN series IS NOT NULL AND series != '' THEN 1 ELSE 0 END) as with_series,
        SUM(CASE WHEN first_appearance IS NOT NULL THEN 1 ELSE 0 END) as with_first,
        SUM(CASE WHEN episodes_count IS NOT NULL THEN 1 ELSE 0 END) as with_count
    FROM Character_Actors
""")

result = cursor.fetchone()
print(f"\nUpdated statistics:")
print(f"  Total records: {result[0]}")
print(f"  With series: {result[1]} ({result[1]*100/result[0]:.1f}%)")
print(f"  With first_appearance: {result[2]} ({result[2]*100/result[0]:.1f}%)")
print(f"  With episodes_count: {result[3]} ({result[3]*100/result[0]:.1f}%)")

# Show sample
cursor.execute("""
    SELECT ca.character_actor_id, c.name, a.first_name, a.last_name, 
           ca.series, ca.first_appearance, ca.episodes_count
    FROM Character_Actors ca
    JOIN Characters c ON ca.character_id = c.character_id
    JOIN Actors a ON ca.actor_id = a.actor_id
    WHERE ca.series IS NOT NULL AND ca.series != ''
    LIMIT 10
""")

print("\nSample updated records:")
for row in cursor.fetchall():
    print(f"  {row[1]} played by {row[2]} {row[3]}: {row[4]} - {row[5]} ({row[6]} eps)")

conn.close()

print("\n" + "="*70)
print("COMPLETE - All characters processed")
print("="*70)
