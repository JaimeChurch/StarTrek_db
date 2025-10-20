"""
Star Trek Database Creation Script
This script creates the SQLite database and populates it with sample data
"""

import sqlite3
import os

def create_database(db_path='startrek.db'):
    """
    Create the Star Trek database and populate it with schema and sample data
    
    Args:
        db_path: Path to the database file (default: startrek.db)
    """
    # Remove existing database if it exists
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    # Create new database connection
    print(f"Creating new database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Read and execute schema
    print("Creating database schema...")
    with open('schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)
    
    # Read and execute sample data
    print("Inserting sample data...")
    with open('sample_data.sql', 'r', encoding='utf-8') as f:
        data_sql = f.read()
        cursor.executescript(data_sql)
    
    # Commit changes
    conn.commit()
    
    # Display statistics
    print("\nDatabase created successfully!")
    print("\nDatabase Statistics:")
    print("-" * 50)
    
    tables = [
        'Species', 'Origins', 'Organizations', 'Actors', 'Ships',
        'Characters', 'Series', 'Episodes', 'Character_Actors',
        'Character_Organizations', 'Character_Ships', 'Character_Episodes'
    ]
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table:30} {count:5} records")
    
    conn.close()
    print("\nDatabase connection closed.")

def test_queries(db_path='startrek.db'):
    """
    Run some test queries to verify the database
    
    Args:
        db_path: Path to the database file
    """
    print("\n" + "=" * 70)
    print("RUNNING TEST QUERIES")
    print("=" * 70)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Test Query 1: All characters with their species
    print("\n1. Characters and their species:")
    print("-" * 70)
    cursor.execute("""
        SELECT c.name, c.rank, s.name as species
        FROM Characters c
        LEFT JOIN Species s ON c.species_id = s.species_id
        ORDER BY c.name
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]:25} {row[1]:20} {row[2]}")
    
    # Test Query 2: Ships and their organizations
    print("\n2. Ships and their organizations:")
    print("-" * 70)
    cursor.execute("""
        SELECT s.name, s.registry, s.class, o.name as organization
        FROM Ships s
        LEFT JOIN Organizations o ON s.organization_id = o.organization_id
        ORDER BY s.name
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]:20} {row[1]:15} {row[2]:15} {row[3]}")
    
    # Test Query 3: Characters and their actors
    print("\n3. Characters and their actors:")
    print("-" * 70)
    cursor.execute("""
        SELECT c.name, a.first_name || ' ' || a.last_name as actor, ca.series
        FROM Characters c
        JOIN Character_Actors ca ON c.character_id = ca.character_id
        JOIN Actors a ON ca.actor_id = a.actor_id
        ORDER BY c.name
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]:25} {row[1]:25} {row[2]}")
    
    # Test Query 4: Characters who served on Enterprise-D
    print("\n4. Characters who served on USS Enterprise NCC-1701-D:")
    print("-" * 70)
    cursor.execute("""
        SELECT c.name, c.rank, cs.role
        FROM Characters c
        JOIN Character_Ships cs ON c.character_id = cs.character_id
        JOIN Ships s ON cs.ship_id = s.ship_id
        WHERE s.registry = 'NCC-1701-D'
        ORDER BY c.name
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]:25} {row[1]:20} {row[2]}")
    
    conn.close()

if __name__ == '__main__':
    # Create the database
    create_database()
    
    # Run test queries
    test_queries()
    
    print("\n" + "=" * 70)
    print("Setup complete! You can now use the database with any SQLite tool.")
    print("Database file: startrek.db")
    print("=" * 70)
