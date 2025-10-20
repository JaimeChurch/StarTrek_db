# Star Trek Database Design

## Overview
This SQLite database is designed to store comprehensive Star Trek universe data from Memory Alpha, including characters, species, actors, ships, organizations, and their various relationships.

## Database Schema

### Core Tables

#### 1. **Species**
Stores information about different species in the Star Trek universe.
- `species_id` (PK): Unique identifier
- `name`: Species name (e.g., Human, Vulcan, Klingon)
- `homeworld`: Name of the species' home planet
- `classification`: Type of species (humanoid, non-humanoid, etc.)
- `description`: Detailed information about the species
- `warp_capable`: Whether the species has warp technology
- `created_at`: Timestamp when record was created
- `updated_at`: Timestamp when record was last updated

#### 2. **Organizations**
Stores various organizations, governments, and groups.
- `organization_id` (PK): Unique identifier
- `name`: Organization name (e.g., Starfleet, Klingon Empire)
- `type`: Organization type (military, government, religious, criminal)
- `founded_year`: Year of establishment
- `affiliation`: Parent organization or alliance
- `description`: Additional details
- `created_at`: Timestamp when record was created
- `updated_at`: Timestamp when record was last updated

#### 3. **Actors**
Stores real-world actors who portray characters.
- `actor_id` (PK): Unique identifier
- `first_name`, `last_name`: Actor's name
- `birth_date`: Date of birth
- `nationality`: Actor's nationality
- `bio`: Biography information
- `created_at`: Timestamp when record was created
- `updated_at`: Timestamp when record was last updated

#### 4. **Ships**
Stores starships and other vessels.
- `ship_id` (PK): Unique identifier
- `name`: Ship name (e.g., USS Enterprise)
- `registry`: Ship registration number (e.g., NCC-1701)
- `class`: Ship class (Constitution, Galaxy, Intrepid, etc.)
- `type`: Ship type (Starship, Shuttle, Warship)
- `launched_year`: Year commissioned
- `status`: Current status (active, destroyed, decommissioned)
- `organization_id` (FK): Owning organization
- `description`: Additional ship details
- `created_at`: Timestamp when record was created
- `updated_at`: Timestamp when record was last updated

#### 5. **Characters**
Stores fictional characters from Star Trek.
- `character_id` (PK): Unique identifier
- `name`: Character name (e.g., James T. Kirk, Jean-Luc Picard)
- `rank`: Military or organizational rank
- `title`: Position or role
- `species_id` (FK): Character's species
- `birth_year`, `death_year`: Lifespan
- `gender`: Character's gender
- `occupation`: Primary occupation
- `bio`: Character biography
- `created_at`: Timestamp when record was created
- `updated_at`: Timestamp when record was last updated

#### 6. **Series**
Stores information about different Star Trek TV series.
- `series_id` (PK): Unique identifier
- `name`: Full series name
- `abbreviation`: Common abbreviation (TOS, TNG, DS9, VOY, ENT, DIS, PIC, SNW, LD, PRO)
- `start_year`, `end_year`: Years the series aired
- `num_seasons`, `num_episodes`: Episode counts
- `description`: Additional series information
- `created_at`: Timestamp when record was created
- `updated_at`: Timestamp when record was last updated

#### 7. **Episodes**
Stores individual episode information.
- `episode_id` (PK): Unique identifier
- `series_id` (FK): Parent series
- `title`: Episode title
- `season`, `episode_number`: Episode numbering
- `air_date`: Original air date
- `description`: Episode synopsis
- `created_at`: Timestamp when record was created
- `updated_at`: Timestamp when record was last updated

### Junction Tables (Many-to-Many Relationships)

#### 8. **Character_Actors**
Links characters to the actors who portrayed them.
- `character_actor_id` (PK): Unique identifier
- `character_id` (FK): Reference to Characters table
- `actor_id` (FK): Reference to Actors table
- `series`: Which series the actor portrayed the character in (e.g., TOS, TNG, DS9)
- `first_appearance`: First episode or movie appearance
- `last_appearance`: Last episode or movie appearance
- `episodes_count`: Number of episodes the actor appeared as this character
- `notes`: Additional information about the portrayal
- `created_at`: Timestamp when record was created
- Unique constraint on (character_id, actor_id, series)

#### 9. **Character_Organizations**
Links characters to organizations they belong to.
- `char_org_id` (PK): Unique identifier
- `character_id` (FK): Reference to Characters table
- `organization_id` (FK): Reference to Organizations table
- `role`: Character's role in the organization (e.g., member, leader, founder)
- `start_year`: When the character joined
- `end_year`: When the character left (NULL if still a member)
- `notes`: Additional information
- `created_at`: Timestamp when record was created

#### 10. **Character_Ships**
Links characters to ships they served on.
- `char_ship_id` (PK): Unique identifier
- `character_id` (FK): Reference to Characters table
- `ship_id` (FK): Reference to Ships table
- `role`: Character's role on the ship (e.g., Captain, First Officer, Chief Engineer)
- `start_year`: When service began
- `end_year`: When service ended (NULL if still serving)
- `notes`: Additional information
- `created_at`: Timestamp when record was created

#### 11. **Character_Episodes**
Tracks which characters appear in which episodes.
- `char_episode_id` (PK): Unique identifier
- `character_id` (FK): Reference to Characters table
- `episode_id` (FK): Reference to Episodes table
- `role_type`: Type of appearance (main, recurring, guest)
- `created_at`: Timestamp when record was created
- Unique constraint on (character_id, episode_id)

## Entity Relationships

```
Species (1) ─────< (M) Characters
Organizations (1) ─────< (M) Ships
Organizations (M) ─────< (M) Characters (via Character_Organizations)
Ships (M) ─────< (M) Characters (via Character_Ships)
Actors (M) ─────< (M) Characters (via Character_Actors)
Series (1) ─────< (M) Episodes
Characters (M) ─────< (M) Episodes (via Character_Episodes)
```

## Key Features

### 1. **Comprehensive Character Tracking**
- Full biographical information
- Multiple affiliations and assignments
- Episode appearances
- Actor portrayals across different series

### 2. **Organizational Hierarchy**
- Organizations can own ships
- Characters can belong to multiple organizations
- Historical tracking with start/end dates

### 3. **Temporal Tracking**
- Birth/death years for characters
- Ship launch dates and status
- Organization founding dates
- Service periods on ships

### 4. **Performance Optimization**
- Indexes on foreign keys
- Indexes on frequently searched fields (names)
- Efficient many-to-many relationships

## Sample Queries

### Find all characters from a specific species
```sql
SELECT c.name, c.rank, c.title
FROM Characters c
JOIN Species s ON c.species_id = s.species_id
WHERE s.name = 'Vulcan';
```

### Find all actors who played a character
```sql
SELECT a.first_name, a.last_name, ca.series, ca.episodes_count
FROM Actors a
JOIN Character_Actors ca ON a.actor_id = ca.actor_id
JOIN Characters c ON ca.character_id = c.character_id
WHERE c.name = 'James T. Kirk';
```

### Find all characters who served on a specific ship
```sql
SELECT c.name, cs.role, c.rank
FROM Characters c
JOIN Character_Ships cs ON c.character_id = cs.character_id
JOIN Ships s ON cs.ship_id = s.ship_id
WHERE s.name = 'USS Enterprise' AND s.registry = 'NCC-1701-D';
```

### Find all ships belonging to an organization
```sql
SELECT s.name, s.registry, s.class, s.status
FROM Ships s
JOIN Organizations o ON s.organization_id = o.organization_id
WHERE o.name = 'Starfleet';
```

## Data Population Strategy

1. **Start with reference data**: Species, Organizations, Series
2. **Add Ships**: Link to organizations
3. **Add Actors**: Real-world people
4. **Add Characters**: Link to species
5. **Create relationships**: Link characters to actors, organizations, ships
6. **Add Episodes**: Link to series
7. **Track appearances**: Link characters to episodes

## Future Enhancements

- Add movies and films table
- Add character relationships (family, friends, enemies)
- Add technology/weapons table
- Add events/battles table
- Add timeline/era classification
- Add images/media references
