"""
Populate Star Trek Database using STAPI (Star Trek API)
http://stapi.co/

This script fetches data from STAPI and populates the database
with characters, species, performers (actors), and spacecraft.
"""

import sqlite3
import requests
import time
from datetime import datetime

class STAPIPopulator:
    """Class to handle fetching data from STAPI and populating the database"""
    
    BASE_URL = "http://stapi.co/api/v1/rest"
    
    def __init__(self, db_path='startrek.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to the database"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def fetch_with_pagination(self, endpoint, page_size=100, max_pages=None):
        """
        Fetch data from STAPI with pagination
        
        Args:
            endpoint: API endpoint (e.g., 'character', 'species')
            page_size: Number of results per page
            max_pages: Maximum number of pages to fetch (None = all)
        
        Returns:
            List of all fetched items
        """
        all_items = []
        page_number = 0
        
        # Map endpoint names to their plural response keys
        endpoint_map = {
            'character': 'characters',
            'species': 'species',
            'performer': 'performers',
            'spacecraft': 'spacecraft'
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
            
            print(f"Fetching {endpoint} page {page_number}...")
            
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Try multiple possible keys
                items = None
                for key in [response_key, endpoint, endpoint + 's']:
                    if key in data:
                        items = data[key]
                        break
                
                if items is None:
                    print(f"  No data found. Available keys: {list(data.keys())}")
                    break
                
                if not items:
                    print(f"  Empty results, stopping pagination")
                    break
                    
                all_items.extend(items)
                print(f"  Retrieved {len(items)} items (total: {len(all_items)})")
                
                # Check if this is the last page
                page = data.get('page', {})
                if page.get('lastPage', True):
                    print(f"  Last page reached")
                    break
                    
                page_number += 1
                time.sleep(0.5)  # Be nice to the API
                
            except requests.exceptions.RequestException as e:
                print(f"  Error fetching data: {e}")
                break
        
        return all_items
    
    def populate_species(self, max_pages=2):
        """Fetch and insert species data"""
        print("\n" + "="*70)
        print("POPULATING SPECIES")
        print("="*70)
        
        species_list = self.fetch_with_pagination('species', max_pages=max_pages)
        
        inserted = 0
        for species in species_list:
            try:
                name = species.get('name')
                if not name:
                    continue
                
                homeworld = species.get('homeworld', {}).get('name') if species.get('homeworld') else None
                classification = species.get('type')
                warp_capable = species.get('warpCapableSpecies', False)
                
                self.cursor.execute("""
                    INSERT OR IGNORE INTO Species (name, homeworld, classification, warp_capable)
                    VALUES (?, ?, ?, ?)
                """, (name, homeworld, classification, int(warp_capable)))
                
                if self.cursor.rowcount > 0:
                    inserted += 1
                    
            except Exception as e:
                print(f"Error inserting species {species.get('name')}: {e}")
        
        self.conn.commit()
        print(f"\nInserted {inserted} new species")
        return inserted
    
    def populate_performers(self, max_pages=5):
        """Fetch and insert actor/performer data"""
        print("\n" + "="*70)
        print("POPULATING PERFORMERS (ACTORS)")
        print("="*70)
        
        performers = self.fetch_with_pagination('performer', max_pages=max_pages)
        
        inserted = 0
        for performer in performers:
            try:
                name = performer.get('name', '')
                if not name:
                    continue
                
                # Split name into first and last
                name_parts = name.split(maxsplit=1)
                first_name = name_parts[0] if name_parts else ''
                last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                birth_date = performer.get('birthDate')
                
                # Check if actor already exists
                self.cursor.execute("""
                    SELECT actor_id FROM Actors 
                    WHERE first_name = ? AND last_name = ?
                """, (first_name, last_name))
                
                if self.cursor.fetchone() is None:
                    self.cursor.execute("""
                        INSERT INTO Actors (first_name, last_name, birth_date)
                        VALUES (?, ?, ?)
                    """, (first_name, last_name, birth_date))
                    inserted += 1
                    
            except Exception as e:
                print(f"Error inserting performer {performer.get('name')}: {e}")
        
        self.conn.commit()
        print(f"\nInserted {inserted} new actors")
        return inserted
    
    def populate_characters(self, max_pages=5):
        """Fetch and insert character data"""
        print("\n" + "="*70)
        print("POPULATING CHARACTERS")
        print("="*70)
        
        characters = self.fetch_with_pagination('character', max_pages=max_pages)
        
        inserted = 0
        for character in characters:
            try:
                name = character.get('name')
                if not name or not character.get('uid'):
                    continue
                
                # Get species
                species_name = None
                if character.get('characterSpecies'):
                    species_name = character['characterSpecies'][0].get('name')
                
                species_id = None
                if species_name:
                    self.cursor.execute("SELECT species_id FROM Species WHERE name = ?", (species_name,))
                    result = self.cursor.fetchone()
                    if result:
                        species_id = result[0]
                
                gender = character.get('gender')
                
                # Check if character exists
                self.cursor.execute("SELECT character_id FROM Characters WHERE name = ?", (name,))
                
                if self.cursor.fetchone() is None:
                    self.cursor.execute("""
                        INSERT INTO Characters (name, species_id, gender)
                        VALUES (?, ?, ?)
                    """, (name, species_id, gender))
                    inserted += 1
                    
            except Exception as e:
                print(f"Error inserting character {character.get('name')}: {e}")
        
        self.conn.commit()
        print(f"\nInserted {inserted} new characters")
        return inserted
    
    def populate_spacecraft(self, max_pages=3):
        """Fetch and insert spacecraft data"""
        print("\n" + "="*70)
        print("POPULATING SPACECRAFT")
        print("="*70)
        
        spacecraft_list = self.fetch_with_pagination('spacecraft', max_pages=max_pages)
        
        # Get Starfleet organization ID
        self.cursor.execute("SELECT organization_id FROM Organizations WHERE name = 'Starfleet'")
        result = self.cursor.fetchone()
        starfleet_id = result[0] if result else None
        
        inserted = 0
        for spacecraft in spacecraft_list:
            try:
                name = spacecraft.get('name')
                if not name:
                    continue
                
                registry = spacecraft.get('registry')
                ship_class = spacecraft.get('spacecraftClass', {}).get('name') if spacecraft.get('spacecraftClass') else None
                status = spacecraft.get('status')
                
                # Check if ship exists
                self.cursor.execute("""
                    SELECT ship_id FROM Ships 
                    WHERE name = ? AND (registry = ? OR registry IS NULL)
                """, (name, registry))
                
                if self.cursor.fetchone() is None:
                    self.cursor.execute("""
                        INSERT INTO Ships (name, registry, class, organization_id, status)
                        VALUES (?, ?, ?, ?, ?)
                    """, (name, registry, ship_class, starfleet_id, status))
                    inserted += 1
                    
            except Exception as e:
                print(f"Error inserting spacecraft {spacecraft.get('name')}: {e}")
        
        self.conn.commit()
        print(f"\nInserted {inserted} new spacecraft")
        return inserted
    
    def show_statistics(self):
        """Display database statistics after population"""
        print("\n" + "="*70)
        print("DATABASE STATISTICS AFTER POPULATION")
        print("="*70)
        
        tables = [
            'Species', 'Origins', 'Organizations', 'Actors', 'Ships',
            'Characters', 'Series', 'Episodes'
        ]
        
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            print(f"{table:30} {count:5} records")

def main():
    """Main function to populate the database"""
    print("="*70)
    print("STAR TREK DATABASE POPULATION FROM STAPI")
    print("="*70)
    print("\nThis script will fetch data from http://stapi.co/")
    print("and populate your Star Trek database.")
    print("\nNote: This will take several minutes due to API rate limiting.")
    
    response = input("\nProceed? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    populator = STAPIPopulator()
    populator.connect()
    
    try:
        # Populate in order (species first, then characters that reference species)
        # Set max_pages=None to fetch ALL data
        populator.populate_species(max_pages=None)
        populator.populate_performers(max_pages=None)
        populator.populate_characters(max_pages=None)
        populator.populate_spacecraft(max_pages=None)
        
        # Show final statistics
        populator.show_statistics()
        
        print("\n" + "="*70)
        print("POPULATION COMPLETE!")
        print("="*70)
        
    except Exception as e:
        print(f"\nError during population: {e}")
    finally:
        populator.close()

if __name__ == '__main__':
    main()
