import pandas as pd

def load_raw_data():
    movies = pd.read_csv('data/movies.csv')
    countries = pd.read_csv('data/countries.csv')
    crew = pd.read_csv('data/crew.csv')
    genres = pd.read_csv('data/genres.csv')
    posters = pd.read_csv('data/posters.csv')
    releases = pd.read_csv('data/releases.csv')
    
    try:
        languages = pd.read_csv('data/languages.csv')
    except Exception:
        languages = None
        
    return movies, countries, crew, genres, posters, releases, languages

def process_and_merge():
    movies, countries, crew, genres, posters, releases, languages = load_raw_data()

    # Filter directors individually
    directors = crew[crew['role'] == 'Director'][['id', 'name']].rename(columns={'name': 'director'})

    # Aggregate genres per movie
    movie_genres = genres.groupby('id')['genre'].apply(lambda x: ', '.join(x)).reset_index()

    # Calculate language counts per movie (polyglot indicator)
    if languages is not None:
        lang_counts = languages.groupby('id')['language'].nunique().reset_index().rename(columns={'language': 'language_count'})
    else:
        lang_counts = pd.DataFrame({'id': movies['id'], 'language_count': 1})

    # Clean missing ratings or titles
    clean_movies = movies.dropna(subset=['rating', 'name']).copy()

    # Merge production countries dataset
    df_prod = clean_movies.merge(countries, on='id', how='inner')
    df_prod = df_prod.merge(directors, on='id', how='left')
    df_prod = df_prod.merge(movie_genres, on='id', how='left')
    df_prod = df_prod.merge(posters, on='id', how='left')
    df_prod = df_prod.merge(lang_counts, on='id', how='left')
    df_prod['language_count'] = df_prod['language_count'].fillna(1)
    df_prod.to_csv('data/processed_movies.csv', index=False)

    # Merge releases dataset
    df_rel = clean_movies.merge(releases[['id', 'country']].drop_duplicates(), on='id', how='inner')
    df_rel = df_rel.merge(directors, on='id', how='left')
    df_rel = df_rel.merge(movie_genres, on='id', how='left')
    df_rel = df_rel.merge(posters, on='id', how='left')
    df_rel = df_rel.merge(lang_counts, on='id', how='left')
    df_rel['language_count'] = df_rel['language_count'].fillna(1)
    df_rel.to_csv('data/processed_releases.csv', index=False)

    print(f"Processing complete: Saved 'data/processed_movies.csv' and 'data/processed_releases.csv'.")

if __name__ == '__main__':
    process_and_merge()