"""
Check which episodes don't have IMDB IDs
"""
import sqlite3

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

# Get total episodes per series
cursor.execute("""
    SELECT s.abbreviation, s.name,
           COUNT(*) as total_episodes,
           SUM(CASE WHEN e.imdb_id IS NOT NULL THEN 1 ELSE 0 END) as with_imdb_id,
           SUM(CASE WHEN e.imdb_id IS NULL THEN 1 ELSE 0 END) as without_imdb_id
    FROM Series s
    JOIN Episodes e ON s.series_id = e.series_id
    GROUP BY s.series_id, s.abbreviation, s.name
    ORDER BY s.series_id
""")

print("Episodes IMDB ID Status by Series:")
print("="*70)
for row in cursor.fetchall():
    abbr, name, total, with_id, without_id = row
    print(f"\n{abbr} - {name}")
    print(f"  Total episodes: {total}")
    print(f"  With IMDB ID:   {with_id} ({with_id/total*100:.1f}%)")
    print(f"  Without ID:     {without_id} ({without_id/total*100:.1f}%)")

# Show some examples of episodes without IMDB IDs
print("\n" + "="*70)
print("Sample episodes without IMDB IDs:")
print("="*70)

cursor.execute("""
    SELECT s.abbreviation, e.season, e.episode_number, e.title
    FROM Episodes e
    JOIN Series s ON e.series_id = s.series_id
    WHERE e.imdb_id IS NULL
    ORDER BY s.abbreviation, e.season, e.episode_number
    LIMIT 20
""")

for row in cursor.fetchall():
    abbr, season, ep_num, title = row
    print(f"{abbr} S{season:02d}E{ep_num:02d}: {title}")

conn.close()
