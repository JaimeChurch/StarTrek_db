"""
Add primary_actor_id column to Characters table.
Populate it using Memory Alpha's regular cast page.
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import re

def add_primary_actor_column():
    conn = sqlite3.connect('startrek.db')
    cursor = conn.cursor()
    
    try:
        # Step 1: Add primary_actor_id column to Characters table
        print("Adding primary_actor_id column to Characters table...")
        try:
            cursor.execute("""
                ALTER TABLE Characters 
                ADD COLUMN primary_actor_id INTEGER
            """)
            print("✓ Added primary_actor_id column")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("ℹ primary_actor_id column already exists")
            else:
                raise
        
        conn.commit()
        
        # Step 2: Scrape Memory Alpha regular cast page
        print("\nScraping Memory Alpha regular cast page...")
        url = "https://memory-alpha.fandom.com/wiki/Regular_cast"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all series sections
        cast_data = []
        series_mapping = {
            'Star Trek: The Original Series': 'TOS',
            'Star Trek: The Animated Series': 'TAS',
            'Star Trek: The Next Generation': 'TNG',
            'Star Trek: Deep Space Nine': 'DS9',
            'Star Trek: Voyager': 'VOY',
            'Star Trek: Enterprise': 'ENT',
            'Star Trek: Discovery': 'DIS',
            'Star Trek: Picard': 'PIC',
            'Star Trek: Lower Decks': 'LD',
            'Star Trek: Prodigy': 'PRO',
            'Star Trek: Strange New Worlds': 'SNW'
        }
        
        # Parse each series section
        for series_full, series_abbr in series_mapping.items():
            # Find the heading for this series (look in span.mw-headline)
            heading = None
            for h2 in soup.find_all('h2'):
                span = h2.find('span', class_='mw-headline')
                if span and series_full in span.get_text():
                    heading = h2
                    break
            
            if not heading:
                continue
            
            # Find the next <ul> after this heading
            current = heading.find_next_sibling()
            while current:
                if current.name == 'ul':
                    # Parse the list items
                    for li in current.find_all('li', recursive=False):
                        # Extract actor and character from the links
                        links = li.find_all('a')
                        if len(links) >= 2:
                            actor_name = links[0].get_text(strip=True)
                            character_name = links[1].get_text(strip=True)
                            
                            cast_data.append({
                                'series': series_abbr,
                                'actor': actor_name,
                                'character': character_name
                            })
                    break
                elif current.name == 'h2':
                    break
                current = current.find_next_sibling()
        
        print(f"✓ Scraped {len(cast_data)} regular cast members")
        
        # Step 3: Match and update database
        print("\nMatching cast data to database...")
        updated_count = 0
        not_found_chars = []
        not_found_actors = []
        
        for entry in cast_data:
            # Find character in database - try exact match first, then fuzzy
            cursor.execute("""
                SELECT character_id FROM Characters 
                WHERE LOWER(name) = LOWER(?)
            """, (entry['character'],))
            char_result = cursor.fetchone()
            
            # Try fuzzy matching for character if exact match fails
            if not char_result:
                # Handle specific name variations
                variations = []
                char_lower = entry['character'].lower()
                
                if 'book' in char_lower and 'booker' in char_lower:
                    variations.append('Cleveland Booker')
                elif char_lower == 'raffi musiker':
                    variations.append('Raffaela Musiker')
                elif char_lower.startswith('gwyndala'):
                    variations.append('Gwyndala')
                elif 'diviner' in char_lower:
                    variations.append('The Diviner')
                elif char_lower == 'asencia/the vindicator':
                    variations.append('Asencia')
                
                # Try variations first
                for var in variations:
                    cursor.execute("""
                        SELECT character_id FROM Characters 
                        WHERE LOWER(name) = LOWER(?)
                    """, (var,))
                    char_result = cursor.fetchone()
                    if char_result:
                        break
                
                # Try general fuzzy match (e.g., "Uhura" matches "Nyota Uhura")
                if not char_result:
                    cursor.execute("""
                        SELECT character_id FROM Characters 
                        WHERE LOWER(name) LIKE '%' || LOWER(?) || '%'
                        LIMIT 1
                    """, (entry['character'],))
                    char_result = cursor.fetchone()
            
            if not char_result:
                not_found_chars.append(f"{entry['character']} ({entry['series']})")
                continue
            
            char_id = char_result[0]
            
            # Find actor in database
            actor_parts = entry['actor'].split(None, 1)
            if len(actor_parts) == 2:
                first_name, last_name = actor_parts
            else:
                first_name = actor_parts[0]
                last_name = ''
            
            # Try exact match first
            cursor.execute("""
                SELECT actor_id FROM Actors 
                WHERE LOWER(first_name) = LOWER(?) AND LOWER(last_name) = LOWER(?)
            """, (first_name, last_name))
            actor_result = cursor.fetchone()
            
            # Try without accents (e.g., René -> Rene)
            if not actor_result:
                first_no_accent = first_name.replace('é', 'e').replace('è', 'e').replace('ê', 'e')
                cursor.execute("""
                    SELECT actor_id FROM Actors 
                    WHERE (LOWER(first_name) = LOWER(?) OR LOWER(first_name) = LOWER(?))
                    AND LOWER(last_name) = LOWER(?)
                """, (first_name, first_no_accent, last_name))
                actor_result = cursor.fetchone()
            
            # Try matching on last name only (handles middle names like "Majel Barrett Roddenberry")
            if not actor_result and last_name:
                cursor.execute("""
                    SELECT actor_id FROM Actors 
                    WHERE LOWER(first_name) = LOWER(?)
                    AND LOWER(last_name) LIKE LOWER(?)
                """, (first_name, f'%{last_name}%'))
                actor_result = cursor.fetchone()
            
            # Try fuzzy match via Character_Actors junction table
            if not actor_result:
                cursor.execute("""
                    SELECT a.actor_id 
                    FROM Actors a
                    JOIN Character_Actors ca ON a.actor_id = ca.actor_id
                    WHERE ca.character_id = ?
                    AND (LOWER(a.first_name) LIKE LOWER(?) OR LOWER(a.last_name) LIKE LOWER(?))
                    LIMIT 1
                """, (char_id, f'%{first_name}%', f'%{last_name}%'))
                actor_result = cursor.fetchone()
            
            if not actor_result:
                not_found_actors.append(f"{entry['actor']} -> {entry['character']}")
                continue
            
            actor_id = actor_result[0]
            
            # Update the character with primary_actor_id
            cursor.execute("""
                UPDATE Characters
                SET primary_actor_id = ?
                WHERE character_id = ?
            """, (actor_id, char_id))
            
            updated_count += 1
        
        conn.commit()
        print(f"✓ Updated {updated_count} characters with primary actor assignments")
        
        if not_found_chars:
            print(f"\n⚠ Could not find {len(not_found_chars)} characters in database:")
            for char in not_found_chars[:10]:
                print(f"  - {char}")
            if len(not_found_chars) > 10:
                print(f"  ... and {len(not_found_chars) - 10} more")
        
        if not_found_actors:
            print(f"\n⚠ Could not find {len(not_found_actors)} actors in database:")
            for actor in not_found_actors[:10]:
                print(f"  - {actor}")
            if len(not_found_actors) > 10:
                print(f"  ... and {len(not_found_actors) - 10} more")
        
        # Step 4: Show assigned characters
        print("\n" + "="*80)
        print("ASSIGNED PRIMARY ACTORS")
        print("="*80)
        
        cursor.execute("""
            SELECT 
                c.name as character_name,
                a.first_name || ' ' || a.last_name as primary_actor,
                COUNT(DISTINCT ce.episode_id) as episodes
            FROM Characters c
            JOIN Actors a ON c.primary_actor_id = a.actor_id
            LEFT JOIN Character_Episodes ce ON c.character_id = ce.character_id
            GROUP BY c.character_id, c.name, a.first_name, a.last_name
            ORDER BY episodes DESC
        """)
        
        examples = cursor.fetchall()
        print(f"\nAll {len(examples)} characters with primary actors assigned:")
        for char_name, actor_name, episodes in examples:
            print(f"  {char_name}: {actor_name} ({episodes} episodes)")
        
        # Step 5: Verification statistics
        print("\n" + "="*80)
        print("VERIFICATION STATISTICS")
        print("="*80)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_chars,
                COUNT(primary_actor_id) as chars_with_primary,
                COUNT(*) - COUNT(primary_actor_id) as chars_without_primary
            FROM Characters
        """)
        stats = cursor.fetchone()
        
        print(f"\nTotal characters: {stats[0]}")
        print(f"Characters with primary actor: {stats[1]}")
        print(f"Characters without primary actor: {stats[2]}")
        
        if stats[2] > 0:
            print("\nNote: Characters without primary actor likely have no episode appearances")
        
        print("\n" + "="*80)
        print("COMPLETE!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    add_primary_actor_column()
