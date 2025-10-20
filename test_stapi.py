"""
Test script to check STAPI responses and see what data is available
"""

import requests
import json

BASE_URL = "http://stapi.co/api/v1/rest"

def test_endpoint(endpoint, search_term=None):
    """Test an API endpoint and show sample results"""
    print(f"\n{'='*70}")
    print(f"Testing: {endpoint}")
    print(f"{'='*70}")
    
    url = f"{BASE_URL}/{endpoint}/search"
    params = {
        'pageNumber': 0,
        'pageSize': 10
    }
    
    if search_term:
        params['name'] = search_term
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"\nResponse Keys: {list(data.keys())}")
        
        # Try to find the data array
        for key in data.keys():
            if isinstance(data[key], list) and len(data[key]) > 0:
                print(f"\nData found in key: '{key}'")
                print(f"Number of items: {len(data[key])}")
                print(f"\nFirst item sample:")
                print(json.dumps(data[key][0], indent=2, default=str)[:1000] + "...")
                break
        
        # Show page info
        if 'page' in data:
            page = data['page']
            print(f"\nPage Info:")
            print(f"  Page Number: {page.get('pageNumber')}")
            print(f"  Page Size: {page.get('pageSize')}")
            print(f"  Total Elements: {page.get('totalElements')}")
            print(f"  Total Pages: {page.get('totalPages')}")
        
    except Exception as e:
        print(f"Error: {e}")

def test_specific_character(name):
    """Test searching for a specific character"""
    print(f"\n{'='*70}")
    print(f"Searching for: {name}")
    print(f"{'='*70}")
    
    url = f"{BASE_URL}/character/search"
    params = {
        'name': name
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        characters = data.get('characters', [])
        print(f"Found {len(characters)} characters matching '{name}'")
        
        for char in characters:
            print(f"\nName: {char.get('name')}")
            print(f"  Gender: {char.get('gender')}")
            print(f"  Species: {[s.get('name') for s in char.get('characterSpecies', [])]}")
            
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("="*70)
    print("STAPI API TESTING TOOL")
    print("="*70)
    
    # Test various endpoints
    endpoints = [
        'character',
        'performer',
        'species',
        'spacecraft',
        'series',
        'episode'
    ]
    
    for endpoint in endpoints:
        test_endpoint(endpoint)
    
    # Test specific famous characters
    print("\n" + "="*70)
    print("TESTING SPECIFIC CHARACTER SEARCHES")
    print("="*70)
    
    famous_characters = [
        'James T. Kirk',
        'Jean-Luc Picard',
        'Benjamin Sisko',
        'Kathryn Janeway',
        'Spock',
        'Data'
    ]
    
    for character in famous_characters:
        test_specific_character(character)

if __name__ == '__main__':
    main()
