"""
Scrape episode descriptions from IMDB and populate the Episodes table
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import time
import random

# IMDB IDs for Star Trek series
SERIES_IMDB_IDS = {
    'TOS': 'tt0060028',  # The Original Series
    'TAS': 'tt0069637',  # The Animated Series
    'TNG': 'tt0092455',  # The Next Generation
    'DS9': 'tt0106145',  # Deep Space Nine
    'VOY': 'tt0112178',  # Voyager
    'ENT': 'tt0244365',  # Enterprise
    'DSC': 'tt5171438',  # Discovery
    'PIC': 'tt8806524',  # Picard
    'LD': 'tt9184820',   # Lower Decks
    'PRO': 'tt9795876',  # Prodigy
    'SNW': 'tt12327578'  # Strange New Worlds
}

def get_episode_from_imdb_page(series_imdb_id, season, episode_num):
    """
    Get episode description by scraping the series season page
    
    Args:
        series_imdb_id: IMDB ID for the series (e.g., 'tt0092455' for TNG)
        season: Season number
        episode_num: Episode number within the season
    
    Returns:
        str: Episode description/plot summary, or None if not found
    """
    url = f"https://www.imdb.com/title/{series_imdb_id}/episodes?season={season}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        time.sleep(random.uniform(1, 2))  # Rate limiting
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find episode containers
        episode_items = soup.find_all('article', class_='episode-item-wrapper')
        if not episode_items:
            episode_items = soup.find_all('div', class_='list_item')
        
        # Find the specific episode
        for item in episode_items:
            # Try to find episode number
            ep_num_elem = item.find('div', class_='ipc-title__text')
            if ep_num_elem:
                text = ep_num_elem.get_text()
                try:
                    if '.' in str(text):
                        parts = str(text).split('.')
                        ep_num = int(parts[1].replace('E', '').strip().split()[0])
                        
                        if ep_num == episode_num:
                            # Found the right episode, now get description
                            # Try to find plot summary
                            plot_div = item.find('div', class_='ipc-html-content-inner-div')
                            if plot_div:
                                return plot_div.get_text(strip=True)
                            
                            # Try alternate selector
                            plot_span = item.find('div', class_='item_description')
                            if plot_span:
                                return plot_span.get_text(strip=True)
                except:
                    continue
        
        return None
        
    except Exception as e:
        print(f"  Error fetching from season page: {e}")
        return None


def get_episode_description(imdb_episode_id):
    """
    Fetch episode description from IMDB episode page
    
    Args:
        imdb_episode_id: IMDB ID for the episode (e.g., 'tt0708807')
    
    Returns:
        str: Episode description/plot summary, or None if not found
    """
    if not imdb_episode_id:
        return None
    
    url = f"https://www.imdb.com/title/{imdb_episode_id}/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        time.sleep(random.uniform(1, 2))  # Rate limiting
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple selectors for plot summary
        description = None
        
        # Method 1: Look for plot summary span
        plot_span = soup.find('span', {'data-testid': 'plot-xl'})
        if plot_span:
            description = plot_span.get_text(strip=True)
        
        # Method 2: Look for storyline section
        if not description:
            storyline = soup.find('section', {'data-testid': 'Storyline'})
            if storyline:
                plot_div = storyline.find('div', class_='ipc-html-content-inner-div')
                if plot_div:
                    description = plot_div.get_text(strip=True)
        
        # Method 3: Look for any plot/summary meta tags
        if not description:
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '').strip()
        
        return description if description else None
        
    except Exception as e:
        print(f"  Error fetching description for {imdb_episode_id}: {e}")
        return None


def get_episodes_needing_descriptions(db_path='startrek.db'):
    """
    Get all episodes that don't have descriptions yet
    
    Returns:
        list: List of tuples (episode_id, series_abbr, season, episode_num, title, series_imdb_id)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if description column exists in Episodes table
    cursor.execute("PRAGMA table_info(Episodes)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Check if imdb_episode_id column exists
    has_imdb_episode_id = 'imdb_episode_id' in columns
    
    # Check if imdb_id column exists in Series table
    cursor.execute("PRAGMA table_info(Series)")
    series_columns = [col[1] for col in cursor.fetchall()]
    has_series_imdb_id = 'imdb_id' in series_columns
    
    # Add columns if needed
    if 'description' not in columns:
        print("Adding 'description' column to Episodes table...")
        cursor.execute("ALTER TABLE Episodes ADD COLUMN description TEXT")
        conn.commit()
    
    if not has_series_imdb_id:
        print("Adding 'imdb_id' column to Series table...")
        cursor.execute("ALTER TABLE Series ADD COLUMN imdb_id TEXT")
        conn.commit()
        
        # Populate IMDB IDs for series
        print("Populating Series IMDB IDs...")
        for abbr, imdb_id in SERIES_IMDB_IDS.items():
            cursor.execute("UPDATE Series SET imdb_id = ? WHERE abbreviation = ?", (imdb_id, abbr))
        conn.commit()
    
    # Get episodes without descriptions
    cursor.execute("""
        SELECT e.episode_id, s.abbreviation, e.season, e.episode_number, e.title, s.imdb_id
        FROM Episodes e
        JOIN Series s ON e.series_id = s.series_id
        WHERE (e.description IS NULL OR e.description = '') AND s.imdb_id IS NOT NULL
        ORDER BY s.abbreviation, e.season, e.episode_number
    """)
    
    episodes = cursor.fetchall()
    conn.close()
    
    return episodes


def update_episode_description(episode_id, description, db_path='startrek.db'):
    """Update episode description in database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE Episodes
        SET description = ?
        WHERE episode_id = ?
    """, (description, episode_id))
    
    conn.commit()
    conn.close()


def populate_episode_descriptions(db_path='startrek.db', limit=None):
    """
    Main function to populate episode descriptions
    
    Args:
        db_path: Path to SQLite database
        limit: Optional limit on number of episodes to process (for testing)
    """
    print("="*70)
    print("POPULATING EPISODE DESCRIPTIONS FROM IMDB")
    print("="*70)
    
    episodes = get_episodes_needing_descriptions(db_path)
    
    if not episodes:
        print("\nNo episodes need descriptions! All done.")
        return
    
    total = len(episodes)
    if limit:
        episodes = episodes[:limit]
        print(f"\nProcessing {len(episodes)} of {total} episodes (limited for testing)")
    else:
        print(f"\nFound {total} episodes needing descriptions")
    
    print("\nStarting to fetch descriptions from IMDB...")
    print("This will take a while due to rate limiting...\n")
    
    success_count = 0
    fail_count = 0
    
    for i, (episode_id, series_code, season, episode_num, title, series_imdb_id) in enumerate(episodes, 1):
        print(f"[{i}/{len(episodes)}] {series_code} S{season:02d}E{episode_num:02d}: {title}")
        
        # Try to get description from season page
        description = get_episode_from_imdb_page(series_imdb_id, season, episode_num)
        
        if description:
            update_episode_description(episode_id, description, db_path)
            print(f"  ✓ Description saved ({len(description)} chars)")
            success_count += 1
        else:
            print(f"  ✗ No description found")
            fail_count += 1
        
        # Progress update every 10 episodes
        if i % 10 == 0:
            print(f"\n--- Progress: {i}/{len(episodes)} episodes processed ---")
            print(f"    Success: {success_count}, Failed: {fail_count}\n")
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total episodes processed: {len(episodes)}")
    print(f"Descriptions added: {success_count}")
    print(f"Failed to fetch: {fail_count}")
    print(f"Success rate: {100*success_count/len(episodes):.1f}%")
    print("="*70)


if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"\nRunning in TEST MODE - processing only {limit} episodes")
            populate_episode_descriptions(limit=limit)
        except ValueError:
            print("Usage: python populate_episode_descriptions.py [limit]")
            print("  limit: optional number of episodes to process (for testing)")
    else:
        # Confirm before processing all
        response = input("\nThis will fetch descriptions for ALL episodes. Continue? (y/n): ")
        if response.lower() == 'y':
            populate_episode_descriptions()
        else:
            print("Cancelled.")
