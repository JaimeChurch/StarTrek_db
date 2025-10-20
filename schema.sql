-- Star Trek Database Schema
-- Based on Memory Alpha data structure

-- Species table: stores information about different species in Star Trek
CREATE TABLE Species (
    species_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    homeworld VARCHAR(100),
    classification VARCHAR(50), -- e.g., humanoid, non-humanoid
    description TEXT,
    warp_capable BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Origins table: stores planets, star systems, or locations
CREATE TABLE Origins (
    origin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50), -- e.g., planet, moon, space station, star system
    quadrant VARCHAR(50), -- Alpha, Beta, Gamma, Delta
    sector VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Organizations table: stores Starfleet, Klingon Empire, etc.
CREATE TABLE Organizations (
    organization_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50), -- e.g., military, government, religious, criminal
    founded_year INTEGER,
    affiliation VARCHAR(100), -- e.g., United Federation of Planets
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Actors table: stores real-world actors
CREATE TABLE Actors (
    actor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    birth_date DATE,
    nationality VARCHAR(50),
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ships table: stores starships and vessels
CREATE TABLE Ships (
    ship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    registry VARCHAR(50), -- e.g., NCC-1701
    class VARCHAR(50), -- e.g., Constitution, Galaxy, Intrepid
    type VARCHAR(50), -- e.g., Starship, Shuttle, Warship
    launched_year INTEGER,
    status VARCHAR(50), -- active, destroyed, decommissioned
    organization_id INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES Organizations(organization_id)
);

-- Characters table: stores fictional characters from Star Trek
CREATE TABLE Characters (
    character_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    rank VARCHAR(50), -- e.g., Captain, Commander, Ensign
    title VARCHAR(100), -- e.g., Chief Engineer, Chief Medical Officer
    species_id INTEGER,
    origin_id INTEGER,
    birth_year INTEGER,
    death_year INTEGER,
    gender VARCHAR(20),
    occupation VARCHAR(100),
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (species_id) REFERENCES Species(species_id),
    FOREIGN KEY (origin_id) REFERENCES Origins(origin_id)
);

-- Character_Actors junction table: links characters to actors (many-to-many)
CREATE TABLE Character_Actors (
    character_actor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    actor_id INTEGER NOT NULL,
    series VARCHAR(100), -- e.g., TOS, TNG, DS9, VOY, ENT, DIS, PIC
    first_appearance VARCHAR(100),
    last_appearance VARCHAR(100),
    episodes_count INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES Characters(character_id),
    FOREIGN KEY (actor_id) REFERENCES Actors(actor_id),
    UNIQUE(character_id, actor_id, series)
);

-- Character_Organizations junction table: links characters to organizations (many-to-many)
CREATE TABLE Character_Organizations (
    char_org_id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    role VARCHAR(100), -- e.g., member, leader, founder
    start_year INTEGER,
    end_year INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES Characters(character_id),
    FOREIGN KEY (organization_id) REFERENCES Organizations(organization_id)
);

-- Character_Ships junction table: links characters to ships they served on (many-to-many)
CREATE TABLE Character_Ships (
    char_ship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    ship_id INTEGER NOT NULL,
    role VARCHAR(100), -- e.g., Captain, First Officer, Chief Engineer
    start_year INTEGER,
    end_year INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES Characters(character_id),
    FOREIGN KEY (ship_id) REFERENCES Ships(ship_id)
);

-- Series table: stores information about different Star Trek series
CREATE TABLE Series (
    series_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    abbreviation VARCHAR(10), -- TOS, TNG, DS9, VOY, ENT, DIS, PIC, SNW, LD, PRO
    start_year INTEGER,
    end_year INTEGER,
    num_seasons INTEGER,
    num_episodes INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Episodes table: stores individual episodes
CREATE TABLE Episodes (
    episode_id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    season INTEGER,
    episode_number INTEGER,
    air_date DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (series_id) REFERENCES Series(series_id)
);

-- Character_Episodes junction table: tracks character appearances in episodes
CREATE TABLE Character_Episodes (
    char_episode_id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    episode_id INTEGER NOT NULL,
    role_type VARCHAR(50), -- main, recurring, guest
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (character_id) REFERENCES Characters(character_id),
    FOREIGN KEY (episode_id) REFERENCES Episodes(episode_id),
    UNIQUE(character_id, episode_id)
);

-- Create indexes for better query performance
CREATE INDEX idx_characters_species ON Characters(species_id);
CREATE INDEX idx_characters_origin ON Characters(origin_id);
CREATE INDEX idx_characters_name ON Characters(name);
CREATE INDEX idx_ships_organization ON Ships(organization_id);
CREATE INDEX idx_character_actors_character ON Character_Actors(character_id);
CREATE INDEX idx_character_actors_actor ON Character_Actors(actor_id);
CREATE INDEX idx_character_organizations_character ON Character_Organizations(character_id);
CREATE INDEX idx_character_organizations_org ON Character_Organizations(organization_id);
CREATE INDEX idx_character_ships_character ON Character_Ships(character_id);
CREATE INDEX idx_character_ships_ship ON Character_Ships(ship_id);
CREATE INDEX idx_episodes_series ON Episodes(series_id);
CREATE INDEX idx_character_episodes_character ON Character_Episodes(character_id);
CREATE INDEX idx_character_episodes_episode ON Character_Episodes(episode_id);
