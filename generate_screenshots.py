import os
import copy
import json
import requests
import pandas as pd
import numpy as np
import folium
from html2image import Html2Image

# Ensure assets output directory exists
os.makedirs("assets", exist_ok=True)

# Initialize html2image headless renderer
hti = Html2Image(output_path="assets", size=(1200, 650))

# Load Summary Data
df = pd.read_csv('data/country_summary.csv')

COUNTRY_NAME_FIXES = {
    "Russia": "Russian Federation", "Czech Republic": "Czechia",
    "Venezuela": "Bolivarian Republic of Venezuela", "United States of America": "USA",
    "United Kingdom": "UK", "Korea, Republic of": "South Korea"
}

COLOR_PALETTE_HEX = [
    "#e6194B", "#3cb44b", "#ffe119", "#4363d8", "#f58231", 
    "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabed4"
]

GENRE_HEX = {
    "Drama": "#4363d8", "Comedy": "#ffe119", "Action": "#e6194B", 
    "Horror": "#800000", "Romance": "#fabed4", "Documentary": "#469990",
    "Animation": "#3cb44b", "Crime": "#911eb4", "Thriller": "#f58231",
    "Adventure": "#42d4f4", "Science Fiction": "#f032e6"
}

def get_hex_color(name):
    return COLOR_PALETTE_HEX[abs(hash(str(name))) % len(COLOR_PALETTE_HEX)]

GEOJSON_URL = "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/world-countries.json"
base_geojson = requests.get(GEOJSON_URL).json()

def prepare_geojson():
    res = copy.deepcopy(base_geojson)
    summary_dict = df.set_index('country').to_dict(orient='index')
    
    for feature in res['features']:
        orig_name = feature['properties']['name']
        cname = COUNTRY_NAME_FIXES.get(orig_name, orig_name)
        feature['properties']['country'] = cname
        
        if cname in summary_dict:
            d = summary_dict[cname]
            feature['properties']['top_movie'] = str(d['top_movie'])
            feature['properties']['top_genre'] = str(d['top_genre'])
            feature['properties']['top_genre_count'] = str(d['top_genre_count'])
            feature['properties']['total_movies'] = str(d['total_movies'])
            feature['properties']['ownership_status'] = "🟢 Domestic" if d['has_domestic_top_film'] else "🔴 Foreign Import"
            feature['properties']['hollywood_pct'] = f"{d['hollywood_pct']}%"
            feature['properties']['avg_top20_year'] = str(d['avg_top20_year'])
            feature['properties']['crime_score'] = f"{d['crime_score']}%"
            feature['properties']['darkness_score'] = f"{d['darkness_score']}%"
            feature['properties']['slow_cinema_pct'] = f"{d['slow_cinema_pct']}%"
            feature['properties']['futurism_score'] = f"{d['futurism_score']}%"
            feature['properties']['melodrama_score'] = f"{d['melodrama_score']}%"
            feature['properties']['avg_runtime'] = f"{d['avg_runtime']} mins"
            
            feature['properties']['movie_color'] = get_hex_color(str(d['top_movie']))
            feature['properties']['domestic_color'] = "#2ecc71" if d['has_domestic_top_film'] else "#e74c3c"
            feature['properties']['genre_color'] = GENRE_HEX.get(d['top_genre'], "#95a5a6")
            
            hw = min(d['hollywood_pct'] / 100.0, 1.0)
            feature['properties']['hollywood_color'] = f"#{int(255*hw):02x}{int(255*(1-hw)):02x}32"
            
            yr = d['avg_top20_year']
            feature['properties']['nostalgia_color'] = "#8e44ad" if yr < 1985 else ("#f1c40f" if yr > 2005 else "#3498db")
            
            cr_norm = min(max((d['crime_score'] - 10.0) / 25.0, 0.0), 1.0)
            feature['properties']['crime_color'] = f"#{int(240-60*cr_norm):02x}{int(180-60*cr_norm):02x}{int(190-30*cr_norm):02x}"
            
            dk = d['darkness_score'] / 100.0
            feature['properties']['darkness_color'] = f"#{int(240*(1-dk)+120*dk):02x}{int(200*(1-dk)):02x}{int(50*(1-dk)+200*dk):02x}"
            
            avg_rt = float(d['avg_runtime']) if str(d['avg_runtime']).replace('.', '').isdigit() else 100.0
            feature['properties']['slow_color'] = "#c8d7e6" if avg_rt <= 92 else ("#8a2be2" if avg_rt > 115 else "#4169e1")
            
            ft_val = d['futurism_score']
            feature['properties']['futurism_color'] = "#23262d" if ft_val <= 0.5 else ("#00f0f0" if ft_val > 4.5 else "#1e90ff")
            
            md_norm = min(max((d['melodrama_score'] - 15.0) / 20.0, 0.0), 1.0)
            feature['properties']['melodrama_color'] = f"#{int(250-30*md_norm):02x}{int(130-110*md_norm):02x}{int(170-130*md_norm):02x}"
        else:
            for key in ['movie_color', 'domestic_color', 'genre_color', 'hollywood_color', 'nostalgia_color', 'crime_color', 'darkness_color', 'slow_color', 'futurism_color', 'melodrama_color']:
                feature['properties'][key] = "#2a2a2a"
            
    return res

geojson_data = prepare_geojson()

def save_map_screenshot(color_prop, map_num):
    m = folium.Map(location=[20, 0], zoom_start=1.8, tiles="cartodbdarkmatter", no_wrap=True)
    folium.GeoJson(
        geojson_data,
        style_function=lambda f: {
            'fillColor': f['properties'].get(color_prop, '#2a2a2a'),
            'color': '#111111',
            'weight': 0.8,
            'fillOpacity': 0.8
        }
    ).add_to(m)
    
    html_path = f"assets/map{map_num}.html"
    png_filename = f"map{map_num}.png"
    m.save(html_path)
    
    # Convert HTML map to PNG image
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    hti.screenshot(html_str=html_content, save_as=png_filename)
    print(f"✅ Generated assets/map{map_num}.png")

print("Generating map screenshots for README...")
map_props = [
    'movie_color', 'domestic_color', 'movie_color', 'genre_color',
    'hollywood_color', 'nostalgia_color', 'crime_color', 'darkness_color',
    'movie_color', 'slow_color', 'futurism_color', 'melodrama_color'
]

for idx, prop in enumerate(map_props, start=1):
    save_map_screenshot(prop, idx)

print("🎉 All 12 screenshots successfully saved in the assets/ directory!")