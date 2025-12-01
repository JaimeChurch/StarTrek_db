import sqlite3
import time

# Try to connect with timeout
conn = sqlite3.connect('startrek.db', timeout=10)
cursor = conn.cursor()

# Find Spock
cursor.execute("""
    SELECT c.character_id, c.name, c.primary_actor_id, 
           a.first_name || ' ' || a.last_name as current_primary
    FROM Characters c
    LEFT JOIN Actors a ON c.primary_actor_id = a.actor_id
    WHERE c.name LIKE '%Spock%'
""")

print("Current Spock entries:")
spock_chars = cursor.fetchall()
for char in spock_chars:
    print(f"  {char[0]}: {char[1]} -> Primary: {char[3]} (ID: {char[2]})")

# Find Nimoy
cursor.execute("""
    SELECT actor_id, first_name || ' ' || last_name as name
    FROM Actors
    WHERE last_name LIKE '%Nimoy%'
""")

print("\nNimoy in database:")
nimoys = cursor.fetchall()
for actor in nimoys:
    print(f"  {actor[0]}: {actor[1]}")

if nimoys:
    nimoy_id = nimoys[0][0]
    
    # Update Spock's primary actor to Nimoy
    cursor.execute("""
        UPDATE Characters
        SET primary_actor_id = ?
        WHERE name = 'Spock'
    """, (nimoy_id,))
    
    conn.commit()
    print(f"\n✓ Updated Spock's primary actor to Leonard Nimoy (ID: {nimoy_id})")
else:
    print("\nLeonard Nimoy not found in database!")

conn.close()
