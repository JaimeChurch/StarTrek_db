import requests
import json

r = requests.get('http://stapi.co/api/v1/rest/performer/search', 
                 params={'pageNumber': 0, 'pageSize': 1})
data = r.json()

print("STAPI Performer/Actor Fields:")
print("="*70)
print(json.dumps(data['performers'][0], indent=2))
