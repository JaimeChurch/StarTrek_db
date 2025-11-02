"""
Find ALL duplicates across ALL tables based on logical unique keys
"""

import sqlite3

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("CHECKING ALL TABLES FOR DUPLICATES")
print("="*70)

all_duplicates = []

# 1. Check Episodes - should be unique by (series_id, season, episode_number)
print("\n" + "="*70)
print("EPISODES TABLE")
print("="*70)
cursor.execute("""
SELECT series_id, season, episode_number, COUNT(*) as count
FROM Episodes
GROUP BY series_id, season, episode_number
HAVING COUNT(*) > 1
""")
ep_dupes = cursor.fetchall()
if ep_dupes:
    print(f"Found {len(ep_dupes)} duplicate episode combinations")
    total_extra = sum(count - 1 for _, _, _, count in ep_dupes)
    print(f"Total extra entries: {total_extra}")
    for series_id, season, ep_num, count in ep_dupes[:10]:
        cursor.execute("SELECT abbreviation FROM Series WHERE series_id = ?", (series_id,))
        series = cursor.fetchone()
        print(f"  {series[0] if series else 'Unknown'} S{season}E{ep_num}: {count} copies")
    all_duplicates.append(('Episodes', len(ep_dupes), total_extra))
else:
    print("✓ No duplicates found")

# 2. Check Characters - should be unique by name
print("\n" + "="*70)
print("CHARACTERS TABLE")
print("="*70)
cursor.execute("""
SELECT name, COUNT(*) as count
FROM Characters
GROUP BY name
HAVING COUNT(*) > 1
""")
char_dupes = cursor.fetchall()
if char_dupes:
    print(f"Found {len(char_dupes)} duplicate character names")
    total_extra = sum(count - 1 for _, count in char_dupes)
    print(f"Total extra entries: {total_extra}")
    for name, count in char_dupes[:10]:
        print(f"  {name}: {count} copies")
    all_duplicates.append(('Characters', len(char_dupes), total_extra))
else:
    print("✓ No duplicates found")

# 3. Check Actors - should be unique by (first_name, last_name, birth_date)
print("\n" + "="*70)
print("ACTORS TABLE")
print("="*70)
cursor.execute("""
SELECT first_name, last_name, birth_date, COUNT(*) as count
FROM Actors
GROUP BY first_name, last_name, birth_date
HAVING COUNT(*) > 1
""")
actor_dupes = cursor.fetchall()
if actor_dupes:
    print(f"Found {len(actor_dupes)} duplicate actors")
    total_extra = sum(count - 1 for _, _, _, count in actor_dupes)
    print(f"Total extra entries: {total_extra}")
    for first, last, bdate, count in actor_dupes[:10]:
        print(f"  {first} {last} ({bdate}): {count} copies")
    all_duplicates.append(('Actors', len(actor_dupes), total_extra))
else:
    print("✓ No duplicates found")

# 4. Check Species - should be unique by name
print("\n" + "="*70)
print("SPECIES TABLE")
print("="*70)
cursor.execute("""
SELECT name, COUNT(*) as count
FROM Species
GROUP BY name
HAVING COUNT(*) > 1
""")
species_dupes = cursor.fetchall()
if species_dupes:
    print(f"Found {len(species_dupes)} duplicate species")
    total_extra = sum(count - 1 for _, count in species_dupes)
    print(f"Total extra entries: {total_extra}")
    for name, count in species_dupes[:10]:
        print(f"  {name}: {count} copies")
    all_duplicates.append(('Species', len(species_dupes), total_extra))
else:
    print("✓ No duplicates found")

# 5. Check Organizations - should be unique by name
print("\n" + "="*70)
print("ORGANIZATIONS TABLE")
print("="*70)
cursor.execute("""
SELECT name, COUNT(*) as count
FROM Organizations
GROUP BY name
HAVING COUNT(*) > 1
""")
org_dupes = cursor.fetchall()
if org_dupes:
    print(f"Found {len(org_dupes)} duplicate organizations")
    total_extra = sum(count - 1 for _, count in org_dupes)
    print(f"Total extra entries: {total_extra}")
    for name, count in org_dupes[:10]:
        print(f"  {name}: {count} copies")
    all_duplicates.append(('Organizations', len(org_dupes), total_extra))
else:
    print("✓ No duplicates found")

# 6. Check Ships - should be unique by (name, registry)
print("\n" + "="*70)
print("SHIPS TABLE")
print("="*70)
cursor.execute("""
SELECT name, registry, COUNT(*) as count
FROM Ships
GROUP BY name, registry
HAVING COUNT(*) > 1
""")
ship_dupes = cursor.fetchall()
if ship_dupes:
    print(f"Found {len(ship_dupes)} duplicate ships")
    total_extra = sum(count - 1 for _, _, count in ship_dupes)
    print(f"Total extra entries: {total_extra}")
    for name, registry, count in ship_dupes[:10]:
        print(f"  {name} ({registry}): {count} copies")
    all_duplicates.append(('Ships', len(ship_dupes), total_extra))
else:
    print("✓ No duplicates found")

# 7. Check Character_Actors - should be unique by (character_id, actor_id, series)
print("\n" + "="*70)
print("CHARACTER_ACTORS TABLE")
print("="*70)
cursor.execute("""
SELECT character_id, actor_id, series, COUNT(*) as count
FROM Character_Actors
GROUP BY character_id, actor_id, series
HAVING COUNT(*) > 1
""")
ca_dupes = cursor.fetchall()
if ca_dupes:
    print(f"Found {len(ca_dupes)} duplicate character-actor-series combinations")
    total_extra = sum(count - 1 for _, _, _, count in ca_dupes)
    print(f"Total extra entries: {total_extra}")
    for char_id, actor_id, series, count in ca_dupes[:10]:
        cursor.execute("SELECT name FROM Characters WHERE character_id = ?", (char_id,))
        char_name = cursor.fetchone()[0] if cursor.fetchone() else "Unknown"
        print(f"  Character {char_id} + Actor {actor_id} in {series}: {count} copies")
    all_duplicates.append(('Character_Actors', len(ca_dupes), total_extra))
else:
    print("✓ No duplicates found")

# 8. Check Character_Episodes - should be unique by (character_id, episode_id)
print("\n" + "="*70)
print("CHARACTER_EPISODES TABLE")
print("="*70)
cursor.execute("""
SELECT character_id, episode_id, COUNT(*) as count
FROM Character_Episodes
GROUP BY character_id, episode_id
HAVING COUNT(*) > 1
""")
ce_dupes = cursor.fetchall()
if ce_dupes:
    print(f"Found {len(ce_dupes)} duplicate character-episode combinations")
    total_extra = sum(count - 1 for _, _, count in ce_dupes)
    print(f"Total extra entries: {total_extra}")
    print(f"  (showing first 10 only)")
    all_duplicates.append(('Character_Episodes', len(ce_dupes), total_extra))
else:
    print("✓ No duplicates found")

# 9. Check Character_Organizations - should be unique by (character_id, organization_id)
print("\n" + "="*70)
print("CHARACTER_ORGANIZATIONS TABLE")
print("="*70)
cursor.execute("""
SELECT character_id, organization_id, COUNT(*) as count
FROM Character_Organizations
GROUP BY character_id, organization_id
HAVING COUNT(*) > 1
""")
co_dupes = cursor.fetchall()
if co_dupes:
    print(f"Found {len(co_dupes)} duplicate character-organization combinations")
    total_extra = sum(count - 1 for _, _, count in co_dupes)
    print(f"Total extra entries: {total_extra}")
    all_duplicates.append(('Character_Organizations', len(co_dupes), total_extra))
else:
    print("✓ No duplicates found")

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)
if all_duplicates:
    print(f"\nFound duplicates in {len(all_duplicates)} table(s):")
    total_to_remove = 0
    for table, dup_count, extra_entries in all_duplicates:
        print(f"  {table}: {dup_count} duplicate combinations, {extra_entries} extra entries")
        total_to_remove += extra_entries
    print(f"\nTotal entries that need to be removed: {total_to_remove}")
else:
    print("\n✓ No duplicates found in any table!")

conn.close()
