import os
import copy
import json
import requests
import pandas as pd
import numpy as np
import folium
from html2image import Html2Image

# Ensure output directory exists
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

def build_legend_html(title, items_or_gradient):
    """Generate floating dark-mode legend overlay box for Folium maps."""
    body_content = ""
    
    if isinstance(items_or_gradient, list):
        # List of items: [("Label", "#color_hex"), ...]
        items_html = "".join([
            f"<div style='display:flex; align-items:center; margin-bottom:4px;'>"
            f"<span style='background:{color}; display:inline-block; width:12px; height:12px; border-radius:3px; margin-right:8px;'></span>"
            f"<span>{label}</span></div>"
            for label, color in items_or_gradient
        ])
        body_content = items_html
    elif isinstance(items_or_gradient, dict):
        # Gradient bar specs: {'min': '0%', 'max': '100%', 'colors': 'linear-gradient(...)', 'mid': '50%'}
        g = items_or_gradient
        mid_label = f"<span>{g['mid']}</span>" if 'mid' in g else ""
        body_content = f"""
        <div style="margin-top: 6px;">
            <div style="height: 12px; border-radius: 4px; background: {g['colors']}; margin-bottom: 4px;"></div>
            <div style="display: flex; justify-content: space-between; font-size: 10px; color: #bbbbbb;">
                <span>{g['min']}</span>
                {mid_label}
                <span>{g['max']}</span>
            </div>
        </div>
        """

    return f"""
    <div style="
        position: fixed; 
        bottom: 30px; 
        left: 30px; 
        z-index: 9999; 
        background-color: rgba(20, 24, 28, 0.92); 
        color: #ffffff; 
        padding: 10px 14px; 
        border-radius: 8px; 
        border: 1px solid #444444; 
        font-family: sans-serif; 
        font-size: 11px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        max-width: 280px;
    ">
        <b style="font-size: 12px; color: #ffb400; display: block; margin-bottom: 6px;">{title}</b>
        {body_content}
    </div>
    """

def get_map_legend(map_num):
    if map_num == 1:
        # Top movies across nations
        top_movies = df['top_movie'].value_counts().head(6).index.tolist()
        items = [(m[:22] + "..." if len(m) > 22 else m, get_hex_color(m)) for m in top_movies]
        items.append(("Other Films", "#95a5a6"))
        return build_legend_html("🏆 Top Film Color Legend", items)
    
    elif map_num == 2:
        items = [("Domestic / Co-Production", "#2ecc71"), ("Foreign Import", "#e74c3c")]
        return build_legend_html("🟢 Origin Status", items)
    
    elif map_num == 3:
        g = {'min': '0 Shared', 'mid': '100', 'max': '20,000+ Shared', 'colors': 'linear-gradient(to right, #1e3c5a, #2ecc71, #f1c40f)'}
        return build_legend_html("🌐 Shared Movie Catalog Scale", g)
    
    elif map_num == 4:
        items = [(g, c) for g, c in GENRE_HEX.items()]
        return build_legend_html("🎭 Dominant Genre", items)
    
    elif map_num == 5:
        g = {'min': '0% (Sovereign)', 'mid': '50%', 'max': '100% (US Dominated)', 'colors': 'linear-gradient(to right, #2ecc71, #f1c40f, #e74c3c)'}
        return build_legend_html("🇺🇸 Hollywood Share %", g)
    
    elif map_num == 6:
        items = [("Pre-1985 (Classic Era)", "#8e44ad"), ("1985–2005 (Balanced)", "#3498db"), ("Post-2005 (Modern Era)", "#f1c40f")]
        return build_legend_html("🕰️ Avg Top 20 Film Era", items)
    
    elif map_num == 7:
        g = {'min': '10% (Low Crime)', 'mid': '22%', 'max': '35%+ (High Crime)', 'colors': 'linear-gradient(to right, #f0f0f5, #b4b4be, #e67e22, #e74c3c)'}
        return build_legend_html("🚨 Crime/Action Share %", g)
    
    elif map_num == 8:
        g = {'min': '0% (Lighthearted)', 'mid': '50%', 'max': '100% (Dark / Horror)', 'colors': 'linear-gradient(to right, #f1c40f, #e67e22, #8e44ad)'}
        return build_legend_html("💀 Dark Genre Ratio %", g)
    
    elif map_num == 9:
        g = {'min': '70% (Low Match)', 'mid': '85%', 'max': '100% (Taste Twin)', 'colors': 'linear-gradient(to right, #f5f5f5, #8c8c8c, #2ecc71)'}
        return build_legend_html("🎯 Taste Similarity %", g)
    
    elif map_num == 10:
        items = [("≤ 92 mins (Fast-Paced)", "#c8d7e6"), ("93–115 mins (Standard)", "#4169e1"), ("116+ mins (Slow Cinema Epic)", "#8a2be2")]
        return build_legend_html("⏳ Avg Movie Runtime", items)
    
    elif map_num == 11:
        g = {'min': '0% (No Sci-Fi)', 'mid': '3.0%', 'max': '6.5%+ (Cyberpunk Focus)', 'colors': 'linear-gradient(to right, #23262d, #1e90ff, #00f0f0)'}
        return build_legend_html("🛸 Sci-Fi Share %", g)
    
    elif map_num == 12:
        g = {'min': '15% (Low)', 'mid': '25%', 'max': '35%+ (High Romance/Drama)', 'colors': 'linear-gradient(to right, #ffffff, #ffb6c1, #e74c3c)'}
        return build_legend_html("💔 Romance & Drama Share %", g)

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
    
    # Inject legend HTML overlay
    legend_code = get_map_legend(map_num)
    m.get_root().html.add_child(folium.Element(legend_code))
    
    html_path = f"assets/map{map_num}.html"
    png_filename = f"map{map_num}.png"
    m.save(html_path)
    
    # Convert HTML map to PNG image
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    hti.screenshot(html_str=html_content, save_as=png_filename)
    print(f"✅ Generated assets/map{map_num}.png with custom legend")

print("Generating map screenshots with dark-mode legends for README...")
map_props = [
    'movie_color', 'domestic_color', 'movie_color', 'genre_color',
    'hollywood_color', 'nostalgia_color', 'crime_color', 'darkness_color',
    'movie_color', 'slow_color', 'futurism_color', 'melodrama_color'
]

for idx, prop in enumerate(map_props, start=1):
    save_map_screenshot(prop, idx)

print("🎉 All 12 screenshots with legends successfully saved in the assets/ directory!")