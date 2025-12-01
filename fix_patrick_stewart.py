"""
Fix Patrick Stewart's name - move "Sir" from first_name to a separate title
"""

import sqlite3

def fix_patrick_stewart():
    conn = sqlite3.connect('startrek.db')
    cursor = conn.cursor()
    
    # Find Patrick Stewart (first_name = "Sir", last_name = "Patrick Stewart")
    cursor.execute("""
        SELECT actor_id, first_name, last_name 
        FROM Actors 
        WHERE LOWER(first_name) = 'sir'
        AND LOWER(last_name) LIKE '%patrick%stewart%'
    """)
    
    results = cursor.fetchall()
    print(f"Found {len(results)} matching actors:")
    for actor_id, first_name, last_name in results:
        print(f"  Actor ID {actor_id}: {first_name} {last_name}")
    
    if not results:
        print("\nPatrick Stewart not found in database")
        conn.close()
        return
    
    # Update the first one found
    actor_id = results[0][0]
    
    # Update first_name to "Patrick" and last_name to "Stewart"
    cursor.execute("""
        UPDATE Actors 
        SET first_name = 'Patrick',
            last_name = 'Stewart'
        WHERE actor_id = ?
    """, (actor_id,))
    
    conn.commit()
    print(f"\n✓ Updated actor {actor_id}: Changed to 'Patrick' 'Stewart'")
    print("  (Removed 'Sir' from first_name field)")
    
    # Verify the change
    cursor.execute("""
        SELECT actor_id, first_name, last_name 
        FROM Actors 
        WHERE actor_id = ?
    """, (actor_id,))
    
    result = cursor.fetchone()
    print(f"\nVerified: Actor {result[0]} is now '{result[1]} {result[2]}'")
    
    conn.close()

if __name__ == "__main__":
    fix_patrick_stewart()
