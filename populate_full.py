"""
Full Population Script for Star Trek Database using STAPI
This script fetches detailed entity data to populate ALL tables including relationships
"""

import sqlite3
import requests
import time
from datetime import datetime

class STAPIFullPopulator:
    """Enhanced class to fully populate all tables including relationships"""
    
    BASE_URL = "http://stapi.co/api/v1/rest"
    
    def __init__(self, db_path='startrek.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # Cache mappings: name -> uid
        self.character_uids = {}
        self.episode_uids = {}
        self.ship_uids = {}
        
    def connect(self):
        """Connect to the database"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def fetch_with_pagination(self, endpoint, page_size=100, max_pages=None):
        """Fetch data with pagination"""
        all_items = []
        page_number = 0
        
        endpoint_map = {
            'character': 'characters',
            'species': 'species',
            'performer': 'performers',
            'spacecraft': 'spacecraft',
            'series': 'series',
            'episode': 'episodes',
            'organization': 'organizations'
        }
        
        response_key = endpoint_map.get(endpoint, endpoint + 's')
        
        while True:
            if max_pages and page_number >= max_pages:
                break
                
            url = f"{self.BASE_URL}/{endpoint}/search"
            params = {
                'pageNumber': page_number,
                'pageSize': page_size
            }
            
            print(f"  Page {page_number}...", end='', flush=True)
            
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                items = None
                for key in [response_key, endpoint, endpoint + 's']:
                    if key in data:
                        items = data[key]
                        break
                
                if items is None or not items:
                    print(f" Done!")
                    break
                    
                all_items.extend(items)
                print(f" +{len(items)} (total: {len(all_items)})")
                
                page = data.get('page', {})
                if page.get('lastPage', True):
                    break
                    
                page_number += 1
                time.sleep(0.3)
                
            except requests.exceptions.RequestException as e:
                print(f" Error: {e}")
                break
        
        return all_items
    
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
    
    def populate_series(self):
        """Populate series table"""
        print("\n" + "="*70)
        print("POPULATING SERIES")
        print("="*70)
        
        series_list = self.fetch_with_pagination('series', max_pages=None)
        
        inserted = 0
        for series in series_list:
            try:
                title = series.get('title')
                if not title:
                    continue
                
                abbreviation = series.get('abbreviation')
                
                # Parse years
                production_start = series.get('productionStartYear')
                production_end = series.get('productionEndYear')
                
                num_seasons = series.get('seasonsCount')
                num_episodes = series.get('episodesCount')
                
                self.cursor.execute("""
                    INSERT OR IGNORE INTO Series 
                    (name, abbreviation, start_year, end_year, num_seasons, num_episodes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, abbreviation, production_start, production_end, num_seasons, num_episodes))
                
                if self.cursor.rowcount > 0:
                    inserted += 1
                    
            except Exception as e:
                print(f"  Error inserting series {series.get('title')}: {e}")
        
        self.conn.commit()
        print(f"Inserted {inserted} new series")
        return inserted
    
    def populate_episodes(self, max_pages=None):
        """Populate episodes table"""
        print("\n" + "="*70)
        print("POPULATING EPISODES")
        print("="*70)
        
        episodes = self.fetch_with_pagination('episode', max_pages=max_pages)
        
        inserted = 0
        for episode in episodes:
            try:
                title = episode.get('title')
                if not title:
                    continue
                
                # Get series
                series_data = episode.get('series')
                series_id = None
                if series_data:
                    series_title = series_data.get('title')
                    self.cursor.execute("SELECT series_id FROM Series WHERE name = ?", (series_title,))
                    result = self.cursor.fetchone()
                    if result:
                        series_id = result[0]
                
                season = episode.get('seasonNumber')
                episode_num = episode.get('episodeNumber')
                
                # Parse air date (format: YYYY-MM-DD)
                air_date = episode.get('usAirDate')
                
                self.cursor.execute("""
                    INSERT OR IGNORE INTO Episodes 
                    (series_id, title, season, episode_number, air_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (series_id, title, season, episode_num, air_date))
                
                if self.cursor.rowcount > 0:
                    inserted += 1
                    
            except Exception as e:
                print(f"  Error inserting episode {episode.get('title')}: {e}")
        
        self.conn.commit()
        print(f"Inserted {inserted} new episodes")
        return inserted
    
    def populate_organizations(self):
        """Populate organizations table"""
        print("\n" + "="*70)
        print("POPULATING ORGANIZATIONS")
        print("="*70)
        
        orgs = self.fetch_with_pagination('organization', max_pages=None)
        
        inserted = 0
        for org in orgs:
            try:
                name = org.get('name')
                if not name:
                    continue
                
                self.cursor.execute("""
                    INSERT OR IGNORE INTO Organizations (name)
                    VALUES (?)
                """, (name,))
                
                if self.cursor.rowcount > 0:
                    inserted += 1
                    
            except Exception as e:
                print(f"  Error inserting organization {org.get('name')}: {e}")
        
        self.conn.commit()
        print(f"Inserted {inserted} new organizations")
        return inserted
    
    def build_character_uid_cache(self, max_pages=None):
        """Build cache of character names to UIDs from search results"""
        print("\n" + "="*70)
        print("BUILDING CHARACTER UID CACHE")
        print("="*70)
        
        page_number = 0
        
        while True:
            if max_pages and page_number >= max_pages:
                break
                
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
    
    def build_episode_uid_cache(self, max_pages=None):
        """Build cache of episode titles to UIDs"""
        print("\n" + "="*70)
        print("BUILDING EPISODE UID CACHE")
        print("="*70)
        
        page_number = 0
        
        while True:
            if max_pages and page_number >= max_pages:
                break
                
            print(f"  Page {page_number}...", end='', flush=True)
            
            try:
                response = requests.get(
                    f"{self.BASE_URL}/episode/search",
                    params={'pageNumber': page_number, 'pageSize': 100},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    episodes = data.get('episodes', [])
                    
                    if not episodes:
                        print(" Done!")
                        break
                    
                    for ep in episodes:
                        title = ep.get('title')
                        uid = ep.get('uid')
                        if title and uid:
                            self.episode_uids[title] = uid
                    
                    print(f" +{len(episodes)} (cache: {len(self.episode_uids)})")
                    
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
        
        print(f"Cached {len(self.episode_uids)} episode UIDs")
        return len(self.episode_uids)
    
    def link_character_performers(self, max_chars=None):
        """Link characters to performers (actors) using cached UIDs"""
        print("\n" + "="*70)
        print("LINKING CHARACTERS TO ACTORS")
        print("="*70)
        
        # Get all characters from database
        self.cursor.execute("SELECT character_id, name FROM Characters")
        characters = self.cursor.fetchall()
        
        if max_chars:
            characters = characters[:max_chars]
        
        print(f"Processing {len(characters)} characters...")
        
        linked = 0
        processed = 0
        
        for char_id, char_name in characters:
            processed += 1
            if processed % 100 == 0:
                print(f"  {processed}/{len(characters)} processed, {linked} links created")
                self.conn.commit()  # Commit periodically
            
            # Get UID from cache
            uid = self.character_uids.get(char_name)
            if not uid:
                continue
            
            try:
                # Fetch full character details
                char_details = self.fetch_entity_details('character', uid)
                
                if char_details and char_details.get('performers'):
                    for performer in char_details['performers']:
                        performer_name = performer.get('name', '')
                        if not performer_name:
                            continue
                        
                        # Split name
                        name_parts = performer_name.split(maxsplit=1)
                        first_name = name_parts[0] if name_parts else ''
                        last_name = name_parts[1] if len(name_parts) > 1 else ''
                        
                        # Find actor in database
                        self.cursor.execute("""
                            SELECT actor_id FROM Actors 
                            WHERE first_name = ? AND last_name = ?
                        """, (first_name, last_name))
                        
                        result = self.cursor.fetchone()
                        if result:
                            actor_id = result[0]
                            
                            # Link character to actor
                            self.cursor.execute("""
                                INSERT OR IGNORE INTO Character_Actors 
                                (character_id, actor_id)
                                VALUES (?, ?)
                            """, (char_id, actor_id))
                            
                            if self.cursor.rowcount > 0:
                                linked += 1
                
                time.sleep(0.2)  # Rate limiting
                
            except Exception as e:
                continue
        
        self.conn.commit()
        print(f"\nLinked {linked} character-actor relationships")
        return linked
    
    def link_character_episodes(self, max_episodes=None):
        """Link characters to episodes they appeared in using cached UIDs"""
        print("\n" + "="*70)
        print("LINKING CHARACTERS TO EPISODES")
        print("="*70)
        
        # Get all episodes from database
        self.cursor.execute("SELECT episode_id, title FROM Episodes")
        episodes = self.cursor.fetchall()
        
        if max_episodes:
            episodes = episodes[:max_episodes]
        
        print(f"Processing {len(episodes)} episodes...")
        
        linked = 0
        processed = 0
        
        for episode_id, episode_title in episodes:
            processed += 1
            if processed % 50 == 0:
                print(f"  {processed}/{len(episodes)} processed, {linked} links created")
                self.conn.commit()  # Commit periodically
            
            # Get UID from cache
            uid = self.episode_uids.get(episode_title)
            if not uid:
                continue
            
            try:
                # Fetch episode details
                ep_details = self.fetch_entity_details('episode', uid)
                
                if ep_details and ep_details.get('characters'):
                    for character in ep_details['characters']:
                        char_name = character.get('name')
                        if not char_name:
                            continue
                        
                        # Find character in database
                        self.cursor.execute("""
                            SELECT character_id FROM Characters WHERE name = ?
                        """, (char_name,))
                        
                        result = self.cursor.fetchone()
                        if result:
                            char_id = result[0]
                            
                            # Link character to episode
                            self.cursor.execute("""
                                INSERT OR IGNORE INTO Character_Episodes 
                                (character_id, episode_id, role_type)
                                VALUES (?, ?, ?)
                            """, (char_id, episode_id, 'main'))
                            
                            if self.cursor.rowcount > 0:
                                linked += 1
                
                time.sleep(0.2)
                
            except Exception as e:
                continue
        
        self.conn.commit()
        print(f"\nLinked {linked} character-episode relationships")
        return linked
    
    def link_character_organizations(self, max_chars=None):
        """Link characters to organizations using character details"""
        print("\n" + "="*70)
        print("LINKING CHARACTERS TO ORGANIZATIONS")
        print("="*70)
        
        # Get all characters from database
        self.cursor.execute("SELECT character_id, name FROM Characters")
        characters = self.cursor.fetchall()
        
        if max_chars:
            characters = characters[:max_chars]
        
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
                
                if char_details and char_details.get('characterOrganizations'):
                    for org in char_details['characterOrganizations']:
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
    
    def link_character_ships(self, max_chars=None):
        """Link characters to ships using character details"""
        print("\n" + "="*70)
        print("LINKING CHARACTERS TO SHIPS")
        print("="*70)
        
        # Get all characters from database
        self.cursor.execute("SELECT character_id, name FROM Characters")
        characters = self.cursor.fetchall()
        
        if max_chars:
            characters = characters[:max_chars]
        
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
                
                if char_details and char_details.get('characterSpacecrafts'):
                    for ship in char_details['characterSpacecrafts']:
                        ship_name = ship.get('name')
                        if not ship_name:
                            continue
                        
                        # Find ship in database (match by name)
                        self.cursor.execute("""
                            SELECT ship_id FROM Ships WHERE name = ?
                        """, (ship_name,))
                        
                        result = self.cursor.fetchone()
                        if result:
                            ship_id = result[0]
                            
                            # Link character to ship
                            self.cursor.execute("""
                                INSERT OR IGNORE INTO Character_Ships 
                                (character_id, ship_id, role)
                                VALUES (?, ?, ?)
                            """, (char_id, ship_id, 'crew member'))
                            
                            if self.cursor.rowcount > 0:
                                linked += 1
                
                time.sleep(0.2)
                
            except Exception as e:
                continue
        
        self.conn.commit()
        print(f"\nLinked {linked} character-ship relationships")
        return linked
    
    def show_statistics(self):
        """Display database statistics"""
        print("\n" + "="*70)
        print("FINAL DATABASE STATISTICS")
        print("="*70)
        
        tables = [
            'Species', 'Organizations', 'Actors', 'Ships',
            'Characters', 'Series', 'Episodes', 'Character_Actors',
            'Character_Organizations', 'Character_Ships', 'Character_Episodes'
        ]
        
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            print(f"{table:30} {count:6} records")

def main():
    """Main function"""
    print("="*70)
    print("FULL STAR TREK DATABASE POPULATION FROM STAPI")
    print("="*70)
    print("\nThis will fetch ALL data including relationships.")
    print("This may take 30-60 minutes due to API rate limiting.\n")
    
    response = input("Proceed? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    populator = STAPIFullPopulator()
    populator.connect()
    
    try:
        # Step 1: Populate main tables (already done, but will add any new)
        print("\n" + "="*70)
        print("STEP 1: UPDATING MAIN TABLES")
        print("="*70)
        
        populator.populate_series()
        populator.populate_organizations()
        populator.populate_episodes(max_pages=None)  # Fetch ALL episodes
        
        # Step 2: Build UID caches
        print("\n" + "="*70)
        print("STEP 2: BUILDING UID CACHES")
        print("="*70)
        
        populator.build_character_uid_cache(max_pages=None)
        populator.build_episode_uid_cache(max_pages=None)
        
        # Step 3: Link relationships
        print("\n" + "="*70)
        print("STEP 3: LINKING RELATIONSHIPS")
        print("="*70)
        print("\nNote: This step is intensive and may take a while...")
        
        # Link ALL characters (remove max_chars limit)
        populator.link_character_performers(max_chars=None)
        
        # Link all episodes
        populator.link_character_episodes(max_episodes=None)
        
        # Link ALL character organizations
        populator.link_character_organizations(max_chars=None)
        
        # Link ALL character ships
        populator.link_character_ships(max_chars=None)
        
        # Show final stats
        populator.show_statistics()
        
        print("\n" + "="*70)
        print("FULL POPULATION COMPLETE!")
        print("="*70)
        print("\nDatabase is now fully populated with all available data from STAPI!")
        
    except Exception as e:
        print(f"\nError during population: {e}")
        import traceback
        traceback.print_exc()
    finally:
        populator.close()

if __name__ == '__main__':
    main()
