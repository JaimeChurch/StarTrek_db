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
    
    
