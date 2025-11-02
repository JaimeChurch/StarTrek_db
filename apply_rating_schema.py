"""
Apply schema changes to add IMDB rating columns to Episodes table
"""

import sqlite3

def apply_rating_schema():
    conn = sqlite3.connect('startrek.db')
    cursor = conn.cursor()
    
    print("Adding IMDB rating columns to Episodes table...")
    
    try:
        # Add the columns directly
        cursor.execute("ALTER TABLE Episodes ADD COLUMN imdb_rating DECIMAL(3,1)")
        cursor.execute("ALTER TABLE Episodes ADD COLUMN imdb_votes INTEGER")
        cursor.execute("ALTER TABLE Episodes ADD COLUMN imdb_id VARCHAR(20)")
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_episodes_imdb_id ON Episodes(imdb_id)")
        cursor.execute("CREATE INDEX idx_episodes_rating ON Episodes(imdb_rating)")
        
        conn.commit()
        
        print("✓ Successfully added columns:")
        print("  - imdb_rating (DECIMAL)")
        print("  - imdb_votes (INTEGER)")
        print("  - imdb_id (VARCHAR)")
        print("✓ Created indexes for better query performance")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    apply_rating_schema()
