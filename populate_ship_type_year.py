"""
Populate type and launched_year columns in Ships table from STAPI
"""
import sqlite3
import requests
import time

BASE_URL = "http://stapi.co/api/v1/rest"

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("POPULATING SHIP TYPE AND LAUNCHED_YEAR FROM STAPI")
print("="*70)

# Build spacecraft UID cache
print("\n1. Building spacecraft UID cache...")
uid_cache = {}
page = 0
max_pages = 100

while page < max_pages:
    search_url = f"{BASE_URL}/spacecraft/search"
    params = {'pageNumber': page, 'pageSize': 100}
    
    try:
        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        spacecraft = data.get('spacecrafts', [])
        if not spacecraft:
            break
        
        for ship in spacecraft:
            ship_name = ship.get('name')
            ship_uid = ship.get('uid')
            if ship_name and ship_uid:
                uid_cache[ship_name] = ship_uid
        
        print(f"   Page {page}: cached {len(spacecraft)} UIDs (total: {len(uid_cache)})")
        
        page_info = data.get('page', {})
        if page_info.get('lastPage', True):
            break
        
        page += 1
        time.sleep(0.3)
        
    except Exception as e:
        print(f"   Error fetching page {page}: {e}")
        break

print(f"\n   Total UIDs cached: {len(uid_cache)}")

# Now populate type and launched_year
print("\n2. Populating type and launched_year fields...")

cursor.execute("SELECT ship_id, name FROM Ships")
all_ships = cursor.fetchall()

updated_count = 0
skipped_count = 0

for ship_id, ship_name in all_ships:
    ship_uid = uid_cache.get(ship_name)
    
    if not ship_uid:
        skipped_count += 1
        continue
    
    # Get full spacecraft details
    try:
        detail_url = f"{BASE_URL}/spacecraft"
        response = requests.get(detail_url, params={'uid': ship_uid}, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'spacecraft' in data:
            ship_details = data['spacecraft']
            
            # Get type from spacecraftTypes
            ship_type = None
            spacecraft_types = ship_details.get('spacecraftTypes', [])
            if spacecraft_types and len(spacecraft_types) > 0:
                ship_type = spacecraft_types[0].get('name')
            
            # Get launched_year from dateStatus (if it's a year number)
            launched_year = None
            date_status = ship_details.get('dateStatus')
            if date_status:
                # Try to extract a year if it's a number
                try:
                    # Could be a year like "2381" or a century like "29th century"
                    if isinstance(date_status, int) or (isinstance(date_status, str) and date_status.isdigit()):
                        launched_year = int(date_status)
                except:
                    pass
            
            # Update ship
            if ship_type or launched_year:
                cursor.execute("""
                    UPDATE Ships
                    SET type = ?, launched_year = ?
                    WHERE ship_id = ?
                """, (ship_type, launched_year, ship_id))
                
                updated_count += 1
                if updated_count % 50 == 0:
                    print(f"   Updated {updated_count} ships...")
                    conn.commit()
        
        time.sleep(0.3)  # Rate limiting
        
    except Exception as e:
        skipped_count += 1
        continue

conn.commit()

print("\n" + "="*70)
print(f"Updated {updated_count} ships with type/launched_year")
print(f"Skipped {skipped_count} (no UID or no data)")
print("="*70)

# Show statistics
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN type IS NOT NULL AND type != '' THEN 1 ELSE 0 END) as with_type,
        SUM(CASE WHEN launched_year IS NOT NULL THEN 1 ELSE 0 END) as with_year
    FROM Ships
""")

result = cursor.fetchone()
print(f"\nFinal statistics:")
print(f"  Total ships: {result[0]}")
print(f"  With type: {result[1]} ({result[1]*100/result[0]:.1f}%)")
print(f"  With launched_year: {result[2]} ({result[2]*100/result[0]:.1f}%)")

# Show sample by type
cursor.execute("""
    SELECT type, COUNT(*) as count
    FROM Ships
    WHERE type IS NOT NULL
    GROUP BY type
    ORDER BY count DESC
    LIMIT 10
""")

print("\nShips by type (top 10):")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Show sample
cursor.execute("""
    SELECT name, type, launched_year
    FROM Ships
    WHERE type IS NOT NULL OR launched_year IS NOT NULL
    LIMIT 10
""")

print("\nSample updated records:")
for row in cursor.fetchall():
    print(f"  {row[0]}: type={row[1] or 'N/A'}, year={row[2] or 'N/A'}")

conn.close()
