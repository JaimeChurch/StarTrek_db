"""
Re-link Character Organizations
This script only re-runs the relationship linking for organizations
"""

import sqlite3
import requests
import time

class RelationshipLinker:
    """Class to link character relationships"""
    
    BASE_URL = "http://stapi.co/api/v1/rest"
    
    def __init__(self, db_path='startrek.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.character_uids = {}
        
    def connect(self):
        """Connect to the database"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def fetch_entity_details(self, endpoint, uid):
        """Fetch detailed information for a single entity by UID"""
        url = f"{self.BASE_URL}/{endpoint}"
        params = {'uid': uid}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # The response key is usually the singular form
            singular_key = endpoint.rstrip('s') if endpoint.endswith('s') else endpoint
            return data.get(singular_key, data.get(endpoint, {}))
            
        except Exception as e:
            print(f"    Error fetching {endpoint}/{uid}: {e}")
            return None
    
    def build_character_uid_cache(self):
        """Build cache of character names to UIDs from search results"""
        print("\n" + "="*70)
        print("BUILDING CHARACTER UID CACHE")
        print("="*70)
        
        page_number = 0
        
        while True:
            print(f"  Page {page_number}...", end='', flush=True)
            
            try:
                response = requests.get(
                    f"{self.BASE_URL}/character/search",
                    params={'pageNumber': page_number, 'pageSize': 100},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    characters = data.get('characters', [])
                    
                    if not characters:
                        print(" Done!")
                        break
                    
                    for char in characters:
                        name = char.get('name')
                        uid = char.get('uid')
                        if name and uid:
                            self.character_uids[name] = uid
                    
                    print(f" +{len(characters)} (cache: {len(self.character_uids)})")
                    
                    page = data.get('page', {})
                    if page.get('lastPage', True):
                        break
                    
                    page_number += 1
                    time.sleep(0.3)
                else:
                    break
                    
            except Exception as e:
                print(f" Error: {e}")
                break
        
        print(f"Cached {len(self.character_uids)} character UIDs")
        return len(self.character_uids)
    
    def link_character_organizations(self):
        """Link characters to organizations using character details"""
        print("\n" + "="*70)
        print("LINKING CHARACTERS TO ORGANIZATIONS")
        print("="*70)
        
        # Clear existing relationships
        print("Clearing existing organization relationships...")
        self.cursor.execute("DELETE FROM Character_Organizations")
        self.conn.commit()
        
        # Get all characters from database
        self.cursor.execute("SELECT character_id, name FROM Characters")
        characters = self.cursor.fetchall()
        
        print(f"Processing {len(characters)} characters...")
        
        linked = 0
        processed = 0
        
        for char_id, char_name in characters:
            processed += 1
            if processed % 100 == 0:
                print(f"  {processed}/{len(characters)} processed, {linked} links created")
                self.conn.commit()
            
            # Get UID from cache
            uid = self.character_uids.get(char_name)
            if not uid:
                continue
            
            try:
                # Fetch character details
                char_details = self.fetch_entity_details('character', uid)
                
                # Use 'organizations' field (not 'characterOrganizations')
                if char_details and char_details.get('organizations'):
                    for org in char_details['organizations']:
                        org_name = org.get('name')
                        if not org_name:
                            continue
                        
                        # Find organization in database
                        self.cursor.execute("""
                            SELECT organization_id FROM Organizations WHERE name = ?
                        """, (org_name,))
                        
                        result = self.cursor.fetchone()
                        if result:
                            org_id = result[0]
                            
                            # Link character to organization
                            self.cursor.execute("""
                                INSERT OR IGNORE INTO Character_Organizations 
                                (character_id, organization_id, role)
                                VALUES (?, ?, ?)
                            """, (char_id, org_id, 'member'))
                            
                            if self.cursor.rowcount > 0:
                                linked += 1
                
                time.sleep(0.2)
                
            except Exception as e:
                continue
        
        self.conn.commit()
        print(f"\nLinked {linked} character-organization relationships")
        return linked
    
    def show_statistics(self):
        """Display database statistics"""
        print("\n" + "="*70)
        print("DATABASE STATISTICS AFTER RE-LINKING")
        print("="*70)
        
        tables = [
            'Character_Organizations',
            'Character_Episodes'
        ]
        
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            print(f"{table:30} {count:6} records")

def main():
    """Main function"""
    print("="*70)
    print("RE-LINK CHARACTER ORGANIZATIONS")
    print("="*70)
    print("\nThis will re-link character-organization relationships")
    print("using the corrected API field names.\n")
    
    response = input("Proceed? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    linker = RelationshipLinker()
    linker.connect()
    
    try:
        # Build UID cache
        linker.build_character_uid_cache()
        
        # Link relationships
        linker.link_character_organizations()
        
        # Show stats
        linker.show_statistics()
        
        print("\n" + "="*70)
        print("RE-LINKING COMPLETE!")
        print("="*70)
        
    except Exception as e:
        print(f"\nError during re-linking: {e}")
        import traceback
        traceback.print_exc()
    finally:
        linker.close()

if __name__ == '__main__':
    main()
