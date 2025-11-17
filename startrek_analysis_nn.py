"""
Neural Network for Star Trek Database Analysis
Analyzes episode ratings, descriptions, character appearances, and species
to determine popularity and find patterns
"""

import torch
import torch.nn as nn
import torch.optim as optim
import sqlite3
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import re
from collections import defaultdict

class StarTrekAnalysisNN(nn.Module):
    def __init__(self, input_size, hidden_size=128):
        super(StarTrekAnalysisNN, self).__init__()
        # Multi-layer architecture for complex pattern recognition
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size // 2)
        self.fc3 = nn.Linear(hidden_size // 2, hidden_size // 4)
        self.fc4 = nn.Linear(hidden_size // 4, 1)  # Output: popularity score
        
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.relu(self.fc3(x))
        x = self.sigmoid(self.fc4(x))  # Output between 0-1
        return x


class StarTrekDataLoader:
    def __init__(self, db_path='startrek.db'):
        self.db_path = db_path
        self.conn = None
        self.tfidf_vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        self.scaler = StandardScaler()
        
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        
    def close(self):
        if self.conn:
            self.conn.close()
    
    def get_episode_data(self):
        """Get all episode data with ratings, descriptions, votes"""
        query = """
        SELECT 
            e.episode_id,
            e.series_id,
            s.abbreviation as series_code,
            e.title,
            e.season,
            e.episode_number,
            e.imdb_rating,
            e.imdb_votes,
            e.description
        FROM Episodes e
        JOIN Series s ON e.series_id = s.series_id
        WHERE e.imdb_rating IS NOT NULL
        ORDER BY s.abbreviation, e.season, e.episode_number
        """
        df = pd.read_sql_query(query, self.conn)
        
        # Fill missing descriptions with empty string
        df['description'] = df['description'].fillna('')
        df['imdb_votes'] = df['imdb_votes'].fillna(0)
        
        return df
    
    def get_character_episodes(self):
        """Get character appearances in episodes"""
        query = """
        SELECT 
            ce.episode_id,
            c.character_id,
            c.name as character_name,
            c.species_id,
            sp.name as species_name,
            s.abbreviation as series_code
        FROM Character_Episodes ce
        JOIN Characters c ON ce.character_id = c.character_id
        LEFT JOIN Species sp ON c.species_id = sp.species_id
        JOIN Episodes e ON ce.episode_id = e.episode_id
        JOIN Series s ON e.series_id = s.series_id
        """
        df = pd.read_sql_query(query, self.conn)
        return df
    
    def get_actor_episodes(self):
        """Get actor performances in episodes"""
        query = """
        SELECT 
            ce.episode_id,
            a.actor_id,
            a.first_name || ' ' || a.last_name as actor_name,
            c.character_id,
            c.name as character_name,
            ca.series as series_code
        FROM Character_Episodes ce
        JOIN Characters c ON ce.character_id = c.character_id
        JOIN Character_Actors ca ON c.character_id = ca.character_id
        JOIN Actors a ON ca.actor_id = a.actor_id
        JOIN Episodes e ON ce.episode_id = e.episode_id
        """
        df = pd.read_sql_query(query, self.conn)
        return df
    
    def analyze_character_popularity(self, episode_df, character_df):
        """
        Calculate character popularity scores based on:
        - Number of episode appearances
        - Average rating of episodes they appear in (weighted by votes)
        - Total votes on their episodes
        """
        print("\n" + "="*70)
        print("ANALYZING CHARACTER POPULARITY")
        print("="*70)
        
        # Merge character appearances with episode ratings
        merged = character_df.merge(episode_df, on='episode_id', how='left')
        
        results = []
        
        for char_id in merged['character_id'].unique():
            char_data = merged[merged['character_id'] == char_id]
            char_name = char_data['character_name'].iloc[0]
            species = char_data['species_name'].iloc[0] if pd.notna(char_data['species_name'].iloc[0]) else 'Unknown'
            
            # Calculate metrics
            num_episodes = len(char_data)
            
            # Weighted average rating (weighted by votes)
            valid_ratings = char_data[char_data['imdb_rating'].notna()]
            if len(valid_ratings) > 0:
                total_votes = valid_ratings['imdb_votes'].sum()
                if total_votes > 0:
                    weighted_rating = (valid_ratings['imdb_rating'] * valid_ratings['imdb_votes']).sum() / total_votes
                else:
                    weighted_rating = valid_ratings['imdb_rating'].mean()
                
                total_votes_on_episodes = valid_ratings['imdb_votes'].sum()
            else:
                weighted_rating = 0
                total_votes_on_episodes = 0
            
            # Get series appearances
            series_list = char_data['series_code_x'].unique().tolist()
            
            results.append({
                'character_id': char_id,
                'character_name': char_name,
                'species': species,
                'num_episodes': num_episodes,
                'weighted_avg_rating': weighted_rating,
                'total_votes': total_votes_on_episodes,
                'series': ', '.join(series_list),
                'popularity_score': (weighted_rating * np.log1p(total_votes_on_episodes)) / 10  # Normalized score
            })
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('popularity_score', ascending=False)
        
        return results_df
    
    def analyze_species_popularity(self, episode_df, character_df):
        """Analyze species popularity based on character appearances and ratings"""
        print("\n" + "="*70)
        print("ANALYZING SPECIES POPULARITY")
        print("="*70)
        
        # Merge data
        merged = character_df.merge(episode_df, on='episode_id', how='left')
        merged = merged[merged['species_name'].notna()]
        
        results = []
        
        for species in merged['species_name'].unique():
            species_data = merged[merged['species_name'] == species]
            
            # Calculate metrics
            num_characters = species_data['character_id'].nunique()
            num_episodes = len(species_data)
            
            valid_ratings = species_data[species_data['imdb_rating'].notna()]
            if len(valid_ratings) > 0:
                total_votes = valid_ratings['imdb_votes'].sum()
                if total_votes > 0:
                    weighted_rating = (valid_ratings['imdb_rating'] * valid_ratings['imdb_votes']).sum() / total_votes
                else:
                    weighted_rating = valid_ratings['imdb_rating'].mean()
            else:
                weighted_rating = 0
                total_votes = 0
            
            results.append({
                'species': species,
                'num_characters': num_characters,
                'num_episodes': num_episodes,
                'weighted_avg_rating': weighted_rating,
                'total_votes': total_votes,
                'popularity_score': (weighted_rating * np.log1p(total_votes)) / 10
            })
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('popularity_score', ascending=False)
        
        return results_df
    
    def analyze_actor_popularity(self, episode_df, actor_df):
        """
        Calculate actor popularity scores based on:
        - Number of episode appearances
        - Average rating of episodes they appear in (weighted by votes)
        - Total votes on their episodes
        - Number of characters they've played
        """
        print("\n" + "="*70)
        print("ANALYZING ACTOR POPULARITY")
        print("="*70)
        
        # Merge actor appearances with episode ratings
        merged = actor_df.merge(episode_df, on='episode_id', how='left')
        
        results = []
        
        for actor_id in merged['actor_id'].unique():
            actor_data = merged[merged['actor_id'] == actor_id]
            actor_name = actor_data['actor_name'].iloc[0]
            
            # Calculate metrics
            num_episodes = len(actor_data)
            num_characters = actor_data['character_id'].nunique()
            
            # Get character names sorted by episode count
            char_episode_counts = actor_data.groupby('character_name').size().sort_values(ascending=False)
            top_characters = char_episode_counts.head(3).index.tolist()
            character_list = ', '.join(top_characters)  # Show top 3 characters by episode count
            if len(char_episode_counts) > 3:
                character_list += f" (+{len(char_episode_counts)-3} more)"
            
            # Weighted average rating (weighted by votes)
            valid_ratings = actor_data[actor_data['imdb_rating'].notna()]
            if len(valid_ratings) > 0:
                total_votes = valid_ratings['imdb_votes'].sum()
                if total_votes > 0:
                    weighted_rating = (valid_ratings['imdb_rating'] * valid_ratings['imdb_votes']).sum() / total_votes
                else:
                    weighted_rating = valid_ratings['imdb_rating'].mean()
                
                total_votes_on_episodes = valid_ratings['imdb_votes'].sum()
            else:
                weighted_rating = 0
                total_votes_on_episodes = 0
            
            # Get series appearances (filter out None values)
            series_list = [s for s in actor_data['series_code_x'].unique() if pd.notna(s)]
            series_str = ', '.join(series_list) if series_list else 'Unknown'
            
            results.append({
                'actor_id': actor_id,
                'actor_name': actor_name,
                'num_episodes': num_episodes,
                'num_characters': num_characters,
                'main_characters': character_list,
                'weighted_avg_rating': weighted_rating,
                'total_votes': total_votes_on_episodes,
                'series': series_str,
                'popularity_score': (weighted_rating * np.log1p(total_votes_on_episodes)) / 10
            })
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('popularity_score', ascending=False)
        
        return results_df
    
    def extract_description_features(self, descriptions):
        """Extract TF-IDF features from episode descriptions"""
        if len(descriptions) == 0:
            return np.array([])
        
        # Clean descriptions
        descriptions = [str(d).lower() for d in descriptions]
        
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(descriptions)
            return tfidf_matrix.toarray()
        except:
            return np.zeros((len(descriptions), 100))
    
    def find_description_patterns(self, episode_df):
        """Find common themes and patterns in highly-rated episodes"""
        print("\n" + "="*70)
        print("ANALYZING DESCRIPTION PATTERNS")
        print("="*70)
        
        # Filter episodes with descriptions and ratings
        valid_eps = episode_df[(episode_df['description'] != '') & 
                               (episode_df['imdb_rating'].notna())].copy()
        
        if len(valid_eps) == 0:
            print("No episodes with descriptions and ratings found.")
            return None
        
        # Reset index to ensure array indices match
        valid_eps = valid_eps.reset_index(drop=True)
        
        # Extract TF-IDF features
        tfidf_features = self.extract_description_features(valid_eps['description'])
        
        # Separate high and low rated episodes
        median_rating = valid_eps['imdb_rating'].median()
        high_rated_mask = valid_eps['imdb_rating'] >= median_rating
        low_rated_mask = valid_eps['imdb_rating'] < median_rating
        
        # Get indices as array positions (0-based, matching tfidf array)
        high_rated_indices = valid_eps[high_rated_mask].index.tolist()
        low_rated_indices = valid_eps[low_rated_mask].index.tolist()
        
        # Get top keywords for each group
        feature_names = self.tfidf_vectorizer.get_feature_names_out()
        
        print(f"\nAnalyzed {len(valid_eps)} episodes with descriptions")
        print(f"Median rating: {median_rating:.2f}")
        print(f"High-rated episodes (≥{median_rating:.2f}): {len(high_rated_indices)}")
        print(f"Low-rated episodes (<{median_rating:.2f}): {len(low_rated_indices)}")
        
        return {
            'tfidf_features': tfidf_features,
            'feature_names': feature_names,
            'high_rated_indices': high_rated_indices,
            'low_rated_indices': low_rated_indices
        }
    
    def prepare_neural_network_data(self, episode_df, character_df):
        """Prepare features for neural network training"""
        print("\n" + "="*70)
        print("PREPARING NEURAL NETWORK TRAINING DATA")
        print("="*70)
        
        # Filter episodes with ratings
        valid_eps = episode_df[episode_df['imdb_rating'].notna()].copy()
        
        features_list = []
        targets = []
        episode_ids = []
        
        for idx, row in valid_eps.iterrows():
            episode_id = row['episode_id']
            
            # Get characters in this episode
            chars_in_ep = character_df[character_df['episode_id'] == episode_id]
            
            # Feature 1: Number of characters
            num_chars = len(chars_in_ep)
            
            # Feature 2: Number of unique species
            num_species = chars_in_ep['species_name'].nunique() if len(chars_in_ep) > 0 else 0
            
            # Feature 3: Has human characters
            has_human = 1 if 'Human' in chars_in_ep['species_name'].values else 0
            
            # Feature 4: Season number (normalized)
            season_norm = row['season'] / 10.0 if pd.notna(row['season']) else 0
            
            # Feature 5: Episode number in season (normalized)
            ep_num_norm = row['episode_number'] / 25.0 if pd.notna(row['episode_number']) else 0
            
            # Feature 6: Description length (log-scaled)
            desc_length = np.log1p(len(str(row['description']))) / 10.0
            
            # Target: Normalized rating (0-1 scale)
            rating_normalized = row['imdb_rating'] / 10.0
            
            # Weight: Log of votes (for weighted loss)
            weight = np.log1p(row['imdb_votes']) if row['imdb_votes'] > 0 else 1.0
            
            features_list.append([
                num_chars,
                num_species,
                has_human,
                season_norm,
                ep_num_norm,
                desc_length,
                weight  # Include weight as a feature
            ])
            
            targets.append(rating_normalized)
            episode_ids.append(episode_id)
        
        features_array = np.array(features_list, dtype=np.float32)
        targets_array = np.array(targets, dtype=np.float32).reshape(-1, 1)
        
        print(f"Prepared {len(features_array)} training samples")
        print(f"Feature dimensions: {features_array.shape}")
        
        return features_array, targets_array, episode_ids


def train_neural_network(features, targets, epochs=1000, learning_rate=0.001):
    """Train the neural network to predict episode ratings"""
    print("\n" + "="*70)
    print("TRAINING NEURAL NETWORK")
    print("="*70)
    
    # Convert to PyTorch tensors
    X = torch.FloatTensor(features)
    y = torch.FloatTensor(targets)
    
    # Extract weights (last column of features)
    weights = X[:, -1]
    X_train = X[:, :-1]  # Remove weight column from features
    
    # Create model
    input_size = X_train.shape[1]
    model = StarTrekAnalysisNN(input_size, hidden_size=128)
    
    # Loss and optimizer
    criterion = nn.MSELoss(reduction='none')  # No reduction for weighted loss
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Training loop
    losses = []
    
    for epoch in range(epochs):
        # Forward pass
        predictions = model(X_train)
        
        # Calculate weighted loss
        loss_per_sample = criterion(predictions, y)
        weighted_loss = (loss_per_sample * weights.unsqueeze(1)).mean()
        
        # Backward pass
        optimizer.zero_grad()
        weighted_loss.backward()
        optimizer.step()
        
        losses.append(weighted_loss.item())
        
        if (epoch + 1) % 100 == 0:
            print(f"Epoch {epoch + 1}/{epochs}, Loss: {weighted_loss.item():.6f}")
    
    print("\nTraining complete!")
    
    return model, losses


def main():
    print("="*70)
    print("STAR TREK DATABASE NEURAL NETWORK ANALYSIS")
    print("="*70)
    
    # Load data
    loader = StarTrekDataLoader()
    loader.connect()
    
    try:
        # Get data
        print("\nLoading data from database...")
        episode_df = loader.get_episode_data()
        character_df = loader.get_character_episodes()
        actor_df = loader.get_actor_episodes()
        
        print(f"Loaded {len(episode_df)} episodes")
        print(f"Loaded {len(character_df)} character appearances")
        print(f"Loaded {len(actor_df)} actor performances")
        
        # Analyze character popularity
        char_popularity = loader.analyze_character_popularity(episode_df, character_df)
        
        print("\n" + "-"*70)
        print("TOP 20 MOST POPULAR CHARACTERS (Overall)")
        print("-"*70)
        print(char_popularity.head(20)[['character_name', 'species', 'num_episodes', 
                                        'weighted_avg_rating', 'series', 'popularity_score']])
        
        # Analyze by series
        print("\n" + "-"*70)
        print("MOST POPULAR CHARACTER PER SERIES")
        print("-"*70)
        for series in episode_df['series_code'].unique():
            series_chars = char_popularity[char_popularity['series'].str.contains(series)]
            if len(series_chars) > 0:
                top_char = series_chars.iloc[0]
                print(f"{series}: {top_char['character_name']} ({top_char['species']}) - "
                      f"{top_char['num_episodes']} episodes, Score: {top_char['popularity_score']:.2f}")
        
        # Analyze species popularity
        species_popularity = loader.analyze_species_popularity(episode_df, character_df)
        
        print("\n" + "-"*70)
        print("TOP 15 MOST POPULAR SPECIES")
        print("-"*70)
        print(species_popularity.head(15)[['species', 'num_characters', 'num_episodes',
                                           'weighted_avg_rating', 'popularity_score']])
        
        # Analyze actor popularity
        actor_popularity = loader.analyze_actor_popularity(episode_df, actor_df)
        
        print("\n" + "-"*70)
        print("TOP 20 MOST POPULAR ACTORS (Overall)")
        print("-"*70)
        print(actor_popularity.head(20)[['actor_name', 'main_characters', 'num_episodes',
                                         'weighted_avg_rating', 'series', 'popularity_score']])
        
        # Analyze by series
        print("\n" + "-"*70)
        print("MOST POPULAR ACTOR PER SERIES")
        print("-"*70)
        for series in episode_df['series_code'].unique():
            series_actors = actor_popularity[actor_popularity['series'].str.contains(series)]
            if len(series_actors) > 0:
                top_actor = series_actors.iloc[0]
                print(f"{series}: {top_actor['actor_name']} ({top_actor['main_characters']}) - "
                      f"{top_actor['num_episodes']} episodes, Score: {top_actor['popularity_score']:.2f}")
        
        # Analyze description patterns
        pattern_data = loader.find_description_patterns(episode_df)
        
        pattern_results = []
        
        if pattern_data:
            # Show top keywords in high-rated episodes
            high_idx = pattern_data['high_rated_indices']
            low_idx = pattern_data['low_rated_indices']
            tfidf = pattern_data['tfidf_features']
            features = pattern_data['feature_names']
            
            if len(high_idx) > 0 and len(low_idx) > 0:
                high_tfidf_avg = tfidf[high_idx].mean(axis=0)
                low_tfidf_avg = tfidf[low_idx].mean(axis=0)
                
                # Calculate difference (keywords more common in high-rated vs low-rated)
                tfidf_diff = high_tfidf_avg - low_tfidf_avg
                
                # Get top keywords for high-rated episodes
                top_high_indices = high_tfidf_avg.argsort()[-30:][::-1]
                
                # Get keywords that differentiate high from low rated
                top_diff_indices = tfidf_diff.argsort()[-30:][::-1]
                
                print("\n" + "-"*70)
                print("TOP KEYWORDS IN HIGH-RATED EPISODES")
                print("-"*70)
                for idx in top_high_indices[:15]:
                    keyword = features[idx]
                    high_score = high_tfidf_avg[idx]
                    low_score = low_tfidf_avg[idx]
                    diff = tfidf_diff[idx]
                    print(f"  - {keyword}: {high_score:.4f} (diff: {diff:+.4f})")
                    
                    pattern_results.append({
                        'Keyword': keyword,
                        'High-Rated Score': round(high_score, 4),
                        'Low-Rated Score': round(low_score, 4),
                        'Difference': round(diff, 4),
                        'Pattern Type': 'High-Rated Keyword'
                    })
                
                print("\n" + "-"*70)
                print("KEYWORDS THAT DIFFERENTIATE HIGH VS LOW RATED")
                print("-"*70)
                for idx in top_diff_indices[:15]:
                    keyword = features[idx]
                    high_score = high_tfidf_avg[idx]
                    low_score = low_tfidf_avg[idx]
                    diff = tfidf_diff[idx]
                    print(f"  - {keyword}: High={high_score:.4f}, Low={low_score:.4f}, Diff={diff:+.4f}")
                    
                    if keyword not in [p['Keyword'] for p in pattern_results]:
                        pattern_results.append({
                            'Keyword': keyword,
                            'High-Rated Score': round(high_score, 4),
                            'Low-Rated Score': round(low_score, 4),
                            'Difference': round(diff, 4),
                            'Pattern Type': 'Differentiating Keyword'
                        })
        
        # Export pattern analysis to CSV
        if pattern_results:
            patterns_df = pd.DataFrame(pattern_results)
            patterns_df = patterns_df.sort_values('Difference', ascending=False)
            patterns_df.to_csv('patterns_analysis.csv', index=False)
            print(f"\n✓ Pattern analysis saved to patterns_analysis.csv")
        
        # Prepare and train neural network
        features, targets, episode_ids = loader.prepare_neural_network_data(episode_df, character_df)
        
        model, losses = train_neural_network(features, targets, epochs=1000, learning_rate=0.001)
        
        # Save results
        print("\n" + "="*70)
        print("SAVING RESULTS")
        print("="*70)
        
        # Format character popularity with better column names
        char_export = char_popularity.copy()
        char_export = char_export.rename(columns={
            'character_id': 'Character ID',
            'character_name': 'Character Name',
            'species': 'Species',
            'num_episodes': 'Episode Count',
            'weighted_avg_rating': 'Avg Rating (Weighted)',
            'total_votes': 'Total IMDB Votes',
            'series': 'Series',
            'popularity_score': 'Popularity Score'
        })
        char_export['Avg Rating (Weighted)'] = char_export['Avg Rating (Weighted)'].round(2)
        char_export['Popularity Score'] = char_export['Popularity Score'].round(3)
        char_export.to_csv('character_popularity_analysis.csv', index=False)
        print("✓ Saved: character_popularity_analysis.csv")
        
        # Format species popularity with better column names
        species_export = species_popularity.copy()
        species_export = species_export.rename(columns={
            'species': 'Species',
            'num_characters': 'Character Count',
            'num_episodes': 'Episode Appearances',
            'weighted_avg_rating': 'Avg Rating (Weighted)',
            'total_votes': 'Total IMDB Votes',
            'popularity_score': 'Popularity Score'
        })
        species_export['Avg Rating (Weighted)'] = species_export['Avg Rating (Weighted)'].round(2)
        species_export['Popularity Score'] = species_export['Popularity Score'].round(3)
        species_export.to_csv('species_popularity_analysis.csv', index=False)
        print("✓ Saved: species_popularity_analysis.csv")
        
        # Format actor popularity with better column names
        actor_export = actor_popularity.copy()
        actor_export = actor_export.rename(columns={
            'actor_id': 'Actor ID',
            'actor_name': 'Actor Name',
            'num_episodes': 'Episode Count',
            'num_characters': 'Characters Played',
            'main_characters': 'Notable Characters',
            'weighted_avg_rating': 'Avg Rating (Weighted)',
            'total_votes': 'Total IMDB Votes',
            'series': 'Series',
            'popularity_score': 'Popularity Score'
        })
        actor_export['Avg Rating (Weighted)'] = actor_export['Avg Rating (Weighted)'].round(2)
        actor_export['Popularity Score'] = actor_export['Popularity Score'].round(3)
        actor_export.to_csv('actor_popularity_analysis.csv', index=False)
        print("✓ Saved: actor_popularity_analysis.csv")
        
        # Save model
        torch.save(model.state_dict(), 'startrek_analysis_model.pth')
        print("✓ Saved: startrek_analysis_model.pth")
        
        print("\n" + "="*70)
        print("ANALYSIS COMPLETE!")
        print("="*70)
        
    finally:
        loader.close()


if __name__ == "__main__":
    main()
