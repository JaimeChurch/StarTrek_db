import sqlite3

conn = sqlite3.connect('startrek.db')
cursor = conn.cursor()

print("="*70)
print("REMOVING DUPLICATE ENTRIES FROM CHARACTER_ACTORS TABLE")
print("="*70)

# First, let's count the current duplicates
cursor.execute("""
SELECT COUNT(*) as total_entries
FROM Character_Actors
""")
total_before = cursor.fetchone()[0]
print(f"\nTotal Character_Actors entries before cleanup: {total_before}")

# Count unique combinations
cursor.execute("""
SELECT COUNT(*)
FROM (
    SELECT DISTINCT character_id, actor_id
    FROM Character_Actors
) as unique_combos
""")
unique_combos = cursor.fetchone()[0]
print(f"Unique character-actor combinations: {unique_combos}")
print(f"Duplicate entries to remove: {total_before - unique_combos}")

# Find all duplicates
cursor.execute("""
SELECT character_id, actor_id, COUNT(*) as count
FROM Character_Actors
GROUP BY character_id, actor_id
HAVING COUNT(*) > 1
""")
duplicates = cursor.fetchall()
print(f"\nNumber of character-actor pairs with duplicates: {len(duplicates)}")

# Show a sample of duplicates
if duplicates:
    print("\nSample duplicates (first 5):")
    for char_id, actor_id, count in duplicates[:5]:
        cursor.execute("SELECT name FROM Characters WHERE character_id = ?", (char_id,))
        char_name = cursor.fetchone()[0]
        cursor.execute("SELECT first_name, last_name FROM Actors WHERE actor_id = ?", (actor_id,))
        actor = cursor.fetchone()
        print(f"  {char_name} - {actor[0]} {actor[1]}: {count} entries")

# Ask for confirmation
print("\n" + "="*70)
response = input("Do you want to remove the duplicate entries? (yes/no): ").strip().lower()

if response == 'yes':
    print("\nRemoving duplicates...")
    
    # Strategy: Keep the entry with the lowest character_actor_id for each unique combination
    # Delete all other entries
    cursor.execute("""
    DELETE FROM Character_Actors
    WHERE character_actor_id NOT IN (
        SELECT MIN(character_actor_id)
        FROM Character_Actors
        GROUP BY character_id, actor_id
    )
    """)
    
    deleted_count = cursor.rowcount
    conn.commit()
    
    print(f"✓ Deleted {deleted_count} duplicate entries")
    
    # Verify the cleanup
    cursor.execute("SELECT COUNT(*) FROM Character_Actors")
    total_after = cursor.fetchone()[0]
    print(f"✓ Total entries after cleanup: {total_after}")
    
    # Verify no duplicates remain
    cursor.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT character_id, actor_id, COUNT(*) as count
        FROM Character_Actors
        GROUP BY character_id, actor_id
        HAVING COUNT(*) > 1
    )
    """)
    remaining_dupes = cursor.fetchone()[0]
    
    if remaining_dupes == 0:
        print("✓ All duplicates successfully removed!")
    else:
        print(f"⚠ Warning: {remaining_dupes} duplicate pairs still exist")
    
    print("\n" + "="*70)
    print("CLEANUP COMPLETE!")
    print("="*70)
else:
    print("\nCleanup cancelled. No changes made to the database.")

conn.close()
