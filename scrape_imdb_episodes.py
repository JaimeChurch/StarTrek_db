"""
Scrape IMDB episode ratings for all Star Trek series
Updates the Episodes table in the database with IMDB ratings and votes
"""

import requests
import json
import time
import sqlite3
from bs4 import BeautifulSoup

# IMDB series IDs for Star Trek shows
STAR_TREK_SERIES = {
    'TOS': 'tt0060028',      # Star Trek: The Original Series (1966)
    'TAS': 'tt0069637',      # Star Trek: The Animated Series (1973)
    'TNG': 'tt0092455',      # Star Trek: The Next Generation (1987)
    'DS9': 'tt0106145',      # Star Trek: Deep Space Nine (1993)
    'VOY': 'tt0112178',      # Star Trek: Voyager (1995)
    'ENT': 'tt0244365',      # Star Trek: Enterprise (2001)
    'DIS': 'tt5171438',      # Star Trek: Discovery (2017)
    'PIC': 'tt8806524',      # Star Trek: Picard (2020)
    'LD': 'tt9184820',       # Star Trek: Lower Decks (2020)
    'PRO': 'tt9690278',      # Star Trek: Prodigy (2021)
    'SNW': 'tt12327578',     # Star Trek: Strange New Worlds (2022)
}

def get_all_episodes_for_series(series_code, imdb_id):
    """
    Get all episode IDs for a given series from IMDB
    
    Args:
        series_code: Short code like 'TNG'
        imdb_id: IMDB series ID like 'tt0092455'
    
    Returns:
        List of episode dictionaries with season, episode, title, and IMDB ID
    """
    print(f"\nFetching episodes for {series_code}...")
    
    episodes = []
    season = 1
    
    while True:
        url = f"https://www.imdb.com/title/{imdb_id}/episodes?season={season}"
        
        try:
            # Add headers to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find episode containers - IMDB structure may vary, check multiple selectors
            episode_items = soup.find_all('article', class_='episode-item-wrapper')
            
            # If no episodes found, try alternate structure
            if not episode_items:
                episode_items = soup.find_all('div', class_='list_item')
            
            # If still no episodes, assume we've reached the end
            if not episode_items:
                if season == 1:
                    print(f"  Warning: No episodes found for season {season}. Check IMDB structure.")
                else:
                    print(f"  Completed: Found {season - 1} season(s)")
                break
            
            print(f"  Season {season}: {len(episode_items)} episodes")
            
            for item in episode_items:
                # Try to find episode number
                ep_num_elem = item.find('div', class_='ipc-title__text') or item.find('meta', {'itemprop': 'episodeNumber'})
                
                # Extract episode number from text like "S1.E1 ∙ Episode Title"
                if ep_num_elem:
                    text = ep_num_elem.get('content') if ep_num_elem.name == 'meta' else ep_num_elem.get_text()
                    try:
                        # Parse "S1.E1" format
                        if '.' in str(text):
                            parts = str(text).split('.')
                            ep_num = int(parts[1].replace('E', '').strip().split()[0])
                        else:
                            ep_num = int(text)
                    except:
                        ep_num = len([e for e in episodes if e['season'] == season]) + 1
                else:
                    ep_num = len([e for e in episodes if e['season'] == season]) + 1
                
                # Find episode title
                title_elem = item.find('a', class_='ipc-title-link-wrapper') or item.find('a', {'itemprop': 'name'})
                title = title_elem.get_text().strip() if title_elem else "Unknown"
                
                # Remove episode number prefix from title if present (e.g., "S1.E1 ∙ Title" -> "Title")
                if '∙' in title:
                    title = title.split('∙', 1)[1].strip()
                
                # Find IMDB episode ID
                imdb_ep_id = None
                link = item.find('a', href=True)
                if link:
                    href = link['href']
                    if '/title/tt' in href:
                        imdb_ep_id = href.split('/title/')[1].split('/')[0]
                
                # Find episode rating
                rating = None
                votes = None
                
                # Try newer IMDB structure
                rating_elem = item.find('span', class_='ipc-rating-star--rating')
                if rating_elem:
                    try:
                        rating = float(rating_elem.get_text().strip())
                    except:
                        pass
                
                # Try older IMDB structure
                if rating is None:
                    rating_elem = item.find('span', class_='ipl-rating-star__rating')
                    if rating_elem:
                        try:
                            rating = float(rating_elem.get_text().strip())
                        except:
                            pass
                
                # Try to find vote count
                votes_elem = item.find('span', class_='ipc-rating-star--voteCount')
                if votes_elem:
                    try:
                        votes_text = votes_elem.get_text().strip()
                        # Remove parentheses and commas, extract number
                        votes_text = votes_text.replace('(', '').replace(')', '').replace(',', '').replace('K', '000').replace('M', '000000')
                        # Handle formats like "1.2K" -> 1200
                        if '.' in votes_text and '000' in votes_text:
                            votes_text = votes_text.replace('.', '').rstrip('0')
                        votes = int(votes_text) if votes_text.isdigit() else None
                    except:
                        pass
                
                # Try older vote count structure
                if votes is None:
                    votes_elem = item.find('span', class_='ipl-rating-star__total-votes')
                    if votes_elem:
                        try:
                            votes_text = votes_elem.get_text().strip()
                            votes_text = votes_text.replace('(', '').replace(')', '').replace(',', '')
                            votes = int(votes_text) if votes_text.isdigit() else None
                        except:
                            pass
                
                episodes.append({
                    'series': series_code,
                    'season': season,
                    'episode': ep_num,
                    'title': title,
                    'imdb_id': imdb_ep_id,
                    'rating': rating,
                    'votes': votes
                })
            
            season += 1
            time.sleep(1)  # Be nice to IMDB servers
            
        except requests.exceptions.RequestException as e:
            print(f"  Error fetching season {season}: {e}")
            break
        except Exception as e:
            print(f"  Error parsing season {season}: {e}")
            break
    
    return episodes

def main():
    print("="*70)
    print("SCRAPING IMDB EPISODE RATINGS FOR STAR TREK")
    print("="*70)
    
    # Connect to database
    conn = sqlite3.connect('startrek.db')
    cursor = conn.cursor()
    
    # Get series mapping
    cursor.execute("SELECT series_id, abbreviation FROM Series")
    series_map = {abbr: sid for sid, abbr in cursor.fetchall()}
    
    all_episodes = {}
    total_updated = 0
    total_not_found = 0
    
    for series_code, imdb_id in STAR_TREK_SERIES.items():
        episodes = get_all_episodes_for_series(series_code, imdb_id)
        all_episodes[series_code] = episodes
        print(f"  Total episodes scraped for {series_code}: {len(episodes)}")
        
        # Update database
        if series_code not in series_map:
            print(f"  Warning: Series {series_code} not found in database")
            continue
        
        series_id = series_map[series_code]
        updated_count = 0
        not_found_count = 0
        
        for episode in episodes:
            season = episode['season']
            episode_num = episode['episode']
            rating = episode.get('rating')
            votes = episode.get('votes')
            
            # Find the episode in the database
            cursor.execute("""
                SELECT episode_id FROM Episodes 
                WHERE series_id = ? AND season = ? AND episode_number = ?
            """, (series_id, season, episode_num))
            
            result = cursor.fetchone()
            
            if result:
                episode_id = result[0]
                
                # Update the rating and votes
                cursor.execute("""
                    UPDATE Episodes 
                    SET imdb_rating = ?, imdb_votes = ?
                    WHERE episode_id = ?
                """, (rating, votes, episode_id))
                
                updated_count += 1
            else:
                not_found_count += 1
        
        total_updated += updated_count
        total_not_found += not_found_count
        
        print(f"  Database: Updated {updated_count} episodes, {not_found_count} not found")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("\n" + "="*70)
    print(f"DATABASE: Updated {total_updated} episodes with ratings")
    print(f"DATABASE: {total_not_found} episodes not found in database")
    print("="*70)
    
    # Print summary
    print("\nSummary by series:")
    for series_code, episodes in all_episodes.items():
        print(f"  {series_code}: {len(episodes)} episodes")

if __name__ == "__main__":
    main()
