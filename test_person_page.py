"""
Test what's on a director's IMDB page to see episode information
"""
import requests
from bs4 import BeautifulSoup

# Test with a known TOS director
person_url = "https://www.imdb.com/name/nm0515237/"  # David Livingston (DS9 director)
series_imdb_id = 'tt0106145'  # DS9

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(person_url, headers=headers, timeout=15)
soup = BeautifulSoup(response.content, 'html.parser')

print(f"Looking for DS9 episodes on {person_url}\n")
print("="*70)

# Look for links to the series
count = 0
for link in soup.find_all('a', href=True):
    if series_imdb_id in link['href']:
        count += 1
        print(f"Found link #{count}:")
        print(f"  href: {link['href']}")
        print(f"  text: {link.get_text(strip=True)}")
        # Get surrounding context
        parent = link.find_parent('div', class_=lambda x: x and 'ipc' in str(x))
        if parent:
            print(f"  context: {parent.get_text(strip=True)[:200]}")
        print()
        
        if count >= 5:  # Just show first 5 for testing
            break

print(f"\nTotal links found with {series_imdb_id}: {count}")
