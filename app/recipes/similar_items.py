import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import Recipe

# Dummy function to clean the R-style string
def clean_keywords(text):
    if pd.isna(text):
        return ""
    # Remove c( at the start and ) at the end
    cleaned = re.sub(r'^c\(|\)$', '', text)
    # Remove all double quotes and commas
    cleaned = cleaned.replace('"', '').replace(',', '')
    # Optional: replace spaces inside tags (e.g., "Low Protein" -> "Low_Protein")
    # so CountVectorizer treats it as a single token
    return cleaned.strip()


def create_soup_metadata_df(df):
    '''
    Expecting an input of "recipes_augmented.csv"
    '''
    data = df.copy()
    # Applying clean words function to the data
    data['cleaned_keywords'] = data['keywords'].apply(clean_keywords)

    # Replace spaces in category so "Main Dish" becomes "Main_Dish"
    data['clean_category'] = data['category'].fillna('').str.replace(' ', '_')

    # Combine them into a single metadata string
    data['metadata_soup'] = data['clean_category'] + " " + data['cleaned_keywords']

    return data

def fit_tfidf(df):
    '''
    Expecting an input of "recipes_augmented.csv"
    '''
    data = df.copy()

    new_data = create_soup_metadata_df(data)

    # 1. Vectorize the text soup
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(new_data['metadata_soup'])

    dense_matrix = tfidf_matrix.toarray()
    feature_names = tfidf.get_feature_names_out()
    df = pd.DataFrame(dense_matrix, columns=feature_names)
    df.to_csv("tfidf_matrix.csv", index=False)

    return tfidf, tfidf_matrix

def get_recommendations(id, tfidf_matrix, indices, top_n=10):
    """
    Takes a recipe title, computes its similarity against all other recipes,
    and returns the top_n most similar recipes.
    """
    # Check if the recipe exists in our dataset
    if id not in indices:
        return f"Recipe '{id}' not found in the dataset."
    
    # Get the row index of our target recipe
    idx = indices[id]
    
    # Extract the TF-IDF vector for this specific recipe
    target_vector = tfidf_matrix[idx]
    
    # Compute similarity between this recipe and ALL recipes in the matrix
    sim_scores = cosine_similarity(target_vector, tfidf_matrix).flatten()
    
    # Get the indices of the highest scores (excluding the recipe itself)
    similar_indices = sim_scores.argsort()[-(top_n+1):-1][::-1]
    #Maps the TF-IDF indices to the recipe IDs, and returns the most similar recipes
    return indices[indices.isin(similar_indices)].index.values


if __name__ == "__main__":
    # Path to your data (Use a smaller nrows sample first for testing!)
    DATA_PATH = "data/recipes_augmented.csv"
    
    print("Loading dataset...")
    # Loading 20,000 rows to keep memory usage safe during testing
    recipes_sample = pd.read_csv(DATA_PATH, nrows=20000)
    
    print("Building TF-IDF features...")
    tfidf_vectorizer, tfidf_matrix = fit_tfidf(recipes_sample)
    
    print("Creating lookup indices...")
    # Building the lookup dynamically inside runtime rather than globally
    recipe_indices = pd.Series(recipes_sample.index, index=recipes_sample['RecipeId']).drop_duplicates()
    
    # Test example
    # Replace this string with an exact recipe Name present in your first 20,000 rows
    test_recipe = recipes_sample['RecipeId'].iloc[0]
    
    print(f"\nGenerating recommendations for: '{test_recipe}'")
    results = get_recommendations(test_recipe, tfidf_matrix, recipes_sample, recipe_indices, top_n=5)
    
    print("\n--- Top Results ---")
    print(results)
