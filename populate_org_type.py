"""
Populate type column in Organizations table from STAPI boolean flags
"""
import sqlite3
import requests
import time

BASE_URL = "http://stapi.co/api/v1/rest"

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("POPULATING ORGANIZATION TYPE FROM STAPI")
print("="*70)

# Build organization UID cache
print("\n1. Building organization UID cache...")
uid_cache = {}
page = 0
max_pages = 100

while page < max_pages:
    search_url = f"{BASE_URL}/organization/search"
    params = {'pageNumber': page, 'pageSize': 100}
    
    try:
        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        organizations = data.get('organizations', [])
        if not organizations:
            break
        
        for org in organizations:
            org_name = org.get('name')
            org_uid = org.get('uid')
            if org_name and org_uid:
                uid_cache[org_name] = org_uid
        
        print(f"   Page {page}: cached {len(organizations)} UIDs (total: {len(uid_cache)})")
        
        page_info = data.get('page', {})
        if page_info.get('lastPage', True):
            break
        
        page += 1
        time.sleep(0.3)
        
    except Exception as e:
        print(f"   Error fetching page {page}: {e}")
        break

print(f"\n   Total UIDs cached: {len(uid_cache)}")

# Now populate type
print("\n2. Populating type field...")

cursor.execute("SELECT organization_id, name FROM Organizations")
all_organizations = cursor.fetchall()

updated_count = 0
skipped_count = 0

for org_id, org_name in all_organizations:
    org_uid = uid_cache.get(org_name)
    
    if not org_uid:
        skipped_count += 1
        continue
    
    # Get full organization details
    try:
        detail_url = f"{BASE_URL}/organization"
        response = requests.get(detail_url, params={'uid': org_uid}, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'organization' in data:
            org_details = data['organization']
            
            # Determine type from boolean flags (priority order)
            org_type = None
            
            if org_details.get('government'):
                org_type = 'government'
            elif org_details.get('militaryOrganization'):
                org_type = 'military'
            elif org_details.get('governmentAgency'):
                org_type = 'government agency'
            elif org_details.get('lawEnforcementAgency'):
                org_type = 'law enforcement'
            elif org_details.get('researchOrganization'):
                org_type = 'research'
            elif org_details.get('medicalOrganization'):
                org_type = 'medical'
            elif org_details.get('sportOrganization'):
                org_type = 'sport'
            elif org_details.get('intergovernmentalOrganization'):
                org_type = 'intergovernmental'
            elif org_details.get('militaryUnit'):
                org_type = 'military unit'
            
            # Update organization
            if org_type:
                cursor.execute("""
                    UPDATE Organizations
                    SET type = ?
                    WHERE organization_id = ?
                """, (org_type, org_id))
                
                updated_count += 1
                if updated_count % 50 == 0:
                    print(f"   Updated {updated_count} organizations...")
                    conn.commit()
        
        time.sleep(0.3)  # Rate limiting
        
    except Exception as e:
        skipped_count += 1
        continue

conn.commit()

print("\n" + "="*70)
print(f"Updated {updated_count} organizations with type")
print(f"Skipped {skipped_count} (no UID or no type flags)")
print("="*70)

# Show statistics
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN type IS NOT NULL AND type != '' THEN 1 ELSE 0 END) as with_type
    FROM Organizations
""")

result = cursor.fetchone()
print(f"\nFinal statistics:")
print(f"  Total organizations: {result[0]}")
print(f"  With type: {result[1]} ({result[1]*100/result[0]:.1f}%)")

# Show sample by type
cursor.execute("""
    SELECT type, COUNT(*) as count
    FROM Organizations
    WHERE type IS NOT NULL
    GROUP BY type
    ORDER BY count DESC
""")

print("\nOrganizations by type:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Show sample
cursor.execute("""
    SELECT name, type
    FROM Organizations
    WHERE type IS NOT NULL
    LIMIT 10
""")

print("\nSample updated records:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
