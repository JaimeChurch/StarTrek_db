10/02:

  Created python script main.py that runs DistilGPT2 locally to write a poem about a sunset. The script imports AutoTokenizer 
    and PyTorch then downloads DistilGPT2. This is an example of a poem GPT2 generated (about a sunset?):  
    
      "This time, you‽re the one! This song is about the way I was in college.
      So I read in my mother‼ and realized that I wanted a lot of something to be. 
      I‿m about to go to the bar and write some poetry. That‴s so, I don’t have to do it every day. 
      Because if you didn‚t do anything, that‵t will be all I can do. 
      Maybe I should have done a few poems more than I did, but I think I could have made some more. 
      Here is a beautiful poem: To a boy you cannot sing because he is not a man. You cannot be too old to sing"
  
  Created db.py that creates uses SQLite to create a database with a single table of characters. The table
    contains an ID, the character's name, actor name, and species. The script also includes seed values to
    populate the table on creation. I don't intend for this to be the final db, just using it now 
    for learning.   
    
  Created fetch_lower_decks.py that clears the seed data from the table (this will need to be changed)
    and retrieves all character and actor names from the Lower Deck's wiki page (https://memory-alpha.fandom.com/wiki/Star_Trek:_Lower_Decks#Starring)
    and inserts them into the characters table. Species must be retrieved separately. 

  Created the fetch_species.py script that fetches characters' species from the Memory Alpha wiki and inserts it
    into the character table. The script works by reading the character's name from the table, and cleaning it by removing
    any titles or rank, then plugging adding it to the url "https://memory-alpha.fandom.com/wiki/" to find the character's
    wiki page. The script then uses the BeautifulSoup html parser to find the string "Species" and add the species to the table.

  Created show_characters.py script that prints the contents of the characters table. Used for testing.

  Created find_common_species.py that SELECTs all the species from the character table and counts them. The script then
    finds the percentage of each species and prints them in order. 
    
10/16:

    I decided to update my database schema now that I have some understanding of what I'm doing. I created a new GitHub repository for the project 
    since I was essentially starting from scratch. The new database contains 11 tables, 7 main tables and 4 junction tables. I also switched from 
    scraping the Memory Alpha wiki to the using Star Trek API for more a more consistent data structure. 

    The tables in the database are as follows:
        1. Species
            Key Fields: 
                species_id - (PK)
                name - Species name (UNIQUE)
                homeworld - Home planet name
                classification - Type (humanoid, non-humanoid, artificial)
                warp_capable - Boolean for warp drive capability
            Relationships:
                One species → Many characters

        2. Organizations 
            Key Fields: 
                organization_id - (PK)
                name - (UNIQUE)
                type - Category (military, government, religious, criminal)
                founded_year 
                affiliation -  (e.g., "United Federation of Planets")
            Relationships:
                One organization → Many ships (via organization_id FK)
                Many organizations ↔ Many characters (via Character_Organizations junction)

        3. Actors
            Key Fields:
                actor_id (PK)
                first_name, last_name
                birth_date
                bio
            Relationships:
                Many actors ↔ Many characters (via Character_Actors junction)

        4. Ships
            Key Fields:
                ship_id (PK)
                name
                registry - Registration number (e.g., NCC-1701)
                class - Ship class (Constitution, Galaxy, Intrepid)
                type - Category (Starship, Shuttle, Warship)
                status - Current state (active, destroyed, decommissioned)
                organization_id (FK) - Owner organization
            Relationships:
                Many ships → One organization (Foreign Key)
                Many ships ↔ Many characters (via Character_Ships junction)

        5. Characters
            Key Fields:
               character_id (PK)
               name
               rank
               title
               species_id (FK) - Links to Species table
               birth_year, death_year
               gender
               occupation
               bio
            Relationships:
                Many characters → One species (Foreign Key)
                Many characters ↔ Many actors (via Character_Actors)
                Many characters ↔ Many organizations (via Character_Organizations)
                Many characters ↔ Many ships (via Character_Ships)
                Many characters ↔ Many episodes (via Character_Episodes)

        6. Series
            Key Fields:
                series_id (PK)
                name - (UNIQUE)
                abbreviation
                start_year, end_year 
                num_seasons, num_episodes
            Relationships
                One series → Many episodes (One-to-Many)

        7. Episodes
            Key Fields:
                episode_id (PK)
                series_id (FK) 
                title 
                season, episode_number 
                air_date 
                description - Synopsis
            Relationships:
                Many episodes → One series (Foreign Key)
                Many episodes ↔ Many characters (via Character_Episodes)

        8. Character_Actors
            Purpose: 
                Characters can have multiple actors, actors can play multiple characters
            Key Fields:
                character_actor_id (PK)
                character_id (FK)
                actor_id (FK)
                series - (e.g., "TOS" vs "Kelvin Timeline")
                first_appearance, last_appearance 
                episodes_count
                notes          
            Unique Constraint: 
                (character_id, actor_id, series)

        9. Character_Organizations
            Purpose: 
                Characters belong to multiple organizations, organizations have many members    
            Key Fields:
                char_org_id (PK)
                character_id (FK)
                organization_id (FK)
                role 
                start_year, end_year   

        10. Character_Ships
            Purpose: 
                Crew members serve on multiple ships, ships have multiple crew         
            Key Fields:
                char_ship_id (PK)
                character_id (FK)
                ship_id (FK)
                role 
                start_year, end_year

        11. Character_Episodes
            Purpose: 
                Episodes feature multiple characters, characters appear in many episodes  
            Key Fields:
                char_episode_id (PK)
                character_id (FK)
                episode_id (FK)
                role_type - (main, recurring, guest)
            Unique Constraint: 
                (character_id, episode_id)

    DB Relationship Diagram 

            ┌──────────┐
            │ Species  │────┐
            └──────────┘    │
                            │
                            ▼
                     ┌─────────────┐
                     │ Characters  │
                     └─────────────┘
                            │ │ │ │
                ┌───────────┘ │ │ └───────────┐
                │             │ │             │
                ▼             ▼ ▼             ▼
            ┌────────┐   ┌──────────┐   ┌──────────┐
            │ Actors │   │  Ships   │   │ Episodes │
            └────────┘   └──────────┘   └──────────┘
                             │              │
                             ▼              ▼
                      ┌──────────────┐ ┌────────┐
                      │ Organizations│ │ Series │
                      └──────────────┘ └────────┘

11/02:
    I spent the last week cleaning up the database and filling in 
    missing information. There were a lot of columns that did not 
    properly populate. I think this came from switching from web 
    scraping Memory Alpha to querying STAPI. Several columns were 
    meant to contain data that was not provided by STAPI, and 
    those columns have been removed, and the schema updated. 
    The db is now fully populated. 

    I added imdb ratings and number of ratings to the episode 
    table by scraping the imdb website. 
    
    I also modified the db to handle characters that appear in 
    multiple series as separate rows. Previously, the populate 
    script was overwriting any characters that appeared in 
    multiple series, so only the last series was saved. 

    Columns removed:
        Species: 
            classification
            description
        Organizations:
            founded_year
            affiliation
            description
        Actors:
            nationality --> changed to birth_place
        Ships:
            description
        Character_Organization:
            role
            start_year
            end_year
        Episodes:
            description
            (added) imdb_rating
            (added) imdb_votes

11/16
    I spent the last module working on a neural net that will analyze the 
    characters, actors, species, planets, directors, and writers for each
    episode based on the episode rating. The number of votes for each 
    episode will be used for weighting. In order to do that I had to scrape
    the episode descriptions, writers, and directors from IMDB. Since IMDB
    doesn't have an API the formatting is sometimes inconsistent, and 
    scraping was a bit of a pain. Some episodes still need cells filled in.
    I used Claude to develop the neural net, and initially the script was
    using an algorithm to calculate the popularity, which worked, but I 
    wanted to see how that compared to calculations done by the neural net, 
    so I started a new script, but I haven't gotten the second neural net 
    working the way I want yet. My plan going forward is to get the rest 
    of the episodes table populated, then finish the new neural net and 
    see how the calculations compare to the first. I also plan to clean
    up my repository and sort everything into folders for easier 
    navigation. 

11/30
    I spent the last module getting the v2 of the Star Trek neural net. 
    Here is a summary of the new neural net. 

        Purpose: Neural network predicts episode quality, drives all analysis

        Neural Network Role: CENTRAL - Trains on 3,073 features:
            7 basic features (chars, season, episode, date, series)
            21 species one-hot encodings (from descriptions)
            13 planet one-hot encodings (from descriptions)
            3,032 character one-hot encodings

        Key Features:
            One-Hot Encoding: Creates binary features for every character, species, 
            and planet
            Character-Centric: Each of 3,032 characters gets its own feature column
            NN Predicts Quality: Model learns which character combinations = good episodes
            Ratings Source: NN PREDICTIONS (scaled 0-1, then × 10 for display)

        Philosophy Difference:
            V1: Trust the data (IMDB ratings), use NN to find patterns in descriptions
            V2: Trust the NN to learn what makes episodes good based on cast/characters

    Overall the V2 uses the 3073 features to predict episode quality. The episode quality 
    for character, actor, and species is used to determine the popularity score for that 
    entity. I was interested to see how the results would differ from the v1 script, which
    calculates popularity based on the IMBDB ratings. 

    The original v1 neural nets top 20 actors:
        1. Michael Dorn: Worf
        2. Kate Mulgrew: Kathryn Janeway
        3. Patrick Stewart: Jean-Luc Picard
        4. Marina Sirtis: Deanna Troi
        5. Brent Spiner: Data
        6. Jonathan Frakes: William T. Riker
        7. Colm Meaney: Miles O'Brien
        8. LeVar Burton: Geordi La Forge
        9. Gates McFadden: Beverly Crusher
        10. Angus Imrie: Zero
        11. Dee Bradley Baker: Murf
        12. Jason Mantzoukas: Jankom Pog
        13. Rylee Alazraqui: Rok-Tahk
        14. Ella Purnell: Gwyndala
        15. Brett Gray: Dal R'El
        16. John Noble: The Diviner
        17. Leonard Nemoy: Spock
        18. Jimmi Simpson: Drednok
        19. William Shatner: James T. Kirk
        20. Armin Shimerman: Quark

    The v2 nn top 20:
        1. Michael Dorn: Worf
        2. Kate Mulgrew: Kathryn Janeway
        3. Patrick Stewart: Jean-Luc Picard
        4. Colm Meaney: Miles O'Brien
        5. Jonathan Frakes: William T. Riker
        6. Brent Spiner: Data
        7. Marina Sirtis: Deanna Troi
        8. LeVar Burton: Geordi La Forge
        9. Gates McFadden: Beverly Crusher
        10. Tim Russ: Tuvok
        11. Robert Beltran: Chakotay
        12. Robert Duncan McNeill: Tom Paris
        13. Robert Picardo: The Doctor
        14. Ethan Phillips: Neelix
        15. Garrett Wang: Harry Kim
        16. Roxann Dawson: B'Elanna Torres
        17. Armin Shimerman: Quark
        18. Rene Auberjonois: Odo
        19. Alexander Siddig: Julian Bashir
        20. Nana Visitor: Kira Nerys
    
    The v2's top 20 seems much more accurate to me. The v1 top 20 is full of Prodigy
    characters. Prodigy only ran for 19 episodes, so I think their popularity is 
    overblown here. I think this is because there are A LOT more episode ratings 
    for Star Trek: Prodigy than there are for other ST shows. This could be due
    to recency or because it's an animated children's show, I'm not sure. 



         
         
            
         
