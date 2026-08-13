import pandas as pd
import requests

def inspect_countries():
    # Load processed movies
    df = pd.read_csv('data/processed_movies.csv')
    processed_countries = set(df['country'].dropna().unique())

    print(f"Total unique countries in processed dataset: {len(processed_countries)}")

    # Fetch GeoJSON country names
    geojson_url = "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/world-countries.json"
    response = requests.get(geojson_url).json()
    geojson_countries = set(f['properties']['name'] for f in response['features'])

    # Target countries to inspect
    target_keywords = ['russia', 'czech', 'congo', 'gabon', 'venezuela', 'turkmen', 'macedonia', 'serbia']

    print("\n--- DATASET VS GEOJSON MATCH INSPECTION ---")
    for kw in target_keywords:
        dataset_matches = [c for c in processed_countries if kw in str(c).lower()]
        geojson_matches = [g for g in geojson_countries if kw in str(g).lower()]
        print(f"Keyword '{kw.upper()}':")
        print(f"  In Dataset: {dataset_matches}")
        print(f"  In GeoJSON: {geojson_matches}\n")

if __name__ == '__main__':
    inspect_countries()