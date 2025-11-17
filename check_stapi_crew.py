"""
Check if STAPI provides director and writer information for episodes
"""

import requests
import json

def test_stapi_episode_details():
    """Test STAPI to see what episode details are available"""
    
    base_url = "http://stapi.co/api/v1/rest/episode/search"
    
    # Test with a known episode from TOS
    params = {
        'title': 'The Man Trap',
        'pageSize': 1
    }
    
    print("Testing STAPI for episode crew information...")
    print("="*70)
    
    try:
        response = requests.post(base_url, data=params)
        response.raise_for_status()
        
        data = response.json()
        
        if 'episodes' in data and len(data['episodes']) > 0:
            episode = data['episodes'][0]
            
            print(f"\nEpisode: {episode.get('title', 'N/A')}")
            print(f"Series: {episode.get('series', {}).get('title', 'N/A')}")
            print("\nAvailable fields:")
            print("-"*70)
            
            for key, value in episode.items():
                if value:  # Only show non-empty fields
                    if isinstance(value, (list, dict)):
                        print(f"{key}: {type(value).__name__} (length: {len(value) if isinstance(value, list) else 'N/A'})")
                    else:
                        print(f"{key}: {value}")
            
            # Check specifically for crew information
            print("\n" + "="*70)
            print("CREW INFORMATION CHECK:")
            print("="*70)
            
            if 'directors' in episode:
                print(f"\n✓ Directors available: {episode['directors']}")
            else:
                print("\n✗ No 'directors' field found")
            
            if 'writers' in episode:
                print(f"✓ Writers available: {episode['writers']}")
            else:
                print("✗ No 'writers' field found")
            
            if 'teleplayAuthors' in episode:
                print(f"✓ Teleplay authors available: {episode['teleplayAuthors']}")
            else:
                print("✗ No 'teleplayAuthors' field found")
            
            if 'storyAuthors' in episode:
                print(f"✓ Story authors available: {episode['storyAuthors']}")
            else:
                print("✗ No 'storyAuthors' field found")
            
            if 'usAirDate' in episode:
                print(f"\n✓ US Air Date available: {episode['usAirDate']}")
            else:
                print("\n✗ No 'usAirDate' field found")
            
            # Print full JSON for inspection
            print("\n" + "="*70)
            print("FULL JSON RESPONSE:")
            print("="*70)
            print(json.dumps(episode, indent=2))
            
        else:
            print("No episodes found in response")
            print(json.dumps(data, indent=2))
    
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_stapi_episode_details()
