-- Sample Data for Star Trek Database
-- This file contains example data to demonstrate the database structure

-- Insert Species
INSERT INTO Species (name, homeworld, classification, warp_capable, description) VALUES
('Human', 'Earth', 'Humanoid', 1, 'Native species of Earth, founding member of the United Federation of Planets'),
('Vulcan', 'Vulcan', 'Humanoid', 1, 'Logical species known for emotional control and telepathic abilities'),
('Klingon', 'Qo''noS', 'Humanoid', 1, 'Warrior species with a strong honor-based culture'),
('Romulan', 'Romulus', 'Humanoid', 1, 'Secretive species related to Vulcans, known for military prowess'),
('Betazoid', 'Betazed', 'Humanoid', 1, 'Empathic and telepathic humanoid species'),
('Android', NULL, 'Artificial', 0, 'Artificial lifeform'),
('Klingon-Human Hybrid', NULL, 'Humanoid', 1, 'Mixed species heritage');

-- Insert Origins
INSERT INTO Origins (name, type, quadrant, sector, description) VALUES
('Earth', 'Planet', 'Alpha', 'Sol System', 'Homeworld of humanity and capital of the United Federation of Planets'),
('Vulcan', 'Planet', 'Alpha', 'Vulcan System', 'Desert planet and homeworld of the Vulcan species'),
('Qo''noS', 'Planet', 'Beta', 'Klingon Empire', 'Homeworld of the Klingon Empire'),
('Betazed', 'Planet', 'Alpha', 'Betazed System', 'Homeworld of the Betazoid species'),
('Deep Space 9', 'Space Station', 'Alpha', 'Bajoran System', 'Former Cardassian station near the Bajoran wormhole'),
('Omicron Theta', 'Planet', 'Unknown', 'Unknown', 'Colony world where Data was discovered');

-- Insert Organizations
INSERT INTO Organizations (name, type, affiliation, description) VALUES
('Starfleet', 'Military', 'United Federation of Planets', 'Space exploration and defense organization'),
('United Federation of Planets', 'Government', NULL, 'Interstellar union of planetary governments'),
('Klingon Empire', 'Government', NULL, 'Klingon interstellar state'),
('Romulan Star Empire', 'Government', NULL, 'Romulan interstellar state'),
('Maquis', 'Resistance', NULL, 'Rebel organization fighting Cardassian occupation');

-- Insert Actors
INSERT INTO Actors (first_name, last_name, nationality) VALUES
('William', 'Shatner', 'Canadian'),
('Patrick', 'Stewart', 'British'),
('Avery', 'Brooks', 'American'),
('Kate', 'Mulgrew', 'American'),
('Leonard', 'Nimoy', 'American'),
('Brent', 'Spiner', 'American'),
('Marina', 'Sirtis', 'British'),
('Michael', 'Dorn', 'American'),
('Zachary', 'Quinto', 'American');

-- Insert Ships
INSERT INTO Ships (name, registry, class, type, organization_id, status, description) VALUES
('USS Enterprise', 'NCC-1701', 'Constitution', 'Starship', 1, 'Decommissioned', 'Famous Constitution-class starship commanded by James T. Kirk'),
('USS Enterprise', 'NCC-1701-D', 'Galaxy', 'Starship', 1, 'Destroyed', 'Galaxy-class flagship commanded by Jean-Luc Picard'),
('USS Enterprise', 'NCC-1701-E', 'Sovereign', 'Starship', 1, 'Active', 'Sovereign-class ship commanded by Jean-Luc Picard'),
('USS Defiant', 'NX-74205', 'Defiant', 'Warship', 1, 'Destroyed', 'First Defiant-class warship assigned to Deep Space 9'),
('USS Voyager', 'NCC-74656', 'Intrepid', 'Starship', 1, 'Active', 'Intrepid-class ship lost in the Delta Quadrant');

-- Insert Series
INSERT INTO Series (name, abbreviation, start_year, end_year, num_seasons, num_episodes) VALUES
('Star Trek: The Original Series', 'TOS', 1966, 1969, 3, 79),
('Star Trek: The Next Generation', 'TNG', 1987, 1994, 7, 178),
('Star Trek: Deep Space Nine', 'DS9', 1993, 1999, 7, 176),
('Star Trek: Voyager', 'VOY', 1995, 2001, 7, 172),
('Star Trek: Enterprise', 'ENT', 2001, 2005, 4, 98),
('Star Trek: Discovery', 'DIS', 2017, NULL, 5, 65);

-- Insert Characters
INSERT INTO Characters (name, rank, title, species_id, origin_id, gender, occupation, bio) VALUES
('James T. Kirk', 'Captain', 'Commanding Officer', 1, 1, 'Male', 'Starfleet Officer', 'Legendary Starfleet captain known for his diplomatic and military achievements'),
('Jean-Luc Picard', 'Captain', 'Commanding Officer', 1, 1, 'Male', 'Starfleet Officer', 'Distinguished captain and diplomat, commanding officer of USS Enterprise-D and E'),
('Spock', 'Commander', 'Science Officer', 2, 2, 'Male', 'Starfleet Officer', 'Half-Vulcan, half-human science officer known for his logic and loyalty'),
('Data', 'Lieutenant Commander', 'Operations Officer', 6, 6, 'Male', 'Starfleet Officer', 'Sentient android seeking to understand humanity'),
('Deanna Troi', 'Commander', 'Counselor', 5, 4, 'Female', 'Starfleet Officer', 'Empathic counselor aboard USS Enterprise-D'),
('Worf', 'Lieutenant Commander', 'Security Chief', 3, 3, 'Male', 'Starfleet Officer', 'First Klingon officer in Starfleet'),
('Benjamin Sisko', 'Captain', 'Commanding Officer', 1, 1, 'Male', 'Starfleet Officer', 'Commander of Deep Space 9 and Emissary to the Prophets'),
('Kathryn Janeway', 'Captain', 'Commanding Officer', 1, 1, 'Female', 'Starfleet Officer', 'Captain of USS Voyager stranded in the Delta Quadrant'),
('B''Elanna Torres', 'Lieutenant', 'Chief Engineer', 7, 3, 'Female', 'Starfleet Officer', 'Half-Klingon, half-human engineer on USS Voyager');

-- Link Characters to Actors
INSERT INTO Character_Actors (character_id, actor_id, series, first_appearance, episodes_count) VALUES
(1, 1, 'TOS', 'The Man Trap', 79),
(2, 2, 'TNG', 'Encounter at Farpoint', 178),
(3, 5, 'TOS', 'The Man Trap', 79),
(3, 9, 'Star Trek (2009)', 'Star Trek', 3),
(4, 6, 'TNG', 'Encounter at Farpoint', 176),
(5, 7, 'TNG', 'Encounter at Farpoint', 172),
(6, 8, 'TNG', 'Encounter at Farpoint', 272),
(7, 3, 'DS9', 'Emissary', 173),
(8, 4, 'VOY', 'Caretaker', 168);

-- Link Characters to Organizations
INSERT INTO Character_Organizations (character_id, organization_id, role, notes) VALUES
(1, 1, 'Captain', 'Commanding officer of multiple starships'),
(2, 1, 'Captain', 'Commanding officer of USS Enterprise-D and E'),
(3, 1, 'Commander', 'Science Officer and First Officer'),
(4, 1, 'Lieutenant Commander', 'Operations Officer'),
(5, 1, 'Commander', 'Ship''s Counselor'),
(6, 1, 'Lieutenant Commander', 'Security Chief and Tactical Officer'),
(7, 1, 'Captain', 'Station Commander'),
(8, 1, 'Captain', 'Ship''s Captain'),
(9, 5, 'Member', 'Former Maquis member before joining Voyager crew'),
(9, 1, 'Lieutenant', 'Chief Engineer after integration with Starfleet');

-- Link Characters to Ships
INSERT INTO Character_Ships (character_id, ship_id, role, notes) VALUES
(1, 1, 'Captain', 'Commanding officer during its five-year mission'),
(2, 2, 'Captain', 'Commanding officer for seven years'),
(2, 3, 'Captain', 'Commanding officer'),
(3, 1, 'First Officer', 'Science Officer and First Officer'),
(4, 2, 'Operations Officer', 'Second Officer'),
(5, 2, 'Counselor', 'Ship''s Counselor'),
(6, 2, 'Security Chief', 'Chief of Security'),
(6, 4, 'First Officer', 'Later transferred to DS9 and commanded USS Defiant'),
(8, 5, 'Captain', 'Commanding officer during Delta Quadrant journey'),
(9, 5, 'Chief Engineer', 'Chief Engineer');

-- Insert sample episodes
INSERT INTO Episodes (series_id, title, season, episode_number, air_date, description) VALUES
(1, 'The Man Trap', 1, 1, '1966-09-08', 'The Enterprise crew encounters a shape-shifting creature'),
(1, 'The City on the Edge of Forever', 1, 28, '1967-04-06', 'Kirk and Spock travel back in time to 1930s Earth'),
(2, 'Encounter at Farpoint', 1, 1, '1987-09-28', 'The new Enterprise crew faces their first mission and meets Q'),
(2, 'The Best of Both Worlds', 3, 26, '1990-06-18', 'Picard is assimilated by the Borg'),
(3, 'Emissary', 1, 1, '1993-01-03', 'Commander Sisko takes command of Deep Space 9'),
(4, 'Caretaker', 1, 1, '1995-01-16', 'Voyager is transported to the Delta Quadrant');

-- Link Characters to Episodes (sample)
INSERT INTO Character_Episodes (character_id, episode_id, role_type) VALUES
(1, 1, 'main'),
(1, 2, 'main'),
(3, 1, 'main'),
(3, 2, 'main'),
(2, 3, 'main'),
(2, 4, 'main'),
(4, 3, 'main'),
(5, 3, 'main'),
(6, 3, 'main'),
(7, 5, 'main'),
(8, 6, 'main'),
(9, 6, 'main');
