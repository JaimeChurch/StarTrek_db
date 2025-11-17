"""
Neural Network for Star Trek Database Analysis
Uses NN to predict episode quality and determine character/species/actor popularity
"""

import torch
import torch.nn as nn
import torch.optim as optim
import sqlite3
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

class StarTrekNN(nn.Module):
    def __init__(self, input_size):
        super(StarTrekNN, self).__init__()
        # Deep architecture for learning episode quality patterns
        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 32)
        self.fc4 = nn.Linear(32, 1)
        
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.relu(self.fc3(x))
        x = self.sigmoid(self.fc4(x))  # Output 0-1 (normalized rating)
        return x


class StarTrekAnalyzer:
    def __init__(self, db_path='startrek.db'):
        self.db_path = db_path
        self.conn = None
        self.model = None
        self.scaler = StandardScaler()
        
        # Vocabularies for encoding
        self.all_species = []
        self.all_planets = []
        self.all_characters = []
        
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        
    def close(self):
        if self.conn:
            self.conn.close()
    
    def load_episode_data(self):
        """Load all episodes with their features"""
        query = """
        SELECT 
            e.episode_id,
            e.series_id,
            e.season,
            e.episode_number,
            e.imdb_rating,
            e.imdb_votes,
            e.description,
            e.air_date,
            s.abbreviation as series_code
        FROM Episodes e
        JOIN Series s ON e.series_id = s.series_id
        WHERE e.imdb_rating IS NOT NULL
        """
        return pd.read_sql_query(query, self.conn)
    
    def load_character_episodes(self):
        """Load character appearances in episodes"""
        query = """
        SELECT 
            ce.episode_id,
            ce.character_id,
            c.name as character_name,
            sp.name as species_name
        FROM Character_Episodes ce
        JOIN Characters c ON ce.character_id = c.character_id
        LEFT JOIN Species sp ON c.species_id = sp.species_id
        """
        return pd.read_sql_query(query, self.conn)
    
    def load_actor_episodes(self):
        """Load actor performances in episodes"""
        query = """
        SELECT 
            ce.episode_id,
            a.actor_id,
            a.first_name || ' ' || a.last_name as actor_name,
            c.character_id,
            c.name as character_name
        FROM Character_Episodes ce
        JOIN Characters c ON ce.character_id = c.character_id
        JOIN Character_Actors ca ON c.character_id = ca.character_id
        JOIN Actors a ON ca.actor_id = a.actor_id
        """
        return pd.read_sql_query(query, self.conn)
    
    def extract_species_from_description(self, description):
        """Extract species mentions from episode description"""
        if pd.isna(description):
            return []
        
        # Common Star Trek species
        species_list = ['Klingon', 'Romulan', 'Vulcan', 'Andorian', 'Tellarite', 'Ferengi', 
                       'Cardassian', 'Bajoran', 'Betazoid', 'Trill', 'Borg', 'Changeling',
                       'Kazon', 'Ocampa', 'Talaxian', 'Species 8472', 'Breen', 'Gorn',
                       'Orion', 'Tholian', 'Horta', 'Tribble', 'Q']
        
        found = []
        desc_lower = description.lower()
        for species in species_list:
            if species.lower() in desc_lower:
                found.append(species)
        return found
    
    def extract_planets_from_description(self, description):
        """Extract planet mentions from episode description"""
        if pd.isna(description):
            return []
        
        # Common Star Trek planets/locations
        planets = ['Earth', 'Vulcan', 'Qo\'noS', 'Romulus', 'Bajor', 'Cardassia', 'Ferenginar',
                  'Betazed', 'Trill', 'Risa', 'Andoria', 'Tellar', 'Deep Space', 'Starbase']
        
        found = []
        desc_lower = description.lower()
        for planet in planets:
            if planet.lower() in desc_lower:
                found.append(planet)
        return found
    
    def build_vocabularies(self, episode_df, character_df):
        """Build vocabularies of all unique species, planets, and characters"""
        print("\nBuilding vocabularies...")
        
        # Get all unique species mentioned in descriptions
        all_species_set = set()
        for desc in episode_df['description']:
            species = self.extract_species_from_description(desc)
            all_species_set.update(species)
        self.all_species = sorted(list(all_species_set))
        
        # Get all unique planets mentioned in descriptions
        all_planets_set = set()
        for desc in episode_df['description']:
            planets = self.extract_planets_from_description(desc)
            all_planets_set.update(planets)
        self.all_planets = sorted(list(all_planets_set))
        
        # Get all unique characters from database
        self.all_characters = sorted(character_df['character_name'].unique().tolist())
        
        print(f"Found {len(self.all_species)} unique species mentions")
        print(f"Found {len(self.all_planets)} unique planet mentions")
        print(f"Found {len(self.all_characters)} unique characters")
    
    def build_episode_features(self, episode_df, character_df):
        """Build feature vectors for each episode"""
        features_list = []
        episode_ids = []
        targets = []
        weights = []
        
        for _, ep in episode_df.iterrows():
            episode_id = ep['episode_id']
            
            # Get characters in this episode
            chars = character_df[character_df['episode_id'] == episode_id]
            char_names = chars['character_name'].tolist()
            
            # Basic features
            num_chars = len(chars)
            season = ep['season'] if pd.notna(ep['season']) else 0
            ep_num = ep['episode_number'] if pd.notna(ep['episode_number']) else 0
            
            # Air date features
            if pd.notna(ep['air_date']):
                try:
                    air_date = pd.to_datetime(ep['air_date'])
                    air_year = air_date.year
                    air_month = air_date.month
                    air_day = air_date.day
                except:
                    air_year = 0
                    air_month = 0
                    air_day = 0
            else:
                air_year = 0
                air_month = 0
                air_day = 0
            
            # Species mentioned in description
            species_mentioned = self.extract_species_from_description(ep['description'])
            
            # Planets mentioned in description
            planets_mentioned = self.extract_planets_from_description(ep['description'])
            
            # Series encoding
            series_map = {'TOS': 1, 'TNG': 2, 'DS9': 3, 'VOY': 4, 'ENT': 5}
            series_code = series_map.get(ep['series_code'], 0)
            
            # Build feature vector
            feature_vector = [
                num_chars, season, ep_num, air_year, air_month, air_day, series_code
            ]
            
            # One-hot encode species (1 if mentioned, 0 if not)
            for species in self.all_species:
                feature_vector.append(1.0 if species in species_mentioned else 0.0)
            
            # One-hot encode planets (1 if mentioned, 0 if not)
            for planet in self.all_planets:
                feature_vector.append(1.0 if planet in planets_mentioned else 0.0)
            
            # One-hot encode characters (1 if appears in episode, 0 if not)
            for character in self.all_characters:
                feature_vector.append(1.0 if character in char_names else 0.0)
            
            # Target: normalized rating
            rating = ep['imdb_rating'] / 10.0
            
            # Weight: log of votes
            weight = np.log1p(ep['imdb_votes']) if ep['imdb_votes'] > 0 else 1.0
            
            features_list.append(feature_vector)
            episode_ids.append(episode_id)
            targets.append(rating)
            weights.append(weight)
        
        return np.array(features_list, dtype=np.float32), np.array(targets, dtype=np.float32), np.array(weights, dtype=np.float32), episode_ids
    
    def train_model(self, features, targets, weights, epochs=1000, learning_rate=0.001):
        """Train the neural network on episode data"""
        print("\n" + "="*70)
        print("TRAINING NEURAL NETWORK")
        print("="*70)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Convert to tensors
        X = torch.FloatTensor(features_scaled)
        y = torch.FloatTensor(targets).reshape(-1, 1)
        w = torch.FloatTensor(weights).reshape(-1, 1)
        
        # Initialize model
        input_size = X.shape[1]
        self.model = StarTrekNN(input_size)
        
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss(reduction='none')
        
        print(f"Training on {len(X)} episodes with {input_size} features")
        print(f"Epochs: {epochs}, Learning rate: {learning_rate}")
        
        losses = []
        
        for epoch in range(epochs):
            self.model.train()
            
            # Forward pass
            predictions = self.model(X)
            
            # Weighted loss
            loss = criterion(predictions, y)
            weighted_loss = (loss * w).mean()
            
            # Backward pass
            optimizer.zero_grad()
            weighted_loss.backward()
            optimizer.step()
            
            losses.append(weighted_loss.item())
            
            if (epoch + 1) % 100 == 0:
                print(f"Epoch {epoch + 1}/{epochs}, Loss: {weighted_loss.item():.6f}")
        
        print(f"\nTraining complete! Final loss: {losses[-1]:.6f}")
        
        return losses
    
    def predict_episode_quality(self, features):
        """Use trained model to predict episode quality (0-10 scale)"""
        self.model.eval()
        with torch.no_grad():
            features_scaled = self.scaler.transform(features)
            X = torch.FloatTensor(features_scaled)
            predictions = self.model(X).numpy().flatten()
            return predictions * 10.0  # Convert back to 0-10 scale
    
    def analyze_character_popularity(self, episode_df, character_df):
        """Use NN to determine character popularity"""
        print("\n" + "="*70)
        print("ANALYZING CHARACTER POPULARITY WITH NEURAL NETWORK")
        print("="*70)
        
        results = []
        
        for char_id in character_df['character_id'].unique():
            # Get episodes this character appears in
            char_episodes = character_df[character_df['character_id'] == char_id]
            char_name = char_episodes['character_name'].iloc[0]
            species = char_episodes['species_name'].iloc[0] if pd.notna(char_episodes['species_name'].iloc[0]) else 'Unknown'
            
            # Get episode details
            ep_ids = char_episodes['episode_id'].unique()
            char_eps = episode_df[episode_df['episode_id'].isin(ep_ids)]
            
            if len(char_eps) == 0:
                continue
            
            # Build features for these episodes
            features, _, _, _ = self.build_episode_features(char_eps, character_df)
            
            # Use NN to predict quality scores
            predicted_ratings = self.predict_episode_quality(features)
            
            # Calculate popularity metrics
            num_episodes = len(char_eps)
            avg_predicted_rating = predicted_ratings.mean()
            total_votes = char_eps['imdb_votes'].sum()
            
            # Get series
            series_list = char_eps['series_code'].unique().tolist()
            
            # Popularity score: average NN prediction weighted by episode count and votes
            popularity_score = (avg_predicted_rating * np.log1p(num_episodes) * np.log1p(total_votes)) / 100
            
            results.append({
                'character_name': char_name,
                'species': species,
                'num_episodes': num_episodes,
                'nn_avg_rating': round(avg_predicted_rating, 2),
                'total_votes': int(total_votes),
                'series': ', '.join(series_list),
                'popularity_score': round(popularity_score, 2)
            })
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('popularity_score', ascending=False)
        
        print(f"Analyzed {len(results_df)} characters")
        
        return results_df
    
    def analyze_species_popularity(self, episode_df, character_df):
        """Use NN to determine species popularity"""
        print("\n" + "="*70)
        print("ANALYZING SPECIES POPULARITY WITH NEURAL NETWORK")
        print("="*70)
        
        results = []
        
        for species_name in character_df['species_name'].dropna().unique():
            # Get all characters of this species
            species_chars = character_df[character_df['species_name'] == species_name]
            
            # Get all episodes featuring this species
            ep_ids = species_chars['episode_id'].unique()
            species_eps = episode_df[episode_df['episode_id'].isin(ep_ids)]
            
            if len(species_eps) == 0:
                continue
            
            # Build features
            features, _, _, _ = self.build_episode_features(species_eps, character_df)
            
            # NN predictions
            predicted_ratings = self.predict_episode_quality(features)
            
            # Metrics
            num_characters = species_chars['character_id'].nunique()
            num_episodes = len(species_eps)
            avg_predicted_rating = predicted_ratings.mean()
            total_votes = species_eps['imdb_votes'].sum()
            
            popularity_score = (avg_predicted_rating * np.log1p(num_episodes) * np.log1p(total_votes)) / 100
            
            results.append({
                'species': species_name,
                'num_characters': num_characters,
                'num_episodes': num_episodes,
                'nn_avg_rating': round(avg_predicted_rating, 2),
                'total_votes': int(total_votes),
                'popularity_score': round(popularity_score, 2)
            })
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('popularity_score', ascending=False)
        
        print(f"Analyzed {len(results_df)} species")
        
        return results_df
    
    def analyze_actor_popularity(self, episode_df, actor_df, character_df):
        """Use NN to determine actor popularity"""
        print("\n" + "="*70)
        print("ANALYZING ACTOR POPULARITY WITH NEURAL NETWORK")
        print("="*70)
        
        results = []
        
        for actor_id in actor_df['actor_id'].unique():
            # Get episodes this actor appears in
            actor_episodes = actor_df[actor_df['actor_id'] == actor_id]
            actor_name = actor_episodes['actor_name'].iloc[0]
            
            # Get their characters (sorted by episode count)
            char_counts = actor_episodes.groupby('character_name').size().sort_values(ascending=False)
            main_characters = ', '.join(char_counts.head(3).index.tolist())
            
            # Get episode details
            ep_ids = actor_episodes['episode_id'].unique()
            actor_eps = episode_df[episode_df['episode_id'].isin(ep_ids)]
            
            if len(actor_eps) == 0:
                continue
            
            # Build features
            features, _, _, _ = self.build_episode_features(actor_eps, character_df)
            
            # NN predictions
            predicted_ratings = self.predict_episode_quality(features)
            
            # Metrics
            num_episodes = len(actor_eps)
            avg_predicted_rating = predicted_ratings.mean()
            total_votes = actor_eps['imdb_votes'].sum()
            
            # Get series
            series_list = actor_eps['series_code'].unique().tolist()
            
            popularity_score = (avg_predicted_rating * np.log1p(num_episodes) * np.log1p(total_votes)) / 100
            
            results.append({
                'actor_name': actor_name,
                'main_characters': main_characters,
                'num_episodes': num_episodes,
                'nn_avg_rating': round(avg_predicted_rating, 2),
                'total_votes': int(total_votes),
                'series': ', '.join(series_list),
                'popularity_score': round(popularity_score, 2)
            })
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('popularity_score', ascending=False)
        
        print(f"Analyzed {len(results_df)} actors")
        
        return results_df


def main():
    print("="*70)
    print("STAR TREK DATABASE ANALYSIS WITH NEURAL NETWORK")
    print("="*70)
    
    analyzer = StarTrekAnalyzer()
    analyzer.connect()
    
    # Load data
    print("\nLoading data from database...")
    episode_df = analyzer.load_episode_data()
    character_df = analyzer.load_character_episodes()
    actor_df = analyzer.load_actor_episodes()
    
    print(f"Loaded {len(episode_df)} episodes")
    print(f"Loaded {len(character_df)} character appearances")
    print(f"Loaded {len(actor_df)} actor performances")
    
    # Build vocabularies for encoding
    analyzer.build_vocabularies(episode_df, character_df)
    
    # Build features and train model
    features, targets, weights, episode_ids = analyzer.build_episode_features(episode_df, character_df)
    losses = analyzer.train_model(features, targets, weights, epochs=1000, learning_rate=0.001)
    
    # Save model
    torch.save(analyzer.model.state_dict(), 'startrek_nn_model.pth')
    print("\n✓ Model saved to startrek_nn_model.pth")
    
    # Use trained NN to analyze popularity
    char_popularity = analyzer.analyze_character_popularity(episode_df, character_df)
    species_popularity = analyzer.analyze_species_popularity(episode_df, character_df)
    actor_popularity = analyzer.analyze_actor_popularity(episode_df, actor_df, character_df)
    
    # Display results
    print("\n" + "="*70)
    print("TOP 20 MOST POPULAR CHARACTERS (by Neural Network)")
    print("="*70)
    print(char_popularity.head(20).to_string(index=False))
    
    print("\n" + "="*70)
    print("TOP 15 MOST POPULAR SPECIES (by Neural Network)")
    print("="*70)
    print(species_popularity.head(15).to_string(index=False))
    
    print("\n" + "="*70)
    print("TOP 20 MOST POPULAR ACTORS (by Neural Network)")
    print("="*70)
    print(actor_popularity.head(20).to_string(index=False))
    
    # Export to CSV
    print("\n" + "="*70)
    print("EXPORTING RESULTS")
    print("="*70)
    
    char_popularity.to_csv('nn_character_popularity.csv', index=False)
    print("✓ Character popularity saved to nn_character_popularity.csv")
    
    species_popularity.to_csv('nn_species_popularity.csv', index=False)
    print("✓ Species popularity saved to nn_species_popularity.csv")
    
    actor_popularity.to_csv('nn_actor_popularity.csv', index=False)
    print("✓ Actor popularity saved to nn_actor_popularity.csv")
    
    analyzer.close()
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
