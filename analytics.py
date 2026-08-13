import pandas as pd
import urllib.parse
import json

def calculate_country_metrics():
    df_prod = pd.read_csv('data/processed_movies.csv')
    df_rel = pd.read_csv('data/processed_releases.csv')
    
    # Filter for narrative feature-length films only (60 to 220 minutes)
    non_doc_prod = df_prod[~df_prod['genre'].str.contains('Documentary', na=False, case=False)]
    music_video_pattern = r'music video|official video|live at|concert|video clip|live in'
    is_mv_prod = non_doc_prod['name'].str.contains(music_video_pattern, na=False, case=False)
    feature_prod = non_doc_prod[~is_mv_prod & (non_doc_prod['minute'] >= 60) & (non_doc_prod['minute'] <= 220)].copy()

    non_doc_rel = df_rel[~df_rel['genre'].str.contains('Documentary', na=False, case=False)]
    is_mv_rel = non_doc_rel['name'].str.contains(music_video_pattern, na=False, case=False)
    feature_rel = non_doc_rel[~is_mv_rel & (non_doc_rel['minute'] >= 60) & (non_doc_rel['minute'] <= 220)].copy()

    # Dictionary mapping movie ID to set of production countries
    movie_production_origins = feature_prod.groupby('id')['country'].apply(set).to_dict()
    usa_movie_ids = set(feature_prod[feature_prod['country'] == 'USA']['id'])

    summary_data = []
    countries = feature_rel['country'].dropna().unique()

    # Build country-to-movie-set dictionary for Global Reach overlap counts
    country_movie_sets = {c: set(feature_rel[feature_rel['country'] == c]['id']) for c in countries}

    for country in countries:
        c_releases = feature_rel[feature_rel['country'] == country]
        c_prod = feature_prod[feature_prod['country'] == country]
        
        if c_releases.empty and c_prod.empty:
            continue
            
        base_df = c_releases if not c_releases.empty else c_prod
        
        # 1. Top Rated Movie Released in Country
        top_movie_row = base_df.sort_values(by='rating', ascending=False).iloc[0]
        top_movie_id = top_movie_row['id']
        prod_origins = movie_production_origins.get(top_movie_id, set())
        
        has_domestic_top_film = country in prod_origins
        
        # Top Directors (Minimum 3 movies threshold)
        director_stats = base_df.dropna(subset=['director']).groupby('director')['rating'].agg(['count', 'mean']).reset_index()
        qualified_directors = director_stats[director_stats['count'] >= 3]
        if qualified_directors.empty:
            qualified_directors = director_stats[director_stats['count'] >= 2]
        if qualified_directors.empty:
            qualified_directors = director_stats
            
        top_director_row = qualified_directors.sort_values(by='mean', ascending=False).iloc[0] if not qualified_directors.empty else None
        top_director = top_director_row['director'] if top_director_row is not None else "N/A"
        top_director_rating = round(top_director_row['mean'], 2) if top_director_row is not None else "N/A"
        top_director_count = int(top_director_row['count']) if top_director_row is not None else 0
        
        # Genres
        all_genres = base_df['genre'].dropna().str.split(', ').explode()
        top_genre = all_genres.mode()[0] if not all_genres.empty else "N/A"
        top_genre_count = int(sum(all_genres == top_genre)) if top_genre != "N/A" else 0
        genre_counts = all_genres.value_counts(normalize=True).to_dict()
        
        # Catalog Metrics
        peak_year_series = base_df['date'].dropna().astype(int).mode()
        peak_year = int(peak_year_series.iloc[0]) if not peak_year_series.empty else "N/A"
        avg_runtime = int(base_df['minute'].dropna().mean()) if not base_df['minute'].dropna().empty else "N/A"
        avg_country_rating = round(base_df['rating'].dropna().mean(), 2) if not base_df['rating'].dropna().empty else "N/A"
        
        # Hollywood Dependence Index
        c_movie_ids = set(base_df['id'])
        hollywood_count = len(c_movie_ids.intersection(usa_movie_ids))
        hollywood_pct = round((hollywood_count / len(c_movie_ids)) * 100, 1) if c_movie_ids else 0.0
        
        # The Nostalgia Index
        top20_movies = base_df.sort_values(by='rating', ascending=False).head(20)
        avg_top20_year = int(top20_movies['date'].dropna().mean()) if not top20_movies['date'].dropna().empty else 2000
        
        # The Sin City / Crime Index
        crime_genres = {'Crime', 'Action', 'Thriller', 'Mystery'}
        crime_count = sum(all_genres.isin(crime_genres))
        crime_score = round((crime_count / len(all_genres)) * 100, 1) if len(all_genres) > 0 else 0.0
        
        # The Darkness Index
        dark_genres = {'Horror', 'Thriller', 'Crime', 'Mystery'}
        light_genres = {'Comedy', 'Animation', 'Family', 'Romance'}
        dark_count = sum(all_genres.isin(dark_genres))
        light_count = sum(all_genres.isin(light_genres))
        total_dl = dark_count + light_count
        darkness_score = round((dark_count / total_dl) * 100, 1) if total_dl > 0 else 50.0
        
        # Arthouse vs. Blockbuster Index
        arthouse_genres = {'Drama', 'History', 'War'}
        blockbuster_genres = {'Action', 'Adventure', 'Science Fiction'}
        arthouse_count = sum(all_genres.isin(arthouse_genres))
        blockbuster_count = sum(all_genres.isin(blockbuster_genres))
        total_ab = arthouse_count + blockbuster_count
        arthouse_score = round((arthouse_count / total_ab) * 100, 1) if total_ab > 0 else 50.0

        # Slow Cinema / Patience Index (% of movies >= 140 mins)
        long_movies_count = len(base_df[base_df['minute'] >= 140])
        slow_cinema_pct = round((long_movies_count / len(base_df)) * 100, 1) if len(base_df) > 0 else 0.0

        # Futurism & Cyberpunk Index (% Sci-Fi)
        scifi_count = sum(all_genres == 'Science Fiction')
        futurism_score = round((scifi_count / len(all_genres)) * 100, 1) if len(all_genres) > 0 else 0.0

        # Tears & Melodrama Index (% Romance + Drama)
        melodrama_genres = {'Romance', 'Drama'}
        melodrama_count = sum(all_genres.isin(melodrama_genres))
        melodrama_score = round((melodrama_count / len(all_genres)) * 100, 1) if len(all_genres) > 0 else 0.0

        # Global Reach Overlap Counts
        reach_counts = {}
        for other_c, other_set in country_movie_sets.items():
            if other_c != country:
                overlap = len(c_movie_ids.intersection(other_set))
                if overlap > 0:
                    reach_counts[other_c] = overlap
        
        # Letterboxd Search URLs
        movie_url = f"https://letterboxd.com/search/{urllib.parse.quote(str(top_movie_row['name']))}/"
        director_url = f"https://letterboxd.com/search/{urllib.parse.quote(str(top_director))}/"
        genre_url = f"https://letterboxd.com/search/{urllib.parse.quote(str(top_genre))}/"
        
        top_10_movies = base_df.sort_values(by='rating', ascending=False).head(10)[['name', 'date', 'rating']].to_dict(orient='records')
        top_10_directors = qualified_directors.sort_values(by='mean', ascending=False).head(10)[['director', 'count', 'mean']].to_dict(orient='records')
        
        yearly_counts = base_df[base_df['date'] >= 1900].groupby('date')['id'].nunique().reset_index()
        yearly_counts.columns = ['year', 'count']
        yearly_trend = yearly_counts.to_dict(orient='records')

        summary_data.append({
            'country': country,
            'total_movies': len(base_df),
            'avg_country_rating': avg_country_rating,
            'avg_runtime': avg_runtime,
            'peak_year': peak_year,
            'top_movie': top_movie_row['name'],
            'top_movie_year': int(top_movie_row['date']) if pd.notnull(top_movie_row['date']) else "N/A",
            'top_movie_rating': top_movie_row['rating'],
            'top_movie_poster': top_movie_row['link'],
            'top_movie_url': movie_url,
            'has_domestic_top_film': has_domestic_top_film,
            'top_director': top_director,
            'top_director_rating': top_director_rating,
            'top_director_count': top_director_count,
            'top_director_url': director_url,
            'top_genre': top_genre,
            'top_genre_count': top_genre_count,
            'top_genre_url': genre_url,
            'hollywood_pct': hollywood_pct,
            'avg_top20_year': avg_top20_year,
            'crime_score': crime_score,
            'darkness_score': darkness_score,
            'arthouse_score': arthouse_score,
            'slow_cinema_pct': slow_cinema_pct,
            'futurism_score': futurism_score,
            'melodrama_score': melodrama_score,
            'genre_distribution': json.dumps(genre_counts),
            'global_reach_counts': json.dumps(reach_counts),
            'top_10_movies': json.dumps(top_10_movies),
            'top_10_directors': json.dumps(top_10_directors),
            'yearly_trend': json.dumps(yearly_trend)
        })

    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv('data/country_summary.csv', index=False)
    print(f"Analytics complete: {len(summary_df)} countries saved to 'data/country_summary.csv'.")

if __name__ == '__main__':
    calculate_country_metrics()