"""
Scrape director and writer from IMDB episode pages and populate Episodes table
For each episode in the database, visits its IMDB page to get director/writer info
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import time
import re

SERIES_IMDB_IDS = {
    'TOS': 'tt0060028',
    'TNG': 'tt0092455',
    'DS9': 'tt0106145',
    'VOY': 'tt0112178',
    'ENT': 'tt0244365'
}

def add_crew_columns():
    """Add director and writer columns to Episodes table"""
    conn = sqlite3.connect('startrek.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE Episodes ADD COLUMN director TEXT")
        print("✓ Added 'director' column")
    except sqlite3.OperationalError:
        print("'director' column already exists")
    
    try:
        cursor.execute("ALTER TABLE Episodes ADD COLUMN writer TEXT")
        print("✓ Added 'writer' column")
    except sqlite3.OperationalError:
        print("'writer' column already exists")
    
    conn.commit()
    conn.close()

def get_episode_crew(episode_imdb_id):
    """Get director and writer(s) for a specific episode"""
    url = f"https://www.imdb.com/title/{episode_imdb_id}/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        director = None
        writers = []
        
        # Look for Director and Writers in credits
        # They typically appear as "Director" or "Writers" followed by names
        for li in soup.find_all('li', class_=lambda x: x and 'ipc-metadata-list__item' in str(x)):
            text = li.get_text()
            
            # Check for Director
            if 'Director' in text and 'Directors' not in text:
                links = li.find_all('a')
                if links:
                    director = links[0].get_text(strip=True)
            
            # Check for Writers - include all writers from the Writers section
            if 'Writer' in text:
                links = li.find_all('a')
                for link in links:
                    writer_name = link.get_text(strip=True)
                    if writer_name and writer_name not in writers:
                        writers.append(writer_name)
        
        return {
            'director': director,
            'writer': ', '.join(writers) if writers else None
        }
    
    except Exception as e:
        print(f"    Error: {e}")
        return {'director': None, 'writer': None}

def populate_crew_data():
    """Populate director and writer for all episodes"""
    conn = sqlite3.connect('startrek.db')
    cursor = conn.cursor()
    
    total_updated = 0
    
    for series_abbr, series_imdb_id in SERIES_IMDB_IDS.items():
        print(f"\n{'='*70}")
        print(f"Processing {series_abbr}")
        print('='*70)
        
        # Get series_id
        cursor.execute("SELECT series_id FROM Series WHERE abbreviation = ?", (series_abbr,))
        result = cursor.fetchone()
        if not result:
            print(f"✗ Series {series_abbr} not found in database")
            continue
        
        series_id = result[0]
        
        # Get all episodes for this series that have IMDB IDs
        cursor.execute("""
            SELECT episode_id, season, episode_number, title, imdb_id
            FROM Episodes
            WHERE series_id = ? AND imdb_id IS NOT NULL
            ORDER BY season, episode_number
        """, (series_id,))
        
        episodes = cursor.fetchall()
        print(f"Found {len(episodes)} episodes with IMDB IDs")
        
        if not episodes:
            print(f"✗ No episodes with IMDB IDs for {series_abbr}")
            continue
        
        updated = 0
        for episode_id, season, ep_num, title, imdb_id in episodes:
            print(f"  S{season:02d}E{ep_num:02d}: {title}")
            
            crew = get_episode_crew(imdb_id)
            
            if crew['director'] or crew['writer']:
                cursor.execute("""
                    UPDATE Episodes 
                    SET director = ?, writer = ?
                    WHERE episode_id = ?
                """, (crew['director'], crew['writer'], episode_id))
                
                if cursor.rowcount > 0:
                    updated += 1
                    if crew['director']:
                        print(f"    Director: {crew['director']}")
                    if crew['writer']:
                        print(f"    Writer: {crew['writer']}")
            
            # Rate limiting
            time.sleep(0.5)
        
        conn.commit()
        print(f"✓ Updated {updated} episodes for {series_abbr}")
        total_updated += updated
        
        # Rate limiting between series
        time.sleep(2)
    
    conn.close()
    
    print("\n" + "="*70)
    print(f"COMPLETE: Updated {total_updated} episodes total")
    print("="*70)

if __name__ == "__main__":
    print("="*70)
    print("IMDB FULLCREDITS CREW DATA POPULATION")
    print("="*70)
    
    add_crew_columns()
    populate_crew_data()
