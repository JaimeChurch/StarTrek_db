"""
Remove duplicate episodes from the Episodes table
Keeps only one entry per series/season/episode_number combination
"""

import sqlite3

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("FINDING DUPLICATE EPISODES")
print("="*70)

# Find duplicates by series_id, season, episode_number
cursor.execute("""
SELECT series_id, season, episode_number, COUNT(*) as count
FROM Episodes
GROUP BY series_id, season, episode_number
HAVING COUNT(*) > 1
ORDER BY count DESC, series_id, season, episode_number
""")

duplicates = cursor.fetchall()

if not duplicates:
    print("\n✓ No duplicate episodes found!")
    conn.close()
    exit()

print(f"\nFound {len(duplicates)} duplicate episode combinations")
print(f"\nSample duplicates (first 10):")
for series_id, season, ep_num, count in duplicates[:10]:
    cursor.execute("SELECT name, abbreviation FROM Series WHERE series_id = ?", (series_id,))
    series = cursor.fetchone()
    print(f"  {series[1]} S{season}E{ep_num}: {count} copies")

# Count total entries to remove
cursor.execute("SELECT COUNT(*) FROM Episodes")
total_count = cursor.fetchone()[0]
cursor.execute("""
SELECT COUNT(*) FROM (
    SELECT series_id, season, episode_number
    FROM Episodes
    GROUP BY series_id, season, episode_number
)
""")
unique_count = cursor.fetchone()[0]
to_remove = total_count - unique_count

print(f"\nTotal duplicate entries to remove: {to_remove}")
print(f"This will keep the FIRST occurrence of each episode")

# Ask for confirmation
print("\n" + "="*70)
response = input("Remove duplicates? (yes/no): ").strip().lower()

if response == 'yes':
    print("\nRemoving duplicate episodes...")
    
    # Keep only the episode with the lowest episode_id for each unique combination
    cursor.execute("""
    DELETE FROM Episodes
    WHERE episode_id NOT IN (
        SELECT MIN(episode_id)
        FROM Episodes
        GROUP BY series_id, season, episode_number
    )
    """)
    
    deleted_count = cursor.rowcount
    conn.commit()
    
    print(f"✓ Deleted {deleted_count} duplicate episodes")
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM Episodes")
    total_after = cursor.fetchone()[0]
    print(f"✓ Total episodes remaining: {total_after}")
    
    # Show breakdown by series
    print("\nEpisodes per series after cleanup:")
    cursor.execute("""
    SELECT s.abbreviation, s.name, COUNT(e.episode_id)
    FROM Series s
    LEFT JOIN Episodes e ON s.series_id = e.series_id
    GROUP BY s.series_id
    ORDER BY s.abbreviation
    """)
    for abbr, name, count in cursor.fetchall():
        print(f"  {abbr}: {count} episodes")
    
    print("\n" + "="*70)
    print("CLEANUP COMPLETE!")
    print("="*70)
else:
    print("\nCancelled. No changes made.")

conn.close()
