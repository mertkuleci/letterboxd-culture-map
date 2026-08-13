import streamlit as st
import pandas as pd
import json
import requests
import folium
from streamlit_folium import st_folium
import numpy as np
import copy

st.set_page_config(page_title="Letterboxd World Cinema Dashboard | mertkuleci", layout="wide", initial_sidebar_state="collapsed")

# Mobile Responsive CSS
st.markdown("""
    <style>
        .main .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
            max-width: 100% !important;
        }
        iframe {
            max-width: 100% !important;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_summary():
    return pd.read_csv('data/country_summary.csv')

df = load_summary()

min_data_year = 1900
max_data_year = int(df['top_movie_year'].dropna().astype(str).str.extract(r'(\d{4})')[0].max()) if 'top_movie_year' in df.columns else 2024

COUNTRY_NAME_FIXES = {
    "Russia": "Russian Federation",
    "Russian Federation": "Russian Federation",
    "Czech Republic": "Czechia",
    "Czech Rep.": "Czechia",
    "Venezuela": "Bolivarian Republic of Venezuela",
    "Democratic Republic of the Congo": "Democratic Republic of Congo",
    "Dem. Rep. Congo": "Democratic Republic of Congo",
    "Republic of the Congo": "Congo",
    "Congo": "Congo",
    "Macedonia": "North Macedonia",
    "Republic of Serbia": "Serbia",
    "United States of America": "USA",
    "United States": "USA",
    "United Kingdom": "UK",
    "Korea, Republic of": "South Korea",
    "Republic of Korea": "South Korea",
    "Dem. Rep. Korea": "North Korea",
    "Bosnia and Herz.": "Bosnia and Herzegovina",
    "Syrian Arab Republic": "Syria",
    "Islamic Republic of Iran": "Iran",
    "Viet Nam": "Vietnam",
    "Lao PDR": "Laos",
    "Central African Rep.": "Central African Republic",
    "Eq. Guinea": "Equatorial Guinea",
    "S. Sudan": "South Sudan",
    "United Republic of Tanzania": "Tanzania",
    "Eswatini": "Swaziland",
    "Moldova": "Moldova",
    "Republic of Moldova": "Moldova",
    "Guyana": "Guyana",
    "Honduras": "Honduras",
    "Somalia": "Somalia",
    "Somaliland": "Somalia",
    "Gabon": "Gabon",
    "Turkmenistan": "Turkmenistan"
}

COLOR_PALETTE_HEX = [
    "#e6194B", "#3cb44b", "#ffe119", "#4363d8", "#f58231", 
    "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabed4", 
    "#469990", "#dcbeff", "#9A6324", "#fffac8", "#800000"
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

@st.cache_data
def fetch_base_geojson():
    return requests.get(GEOJSON_URL).json()

@st.cache_data
def prepare_geojson():
    res = copy.deepcopy(fetch_base_geojson())
    summary_dict = df.set_index('country').to_dict(orient='index')
    
    for feature in res['features']:
        orig_name = feature['properties']['name']
        cname = COUNTRY_NAME_FIXES.get(orig_name, orig_name)
        feature['properties']['country'] = cname
        
        if cname in summary_dict:
            d = summary_dict[cname]
            feature['properties']['top_movie'] = str(d['top_movie'])
            feature['properties']['top_movie_year'] = str(d['top_movie_year'])
            feature['properties']['top_movie_rating'] = f"★ {d['top_movie_rating']}"
            feature['properties']['top_director'] = str(d['top_director'])
            feature['properties']['top_director_rating'] = f"★ {d['top_director_rating']}"
            feature['properties']['top_genre'] = str(d['top_genre'])
            feature['properties']['top_genre_count'] = str(d['top_genre_count'])
            feature['properties']['total_movies'] = str(d['total_movies'])
            feature['properties']['avg_country_rating'] = f"★ {d['avg_country_rating']}"
            feature['properties']['avg_runtime'] = f"{d['avg_runtime']} mins"
            feature['properties']['ownership_status'] = "🟢 Domestic / Co-Production" if d['has_domestic_top_film'] else "🔴 Foreign Import"
            feature['properties']['hollywood_pct'] = f"{d['hollywood_pct']}%"
            feature['properties']['avg_top20_year'] = str(d['avg_top20_year'])
            feature['properties']['crime_score'] = f"{d['crime_score']}%"
            feature['properties']['darkness_score'] = f"{d['darkness_score']}%"
            feature['properties']['arthouse_score'] = f"{d['arthouse_score']}%"
            feature['properties']['slow_cinema_pct'] = f"{d['slow_cinema_pct']}%"
            feature['properties']['futurism_score'] = f"{d['futurism_score']}%"
            feature['properties']['melodrama_score'] = f"{d['melodrama_score']}%"
            
            # Map Base Colors in Hex
            feature['properties']['movie_color'] = get_hex_color(str(d['top_movie']))
            feature['properties']['domestic_color'] = "#2ecc71" if d['has_domestic_top_film'] else "#e74c3c"
            feature['properties']['genre_color'] = GENRE_HEX.get(d['top_genre'], "#95a5a6")
            
            # Hollywood scale
            hw = min(d['hollywood_pct'] / 100.0, 1.0)
            feature['properties']['hollywood_color'] = f"#{int(255*hw):02x}{int(255*(1-hw)):02x}32"
            
            # Nostalgia scale
            yr = d['avg_top20_year']
            if yr < 1985:
                feature['properties']['nostalgia_color'] = "#8e44ad"
            elif yr > 2005:
                feature['properties']['nostalgia_color'] = "#f1c40f"
            else:
                feature['properties']['nostalgia_color'] = "#3498db"
                
            # Crime scale (10%-35%)
            cr_norm = min(max((d['crime_score'] - 10.0) / 25.0, 0.0), 1.0)
            if cr_norm <= 0.25:
                t = cr_norm / 0.25
                feature['properties']['crime_color'] = f"#{int(240-60*t):02x}{int(240-60*t):02x}{int(245-55*t):02x}"
            elif cr_norm <= 0.65:
                t = (cr_norm - 0.25) / 0.40
                feature['properties']['crime_color'] = f"#{int(180+60*t):02x}{int(180-60*t):02x}{int(190-30*t):02x}"
            else:
                t = (cr_norm - 0.65) / 0.35
                feature['properties']['crime_color'] = f"#{int(240-20*t):02x}{int(120-100*t):02x}{int(160-110*t):02x}"

            # Darkness scale
            dk = d['darkness_score'] / 100.0
            feature['properties']['darkness_color'] = f"#{int(240*(1-dk)+120*dk):02x}{int(200*(1-dk)):02x}{int(50*(1-dk)+200*dk):02x}"
            
            # Slow Cinema scale
            avg_rt = float(d['avg_runtime']) if str(d['avg_runtime']).replace('.', '').isdigit() else 100.0
            if avg_rt <= 92:
                feature['properties']['slow_color'] = "#c8d7e6"
            elif avg_rt <= 102:
                t = (avg_rt - 92) / 10.0
                feature['properties']['slow_color'] = f"#{int(200-100*t):02x}{int(215-95*t):02x}{int(230-30*t):02x}"
            elif avg_rt <= 115:
                t = (avg_rt - 102) / 13.0
                feature['properties']['slow_color'] = f"#{int(100+40*t):02x}{int(120-70*t):02x}{int(200+10*t):02x}"
            else:
                t = min((avg_rt - 115) / 15.0, 1.0)
                feature['properties']['slow_color'] = f"#{int(140+80*t):02x}{int(50-30*t):02x}{int(210+35*t):02x}"

            # Futurism scale
            ft_val = d['futurism_score']
            if ft_val <= 0.5:
                feature['properties']['futurism_color'] = "#23262d"
            elif ft_val <= 2.0:
                t = (ft_val - 0.5) / 1.5
                feature['properties']['futurism_color'] = f"#{int(20+30*t):02x}{int(60+80*t):02x}{int(140+60*t):02x}"
            elif ft_val <= 4.5:
                t = (ft_val - 2.0) / 2.5
                feature['properties']['futurism_color'] = f"#{int(50-50*t):02x}{int(140+100*t):02x}{int(200+40*t):02x}"
            else:
                t = min((ft_val - 4.5) / 2.5, 1.0)
                feature['properties']['futurism_color'] = f"#{int(0+100*t):02x}{int(240+15*t):02x}{int(240-40*t):02x}"

            # Melodrama scale
            md_norm = min(max((d['melodrama_score'] - 15.0) / 20.0, 0.0), 1.0)
            if md_norm <= 0.5:
                t = md_norm / 0.5
                feature['properties']['melodrama_color'] = f"#fa{int(250-120*t):02x}{int(250-80*t):02x}"
            else:
                t = (md_norm - 0.5) / 0.5
                feature['properties']['melodrama_color'] = f"#{int(250-30*t):02x}{int(130-110*t):02x}{int(170-130*t):02x}"
        else:
            feature['properties']['top_movie'] = "N/A"
            feature['properties']['top_movie_year'] = "N/A"
            feature['properties']['top_movie_rating'] = "N/A"
            feature['properties']['top_director'] = "N/A"
            feature['properties']['top_director_rating'] = "N/A"
            feature['properties']['top_genre'] = "N/A"
            feature['properties']['top_genre_count'] = "0"
            feature['properties']['total_movies'] = "0"
            feature['properties']['avg_country_rating'] = "N/A"
            feature['properties']['avg_runtime'] = "N/A"
            feature['properties']['ownership_status'] = "No Data"
            feature['properties']['hollywood_pct'] = "N/A"
            feature['properties']['avg_top20_year'] = "N/A"
            feature['properties']['crime_score'] = "N/A"
            feature['properties']['darkness_score'] = "N/A"
            feature['properties']['slow_cinema_pct'] = "N/A"
            feature['properties']['futurism_score'] = "N/A"
            feature['properties']['melodrama_score'] = "N/A"
            
            for key in ['movie_color', 'domestic_color', 'genre_color', 'hollywood_color', 'nostalgia_color', 'crime_color', 'darkness_color', 'slow_color', 'futurism_color', 'melodrama_color']:
                feature['properties'][key] = "#2a2a2a"
            
    return res

geojson_data = prepare_geojson()

def build_folium_map(color_prop, tooltip_fields, tooltip_aliases, map_key, custom_geojson=None):
    m = folium.Map(
        location=[20, 0],
        zoom_start=1.8,
        tiles="cartodbdarkmatter",
        min_zoom=1.2,
        max_zoom=6,
        no_wrap=True
    )
    
    folium.GeoJson(
        custom_geojson or geojson_data,
        style_function=lambda feature: {
            'fillColor': feature['properties'].get(color_prop, '#2a2a2a'),
            'color': '#111111',
            'weight': 0.8,
            'fillOpacity': 0.8
        },
        highlight_function=lambda feature: {
            'weight': 2,
            'color': '#ffffff',
            'fillOpacity': 0.95
        },
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            sticky=True,
            style="background-color: rgba(20, 24, 28, 0.95); color: #ffffff; border: 1px solid #444444; border-radius: 6px; padding: 8px; font-family: sans-serif; font-size: 12px;"
        )
    ).add_to(m)
    
    st_folium(m, use_container_width=True, height=480, key=map_key, returned_objects=[])

# --- HEADER SECTION ---
col_head, col_brand = st.columns([3, 1])

with col_head:
    st.title("🎬 Letterboxd World Cinema Dashboard")
    st.caption(f"📅 **Dataset Coverage:** Archive spanning **{min_data_year} – {max_data_year}** (Letterboxd & TMDb Metadata Snapshot)")

with col_brand:
    st.markdown(
        """
        <div style="text-align: right; padding-top: 10px; font-family: sans-serif; font-size: 13px; color: #aaaaaa;">
            Created by <a href="https://github.com/mertkuleci" target="_blank" style="color: #00e054; text-decoration: none; font-weight: bold;">mertkuleci ↗</a><br>
            <a href="https://letterboxd.com" target="_blank" style="color: #ffb400; text-decoration: none; font-weight: bold;">
                Letterboxd ↗
            </a> | 
            <a href="https://www.kaggle.com/datasets" target="_blank" style="color: #20beff; text-decoration: none; font-weight: bold;">
                Dataset ↗
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs([
    "1. World Favorites", 
    "2. Domestic vs Foreign", 
    "3. Spotlight & Global Reach", 
    "4. Genre Capitals",
    "5. Hollywood Dependence",
    "6. The Nostalgia Index",
    "7. Sin City & Crime",
    "8. The Darkness Index",
    "9. Taste Twin Finder",
    "10. Slow Cinema Index",
    "11. Futurism & Cyberpunk",
    "12. Tears & Melodrama"
])

# -----------------------------------------------------------------------------
# TAB 1: World Cinema
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("Map 1: Favorite Feature Films Worldwide")
    st.caption(r"📐 **How it's calculated:** Identifies the highest Letterboxd-rated feature film (60-220 min) released in each nation's catalog. Countries that share the exact same top film share the exact same color.")
    build_folium_map(
        'movie_color',
        ['country', 'top_movie', 'top_movie_year', 'top_movie_rating', 'top_director', 'top_director_rating', 'top_genre', 'total_movies', 'avg_country_rating'],
        ['Country:', 'Top Film:', 'Year:', 'Rating:', 'Top Director:', 'Director Rating:', 'Genre:', 'Catalog Size:', 'Average Rating:'],
        'm1'
    )

# -----------------------------------------------------------------------------
# TAB 2: Domestic vs Foreign
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("Map 2: Favorite Released Movie - Domestic vs Foreign Origin")
    st.caption(r"📐 **How it's calculated:** Cross-references distribution country with production country. Green = domestic/co-production; Red = foreign import.")
    build_folium_map(
        'domestic_color',
        ['country', 'ownership_status', 'top_movie', 'top_movie_year', 'top_movie_rating'],
        ['Country:', 'Status:', 'Top Film:', 'Year:', 'Rating:'],
        'm2'
    )

# -----------------------------------------------------------------------------
# TAB 3: Country Spotlight & Reach
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("Map 3: Country Spotlight & Global Distribution Reach")
    st.caption(r"📐 **How it's calculated:** Ranks top 10 films and directors. Global Reach map calculates catalog overlap ($\text{Shared Movies} = |M_A \cap M_B|$) with a logarithmic color scale from 0 to 20,000+ shared titles.")
    
    sorted_countries = sorted(df['country'].dropna().unique().tolist())
    selected_c = st.selectbox("Search & Select Country:", sorted_countries, index=sorted_countries.index("Turkey") if "Turkey" in sorted_countries else 0)
    
    summary_dict = df.set_index('country').to_dict(orient='index')
    
    if selected_c in summary_dict:
        c_data = summary_dict[selected_c]
        reach_map = json.loads(c_data['global_reach_counts'])
        
        col_a, col_b = st.columns([1, 1])
        
        with col_a:
            st.write("### 🎬 Top 10 Directors (Min. 3 Movies)")
            top_d_list = json.loads(c_data['top_10_directors'])
            st.dataframe(pd.DataFrame(top_d_list).rename(columns={'director': 'Director', 'count': 'Movie Count', 'mean': 'Average Rating'}))

            st.write("### 🏆 Top 10 Highest Rated Movies")
            top_m_list = json.loads(c_data['top_10_movies'])
            st.dataframe(pd.DataFrame(top_m_list).rename(columns={'name': 'Movie Name', 'date': 'Year', 'rating': 'Average Rating'}))

        with col_b:
            st.write("### 📈 Movie Production Output per Year (1900 - Present)")
            yearly_data = json.loads(c_data['yearly_trend'])
            if yearly_data:
                yearly_df = pd.DataFrame(yearly_data).set_index('year')
                st.line_chart(yearly_df)

            st.write("### 🌐 Global Reach Map (Shared movie scale with " + selected_c + ")")
            
            reach_geojson = copy.deepcopy(fetch_base_geojson())
            for feature in reach_geojson['features']:
                orig = feature['properties']['name']
                cn = COUNTRY_NAME_FIXES.get(orig, orig)
                feature['properties']['country'] = cn
                cnt = reach_map.get(cn, 0)
                feature['properties']['shared_count'] = str(cnt)
                
                if cn == selected_c:
                    feature['properties']['reach_color'] = "#ffb400"
                elif cnt > 0:
                    r_norm = min(np.log1p(cnt) / np.log1p(20000.0), 1.0)
                    feature['properties']['reach_color'] = f"#{int(30+150*r_norm):02x}{int(60+195*r_norm):02x}{int(90-40*r_norm):02x}"
                else:
                    feature['properties']['reach_color'] = "#2a2a2a"

            build_folium_map(
                'reach_color',
                ['country', 'shared_count'],
                ['Country:', 'Shared Catalog Movies:'],
                'm3',
                custom_geojson=reach_geojson
            )

# -----------------------------------------------------------------------------
# TAB 4: Genre Capitals
# -----------------------------------------------------------------------------
with tab4:
    st.subheader("Map 4: Dominant Genre Capitals of the World")
    st.caption(r"📐 **How it's calculated:** Most frequent genre entry across all feature films in each country's catalog.")
    build_folium_map(
        'genre_color',
        ['country', 'top_genre', 'top_genre_count', 'total_movies'],
        ['Country:', 'Top Genre:', 'Movie Count:', 'Total Catalog:'],
        'm4'
    )

# -----------------------------------------------------------------------------
# TAB 5: Hollywood Dependence
# -----------------------------------------------------------------------------
with tab5:
    st.subheader("Map 5: Hollywood Dependence Index")
    st.caption(r"📐 **How it's calculated:** $\text{Hollywood Share \%} = \frac{\text{USA Produced Movies in Catalog}}{\text{Total Catalog Movies}} \times 100$.")
    build_folium_map(
        'hollywood_color',
        ['country', 'hollywood_pct', 'total_movies'],
        ['Country:', 'Hollywood Share:', 'Total Catalog:'],
        'm5'
    )

# -----------------------------------------------------------------------------
# TAB 6: The Nostalgia Index
# -----------------------------------------------------------------------------
with tab6:
    st.subheader("Map 6: The Nostalgia Index (Vintage vs. Modern Taste)")
    st.caption(r"📐 **How it's calculated:** Average release year ($\bar{Y}$) of top 20 highest-rated films in catalog.")
    build_folium_map(
        'nostalgia_color',
        ['country', 'avg_top20_year'],
        ['Country:', 'Avg Top 20 Release Year:'],
        'm6'
    )

# -----------------------------------------------------------------------------
# TAB 7: Sin City & Crime Index
# -----------------------------------------------------------------------------
with tab7:
    st.subheader("Map 7: The Sin City & Crime Index")
    st.caption(r"📐 **How it's calculated:** $\text{Crime Share \%} = \frac{\text{Crime + Action + Thriller + Mystery Entries}}{\text{Total Catalog Genre Entries}} \times 100$.")
    build_folium_map(
        'crime_color',
        ['country', 'crime_score'],
        ['Country:', 'Crime/Action/Thriller Share:'],
        'm7'
    )

# -----------------------------------------------------------------------------
# TAB 8: The Darkness Index
# -----------------------------------------------------------------------------
with tab8:
    st.subheader("Map 8: The Darkness Index (Horror/Thriller vs. Lighthearted Cinema)")
    st.caption(r"📐 **How it's calculated:** $\text{Dark Ratio \%} = \frac{\text{Horror, Thriller, Crime, Mystery}}{\text{Horror, Thriller, Crime, Mystery + Comedy, Animation, Family, Romance}} \times 100$.")
    build_folium_map(
        'darkness_color',
        ['country', 'darkness_score'],
        ['Country:', 'Dark Genre Ratio:'],
        'm8'
    )

# -----------------------------------------------------------------------------
# TAB 9: Taste Twin Finder
# -----------------------------------------------------------------------------
with tab9:
    st.subheader("Map 9: Cinematic Taste Twin Finder")
    st.caption(r"📐 **How it's calculated:** Cosine Similarity between normalized genre distribution vectors ($V_A \cdot V_B / (\|V_A\| \|V_B\|)$).")
    
    sorted_c_list = sorted(df['country'].dropna().unique().tolist())
    ref_country = st.selectbox("Select Reference Country:", sorted_c_list, index=sorted_c_list.index("Turkey") if "Turkey" in sorted_c_list else 0)
    
    all_dist = df.set_index('country')['genre_distribution'].apply(json.loads).to_dict()
    ref_dist = all_dist.get(ref_country, {})
    
    all_genres_set = set()
    for d_dict in all_dist.values():
        all_genres_set.update(d_dict.keys())
    genre_list = list(all_genres_set)
    
    ref_vector = np.array([ref_dist.get(g, 0.0) for g in genre_list])
    ref_norm = np.linalg.norm(ref_vector)
    
    similarity_dict = {}
    for c_name, d_dict in all_dist.items():
        v = np.array([d_dict.get(g, 0.0) for g in genre_list])
        v_norm = np.linalg.norm(v)
        if ref_norm > 0 and v_norm > 0:
            sim = np.dot(ref_vector, v) / (ref_norm * v_norm)
        else:
            sim = 0.0
        similarity_dict[c_name] = round(sim * 100, 1)

    twin_geojson = copy.deepcopy(fetch_base_geojson())
    for feature in twin_geojson['features']:
        orig = feature['properties']['name']
        cn = COUNTRY_NAME_FIXES.get(orig, orig)
        feature['properties']['country'] = cn
        score = similarity_dict.get(cn, 0.0)
        feature['properties']['similarity_score'] = f"{score}%"
        
        if cn == ref_country:
            feature['properties']['twin_color'] = "#ffb400"
        else:
            s_norm = min(max((score - 70.0) / 30.0, 0.0), 1.0)
            if s_norm <= 0.40:
                t = s_norm / 0.40
                feature['properties']['twin_color'] = f"#{int(245-105*t):02x}{int(245-105*t):02x}{int(245-95*t):02x}"
            else:
                t = (s_norm - 0.40) / 0.60
                feature['properties']['twin_color'] = f"#{int(140-94*t):02x}{int(140+64*t):02x}{int(150-37*t):02x}"

    build_folium_map(
        'twin_color',
        ['country', 'similarity_score'],
        ['Country:', f'Taste Similarity to {ref_country}:'],
        'm9',
        custom_geojson=twin_geojson
    )

# -----------------------------------------------------------------------------
# TAB 10: Slow Cinema Index
# -----------------------------------------------------------------------------
with tab10:
    st.subheader("Map 10: The Slow Cinema / Patience Index")
    st.caption(r"📐 **How it's calculated:** Average feature film runtime ($\bar{R}$) in minutes.")
    build_folium_map(
        'slow_color',
        ['country', 'slow_cinema_pct', 'avg_runtime'],
        ['Country:', '140+ Min Epics Ratio:', 'Average Runtime:'],
        'm10'
    )

# -----------------------------------------------------------------------------
# TAB 11: Futurism & Cyberpunk Index
# -----------------------------------------------------------------------------
with tab11:
    st.subheader("Map 11: Futurism & Cyberpunk Index")
    st.caption(r"📐 **How it's calculated:** $\text{Sci-Fi Share \%} = \frac{\text{Science Fiction Genre Entries}}{\text{Total Catalog Genre Entries}} \times 100$.")
    build_folium_map(
        'futurism_color',
        ['country', 'futurism_score'],
        ['Country:', 'Sci-Fi Genre Share:'],
        'm11'
    )

# -----------------------------------------------------------------------------
# TAB 12: Tears & Melodrama Index
# -----------------------------------------------------------------------------
with tab12:
    st.subheader("Map 12: The Tears & Melodrama Index")
    st.caption(r"📐 **How it's calculated:** $\text{Melodrama Share \%} = \frac{\text{Romance + Drama Genre Entries}}{\text{Total Catalog Genre Entries}} \times 100$.")
    build_folium_map(
        'melodrama_color',
        ['country', 'melodrama_score'],
        ['Country:', 'Romance & Drama Share:'],
        'm12'
    )

# --- FOOTER SECTION ---
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #888888; font-size: 13px; padding: 10px 0 20px 0;">
        Created with ❤️ by <a href="https://github.com/mertkuleci" target="_blank" style="color: #00e054; text-decoration: none; font-weight: bold;">mertkuleci ↗</a> | Powered by 
        <a href="https://letterboxd.com" target="_blank" style="color: #ffb400; text-decoration: none; font-weight: bold;">
            Letterboxd
        </a> 
        & 
        <a href="https://www.kaggle.com/datasets" target="_blank" style="color: #20beff; text-decoration: none; font-weight: bold;">
            Kaggle Datasets
        </a>
    </div>
    """,
    unsafe_allow_html=True
)