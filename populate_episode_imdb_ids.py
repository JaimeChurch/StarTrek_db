"""
Populate IMDB IDs for episodes by scraping series episode list pages
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
    'ENT': 'tt0244365',
    'TAS': 'tt0070991',
    'DIS': 'tt5171438',
    'PIC': 'tt8806524',
    'LD': 'tt9184820',
    'PRO': 'tt11253774',
    'SNW': 'tt12327578'
}

def get_season_episodes(series_imdb_id, season_num):
    """Get episode IMDB IDs for a specific season"""
    url = f"https://www.imdb.com/title/{series_imdb_id}/episodes/?season={season_num}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        episodes = []
        
        # Find all episode items
        # Look for article elements or divs that contain episode information
        for article in soup.find_all(['article', 'div'], class_=lambda x: x and 'episode' in str(x).lower()):
            # Try to find the episode link
            link = article.find('a', href=lambda x: x and '/title/tt' in str(x))
            if link and link.get('href'):
                href = link.get('href')
                # Extract IMDB ID from href like /title/tt0708414/ or /title/tt0708414/?ref=...
                match = re.search(r'/title/(tt\d+)', href)
                if match:
                    imdb_id = match.group(1)
                    
                    # Try to find episode number
                    ep_num = None
                    # Look for episode number in text
                    text = article.get_text()
                    ep_match = re.search(r'S\d+\.E(\d+)', text) or re.search(r'Ep\.*\s*(\d+)', text, re.IGNORECASE)
                    if ep_match:
                        ep_num = int(ep_match.group(1))
                    else:
                        # Try to find it in a span or div with episode info
                        for elem in article.find_all(['span', 'div', 'h4']):
                            elem_text = elem.get_text()
                            ep_match = re.search(r'(?:Episode|Ep\.?)\s*(\d+)', elem_text, re.IGNORECASE)
                            if ep_match:
                                ep_num = int(ep_match.group(1))
                                break
                    
                    if ep_num:
                        episodes.append((ep_num, imdb_id))
        
        # Sort by episode number
        episodes.sort()
        return episodes
    
    except Exception as e:
        print(f"  Error scraping season {season_num}: {e}")
        return []

def populate_episode_imdb_ids():
    """Populate IMDB IDs for all episodes"""
    conn = sqlite3.connect('startrek.db')
    cursor = conn.cursor()
    
    total_updated = 0
    
    for series_abbr, series_imdb_id in SERIES_IMDB_IDS.items():
        print(f"\n{'='*70}")
        print(f"Processing {series_abbr} ({series_imdb_id})")
        print('='*70)
        
        # Get series_id
        cursor.execute("SELECT series_id FROM Series WHERE abbreviation = ?", (series_abbr,))
        result = cursor.fetchone()
        if not result:
            print(f"✗ Series {series_abbr} not found in database")
            continue
        
        series_id = result[0]
        
        # Get all seasons for this series
        cursor.execute("""
            SELECT DISTINCT season 
            FROM Episodes 
            WHERE series_id = ?
            ORDER BY season
        """, (series_id,))
        
        seasons = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(seasons)} seasons")
        
        updated = 0
        for season in seasons:
            print(f"\n  Season {season}:")
            
            # Scrape episode IDs for this season
            episode_ids = get_season_episodes(series_imdb_id, season)
            print(f"    Found {len(episode_ids)} episode IMDB IDs")
            
            for ep_num, imdb_id in episode_ids:
                # Update the episode in the database
                cursor.execute("""
                    UPDATE Episodes 
                    SET imdb_id = ?
                    WHERE series_id = ? AND season = ? AND episode_number = ?
                """, (imdb_id, series_id, season, ep_num))
                
                if cursor.rowcount > 0:
                    updated += 1
                    print(f"    S{season:02d}E{ep_num:02d}: {imdb_id}")
            
            # Rate limiting between seasons
            time.sleep(1)
        
        conn.commit()
        print(f"\n✓ Updated {updated} episodes for {series_abbr}")
        total_updated += updated
        
        # Rate limiting between series
        time.sleep(2)
    
    conn.close()
    
    print("\n" + "="*70)
    print(f"COMPLETE: Updated {total_updated} episodes with IMDB IDs")
    print("="*70)

if __name__ == "__main__":
    print("="*70)
    print("IMDB EPISODE ID POPULATION")
    print("="*70)
    populate_episode_imdb_ids()
