import sqlite3

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("Searching for major characters...")
cursor.execute("""
    SELECT name, rank, gender, species_id 
    FROM Characters 
    WHERE name LIKE '%Kirk%' 
       OR name LIKE '%Spock%' 
       OR name LIKE '%Picard%' 
       OR name LIKE '%Data%'
       OR name LIKE '%Janeway%'
       OR name LIKE '%Sisko%'
    ORDER BY name
""")

results = cursor.fetchall()
print(f"\nFound {len(results)} major characters:")
for r in results:
    print(f"  {r[0]:30} {r[1] if r[1] else 'None':20} {r[2] if r[2] else 'None'}")

print(f"\n\nTotal characters in database:")
cursor.execute("SELECT COUNT(*) FROM Characters")
print(f"  {cursor.fetchone()[0]} characters")

print(f"\nSample of all characters (first 20):")
cursor.execute("SELECT name, gender FROM Characters ORDER BY name LIMIT 20")
for r in cursor.fetchall():
    print(f"  {r[0]:40} {r[1] if r[1] else 'None'}")

conn.close()
