import sqlite3

# Connect to the database
conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("ACTOR WHO HAS PLAYED THE MOST CHARACTERS IN STAR TREK")
print("="*70)

# Query to find the actor who has played the most characters
query = """
SELECT 
    a.actor_id,
    a.first_name,
    a.last_name,
    COUNT(DISTINCT ca.character_id) as character_count,
    GROUP_CONCAT(c.name, ', ') as characters
FROM Actors a
JOIN Character_Actors ca ON a.actor_id = ca.actor_id
JOIN Characters c ON ca.character_id = c.character_id
GROUP BY a.actor_id, a.first_name, a.last_name
ORDER BY character_count DESC
LIMIT 10
"""

cursor.execute(query)
results = cursor.fetchall()

if results:
    print(f"\nTop 10 Actors by Number of Characters Played:\n")
    print(f"{'Rank':<6} {'Actor Name':<30} {'Characters':<10} {'Character Names'}")
    print("-" * 70)
    
    for idx, row in enumerate(results, 1):
        actor_id, first_name, last_name, char_count, characters = row
        actor_name = f"{first_name} {last_name}"
        
        # Truncate character list if too long
        if len(characters) > 50:
            char_display = characters[:47] + "..."
        else:
            char_display = characters
        
        print(f"{idx:<6} {actor_name:<30} {char_count:<10} {char_display}")
    
    # Show summary for the top actor
    top_actor = results[0]
    print("\n" + "="*70)
    print(f"TOP ACTOR: {top_actor[1]} {top_actor[2]}")
    print("="*70)
    print(f"Total Characters Played: {top_actor[3]}")
    print(f"\nAll Characters: {top_actor[4]}")
else:
    print("No data found in the database.")

conn.close()
