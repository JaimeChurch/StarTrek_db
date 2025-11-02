# Star Trek Database - Entity Relationship Diagram

```mermaid
erDiagram
    Species ||--o{ Characters : belongs_to
    Organizations ||--o{ Ships : operates
    Organizations ||--o{ Character_Organizations : has_members
    
    Characters ||--o{ Character_Actors : portrayed_by
    Characters ||--o{ Character_Organizations : member_of
    Characters ||--o{ Character_Episodes : appears_in
    
    Actors ||--o{ Character_Actors : portrays
    
    Series ||--o{ Episodes : contains
    
    Episodes ||--o{ Character_Episodes : features
    
    Species {
        int species_id
        string name
        string homeworld
        string classification
    }
    
    Organizations {
        int organization_id
        string name
        string type
        int founded_year
    }
    
    Actors {
        int actor_id
        string first_name
        string last_name
        date birth_date
    }
    
    Ships {
        int ship_id
        string name
        string registry
        string class
        int organization_id
    }
    
    Characters {
        int character_id
        string name
        string rank
        string title
        int species_id
    }
    
    Character_Actors {
        int character_actor_id
        int character_id
        int actor_id
        string series
    }
    
    Character_Organizations {
        int char_org_id
        int character_id
        int organization_id
        string role
    }
    
    Series {
        int series_id
        string name
        string abbreviation
        int start_year
        int end_year
    }
    
    Episodes {
        int episode_id
        int series_id
        string title
        int season
        int episode_number
    }
    
    Character_Episodes {
        int char_episode_id
        int character_id
        int episode_id
        string role_type
    }
```

## Relationship Summary

### One-to-Many Relationships
- **Species → Characters**: One species has many characters
- **Organizations → Ships**: One organization operates many ships
- **Series → Episodes**: One series contains many episodes

### Many-to-Many Relationships
- **Characters ↔ Actors**: Characters portrayed by multiple actors; actors play multiple characters
- **Characters ↔ Organizations**: Characters belong to multiple organizations; organizations have multiple members
- **Characters ↔ Episodes**: Characters appear in multiple episodes; episodes feature multiple characters

### Key Insights
- Junction tables: `Character_Actors`, `Character_Organizations`, `Character_Episodes`
- All tables include timestamp tracking (`created_at`, `updated_at`)
- Foreign keys maintain referential integrity
- Unique constraints prevent duplicates in junction tables
