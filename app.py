import streamlit as st
import pandas as pd
import json
import requests
import pydeck as pdk
import numpy as np

st.set_page_config(page_title="Letterboxd World Cinema Dashboard | mertkuleci", layout="wide", initial_sidebar_state="collapsed")

@st.cache_data
def load_summary():
    return pd.read_csv('data/country_summary.csv')

df = load_summary()

# Tarih aralığını özet veriden alıyoruz (Ağır CSV okumuyoruz)
min_data_year = 1900
max_data_year = int(df['top_movie_year'].dropna().astype(str).str.extract(r'(\d{4})')[0].max()) if 'top_movie_year' in df.columns else 2024

# GeoJSON Country Name Alignment Map
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

COLOR_PALETTE = [
    [230, 25, 75], [60, 180, 75], [255, 225, 25], [67, 99, 216], [245, 130, 49],
    [145, 30, 180], [66, 212, 244], [240, 50, 230], [191, 239, 69], [250, 190, 212],
    [70, 153, 144], [220, 190, 255], [154, 99, 36], [255, 250, 200], [128, 0, 0]
]

GENRE_COLORS = {
    "Drama": [67, 99, 216, 180],
    "Comedy": [255, 225, 25, 180],
    "Action": [230, 25, 75, 180],
    "Horror": [128, 0, 0, 180],
    "Romance": [250, 190, 212, 180],
    "Documentary": [70, 153, 144, 180],
    "Animation": [60, 180, 75, 180],
    "Crime": [145, 30, 180, 180],
    "Thriller": [245, 130, 49, 180],
    "Adventure": [66, 212, 244, 180],
    "Science Fiction": [240, 50, 230, 180]
}

def get_rgb_color(name):
    rgb = COLOR_PALETTE[abs(hash(str(name))) % len(COLOR_PALETTE)]
    return [rgb[0], rgb[1], rgb[2], 180]

GEOJSON_URL = "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/world-countries.json"

@st.cache_data
def prepare_geojson():
    res = requests.get(GEOJSON_URL).json()
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
            feature['properties']['avg_runtime'] = str(d['avg_runtime'])
            feature['properties']['has_domestic_top_film'] = d['has_domestic_top_film']
            feature['properties']['ownership_status'] = "🟢 Domestic / Co-Production" if d['has_domestic_top_film'] else "🔴 Foreign Import"
            feature['properties']['hollywood_pct'] = f"{d['hollywood_pct']}%"
            feature['properties']['avg_top20_year'] = str(d['avg_top20_year'])
            feature['properties']['crime_score'] = f"{d['crime_score']}%"
            feature['properties']['darkness_score'] = f"{d['darkness_score']}%"
            feature['properties']['arthouse_score'] = f"{d['arthouse_score']}%"
            feature['properties']['slow_cinema_pct'] = f"{d['slow_cinema_pct']}%"
            feature['properties']['futurism_score'] = f"{d['futurism_score']}%"
            feature['properties']['melodrama_score'] = f"{d['melodrama_score']}%"
            
            # Map Base Colors
            feature['properties']['fill_color'] = get_rgb_color(cname)
            feature['properties']['movie_color'] = get_rgb_color(str(d['top_movie']))
            feature['properties']['domestic_color'] = [46, 204, 113, 180] if d['has_domestic_top_film'] else [231, 76, 60, 180]
            feature['properties']['genre_color'] = GENRE_COLORS.get(d['top_genre'], [149, 165, 166, 180])
            
            # Hollywood scale
            hw = min(d['hollywood_pct'] / 100.0, 1.0)
            feature['properties']['hollywood_color'] = [int(255 * hw), int(255 * (1 - hw)), 50, 180]
            
            # Nostalgia scale
            yr = d['avg_top20_year']
            if yr < 1985:
                feature['properties']['nostalgia_color'] = [142, 68, 173, 180]
            elif yr > 2005:
                feature['properties']['nostalgia_color'] = [241, 196, 15, 180]
            else:
                feature['properties']['nostalgia_color'] = [52, 152, 219, 180]
                
            # Crime scale
            cr_norm = min(max((d['crime_score'] - 10.0) / 25.0, 0.0), 1.0)
            if cr_norm <= 0.25:
                t = cr_norm / 0.25
                feature['properties']['crime_color'] = [int(240 - 60 * t), int(240 - 60 * t), int(245 - 55 * t), 180]
            elif cr_norm <= 0.65:
                t = (cr_norm - 0.25) / 0.40
                feature['properties']['crime_color'] = [int(180 + 60 * t), int(180 - 60 * t), int(190 - 30 * t), 180]
            else:
                t = (cr_norm - 0.65) / 0.35
                feature['properties']['crime_color'] = [int(240 - 20 * t), int(120 - 100 * t), int(160 - 110 * t), 200]

            # Darkness scale
            dk = d['darkness_score'] / 100.0
            feature['properties']['darkness_color'] = [int(240 * (1 - dk) + 120 * dk), int(200 * (1 - dk)), int(50 * (1 - dk) + 200 * dk), 180]
            
            # Slow Cinema scale
            avg_rt = float(d['avg_runtime']) if str(d['avg_runtime']).replace('.', '').isdigit() else 100.0
            if avg_rt <= 92:
                feature['properties']['slow_color'] = [200, 215, 230, 160]
            elif avg_rt <= 102:
                t = (avg_rt - 92) / 10.0
                feature['properties']['slow_color'] = [int(200 - 100*t), int(215 - 95*t), int(230 - 30*t), 180]
            elif avg_rt <= 115:
                t = (avg_rt - 102) / 13.0
                feature['properties']['slow_color'] = [int(100 + 40*t), int(120 - 70*t), int(200 + 10*t), 180]
            else:
                t = min((avg_rt - 115) / 15.0, 1.0)
                feature['properties']['slow_color'] = [int(140 + 80*t), int(50 - 30*t), int(210 + 35*t), 200]

            # Futurism scale
            ft_val = d['futurism_score']
            if ft_val <= 0.5:
                feature['properties']['futurism_color'] = [35, 38, 45, 120]
            elif ft_val <= 2.0:
                t = (ft_val - 0.5) / 1.5
                feature['properties']['futurism_color'] = [int(20 + 30*t), int(60 + 80*t), int(140 + 60*t), 180]
            elif ft_val <= 4.5:
                t = (ft_val - 2.0) / 2.5
                feature['properties']['futurism_color'] = [int(50 - 50*t), int(140 + 100*t), int(200 + 40*t), 200]
            else:
                t = min((ft_val - 4.5) / 2.5, 1.0)
                feature['properties']['futurism_color'] = [int(0 + 100*t), int(240 + 15*t), int(240 - 40*t), 220]

            # Melodrama scale
            md_norm = min(max((d['melodrama_score'] - 15.0) / 20.0, 0.0), 1.0)
            if md_norm <= 0.5:
                t = md_norm / 0.5
                feature['properties']['melodrama_color'] = [250, int(250 - 120 * t), int(250 - 80 * t), 180]
            else:
                t = (md_norm - 0.5) / 0.5
                feature['properties']['melodrama_color'] = [int(250 - 30 * t), int(130 - 110 * t), int(170 - 130 * t), 200]
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
            
            for key in ['fill_color', 'movie_color', 'domestic_color', 'genre_color', 'hollywood_color', 'nostalgia_color', 'crime_color', 'darkness_color', 'slow_color', 'futurism_color', 'melodrama_color']:
                feature['properties'][key] = [40, 40, 40, 100]
            
    return res

geojson_data = prepare_geojson()

def build_pydeck_map(color_accessor, tooltip_html, custom_geojson=None):
    layer = pdk.Layer(
        "GeoJsonLayer",
        custom_geojson or geojson_data,
        opacity=0.8,
        stroked=True,
        filled=True,
        extruded=False,
        wireframe=True,
        get_fill_color=color_accessor,
        get_line_color=[30, 30, 30, 200],
        get_line_width=1000,
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 255, 255, 120]
    )

    view_state = pdk.ViewState(
        latitude=20,
        longitude=0,
        zoom=1.2,
        min_zoom=1,
        max_zoom=6,
        pitch=0,
        bearing=0
    )

    return pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip={
            "html": tooltip_html,
            "style": {
                "backgroundColor": "rgba(20, 24, 28, 0.95)",
                "color": "#ffffff",
                "border": "1px solid #444444",
                "borderRadius": "6px",
                "padding": "8px",
                "zIndex": "9999"
            }
        }
    )

# --- HEADER SECTION WITH BRANDING ---
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
# TAB 1: World Cinema & Local Highlights
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("Map 1: Favorite Feature Films Worldwide (Color-Coded by Movie Title)")
    st.caption(r"📐 **How it's calculated:** Identifies the highest Letterboxd-rated feature film (60-220 min) released in each nation's catalog. Countries that share the exact same top film share the exact same color.")
    
    t1_html = """
    <div style="font-family: sans-serif; font-size: 12px; width: 220px;">
        <b style="font-size: 15px; color: #ffb400;">{country}</b><br><br>
        🏆 <b>Top Film:</b> {top_movie} ({top_movie_year})<br>
        <b>Rating:</b> <span style="color: #e50914; font-weight: bold;">{top_movie_rating}</span><br><br>
        🎬 <b>Top Director:</b> {top_director} ({top_director_rating})<br>
        🎭 <b>Top Genre:</b> {top_genre}<br><br>
        📊 <b>Catalog:</b> {total_movies} movies | Avg {avg_country_rating}
    </div>
    """
    st.pydeck_chart(build_pydeck_map("properties.movie_color", t1_html), use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 2: Film Domestic vs Foreign Release
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("Map 2: Favorite Released Movie - Domestic vs Foreign Origin")
    st.caption(r"📐 **How it's calculated:** Cross-references `processed_releases.csv` (where movies were distributed) with `processed_movies.csv` (where movies were produced). Green = country is a producer of its top released film; Red = top film is a foreign import.")
    
    t2_html = """
    <div style="font-family: sans-serif; font-size: 12px; width: 210px;">
        <b style="font-size: 15px; color: #ffb400;">{country}</b><br><br>
        <b>Origin Status:</b> {ownership_status}<br><br>
        🏆 <b>Top Released Film:</b> {top_movie} ({top_movie_year})<br>
        <b>Rating:</b> <span style="color: #e50914; font-weight: bold;">{top_movie_rating}</span>
    </div>
    """
    st.pydeck_chart(build_pydeck_map("properties.domestic_color", t2_html), use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 3: Country Spotlight & Global Reach
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("Map 3: Country Spotlight & Global Distribution Reach")
    st.caption(r"📐 **How it's calculated:** Ranks the selected nation's top 10 films and directors (min. 3 films). The Global Reach map calculates catalog overlap counts ($\text{Shared Movies} = |M_A \cap M_B|$) using a logarithmic color scale from 0 to 20,000+ shared titles.")
    
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

            st.write("### 🌐 Global Reach Map (Graduated 0 to 20,000+ shared movie scale with " + selected_c + ")")
            
            reach_geojson = requests.get(GEOJSON_URL).json()
            
            for feature in reach_geojson['features']:
                orig = feature['properties']['name']
                cn = COUNTRY_NAME_FIXES.get(orig, orig)
                feature['properties']['country'] = cn
                cnt = reach_map.get(cn, 0)
                feature['properties']['shared_count'] = str(cnt)
                
                if cn == selected_c:
                    feature['properties']['reach_color'] = [255, 180, 0, 240]
                elif cnt > 0:
                    r_norm = min(np.log1p(cnt) / np.log1p(20000.0), 1.0)
                    feature['properties']['reach_color'] = [int(30 + 150 * r_norm), int(60 + 195 * r_norm), int(90 - 40 * r_norm), 190]
                else:
                    feature['properties']['reach_color'] = [40, 40, 40, 100]

            reach_html = "<b>📍 {country}</b><br>Shared Catalog Movies: <b>{shared_count}</b>"
            st.pydeck_chart(build_pydeck_map("properties.reach_color", reach_html, custom_geojson=reach_geojson), use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 4: Genre Capitals
# -----------------------------------------------------------------------------
with tab4:
    st.subheader("Map 4: Dominant Genre Capitals of the World")
    st.caption(r"📐 **How it's calculated:** Evaluates the mode (most frequent) genre entry across all feature films in each country's catalog, displaying both dominant genre type and its movie count.")
    
    t4_html = """
    <div style="font-family: sans-serif; font-size: 12px; width: 210px;">
        <b style="font-size: 15px; color: #ffb400;">{country}</b><br><br>
        🎭 <b>Top Genre:</b> {top_genre} (<b>{top_genre_count}</b> movies)<br>
        📊 <b>Total Catalog:</b> {total_movies} movies
    </div>
    """
    st.pydeck_chart(build_pydeck_map("properties.genre_color", t4_html), use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 5: Hollywood Dependence Index
# -----------------------------------------------------------------------------
with tab5:
    st.subheader("Map 5: Hollywood Dependence Index")
    st.caption(r"📐 **How it's calculated:** $\text{Hollywood Share \%} = \frac{\text{USA Produced Movies in Catalog}}{\text{Total Catalog Movies}} \times 100$. Red indicates heavy US dominance; Green indicates high cinematic sovereignty.")
    
    t5_html = """
    <div style="font-family: sans-serif; font-size: 12px; width: 200px;">
        <b style="font-size: 15px; color: #ffb400;">{country}</b><br><br>
        🇺🇸 <b>Hollywood Share:</b> {hollywood_pct}<br>
        📊 <b>Catalog:</b> {total_movies} movies
    </div>
    """
    st.pydeck_chart(build_pydeck_map("properties.hollywood_color", t5_html), use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 6: The Nostalgia Index
# -----------------------------------------------------------------------------
with tab6:
    st.subheader("Map 6: The Nostalgia Index (Vintage vs. Modern Taste)")
    st.caption(r"📐 **How it's calculated:** Computes the average release year ($\bar{Y}$) of the top 20 highest-rated films in a nation's catalog. Purple = Pre-1985 (Classic Era); Blue = 1985-2005 (Balanced); Yellow = Post-2005 (Modern Era).")
    
    t6_html = """
    <div style="font-family: sans-serif; font-size: 12px; width: 200px;">
        <b style="font-size: 15px; color: #ffb400;">{country}</b><br><br>
        🕰️ <b>Avg Top 20 Release Year:</b> {avg_top20_year}
    </div>
    """
    st.pydeck_chart(build_pydeck_map("properties.nostalgia_color", t6_html), use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 7: Sin City & Crime Index
# -----------------------------------------------------------------------------
with tab7:
    st.subheader("Map 7: The Sin City & Crime Index")
    st.caption(r"📐 **How it's calculated:** $\text{Crime Share \%} = \frac{\text{Crime + Action + Thriller + Mystery Entries}}{\text{Total Catalog Genre Entries}} \times 100$. Color gradient calibrated across 10% to 35%+.")
    
    t7_html = """
    <div style="font-family: sans-serif; font-size: 12px; width: 200px;">
        <b style="font-size: 15px; color: #ffb400;">{country}</b><br><br>
        🚨 <b>Crime/Action/Thriller Share:</b> {crime_score}
    </div>
    """
    st.pydeck_chart(build_pydeck_map("properties.crime_color", t7_html), use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 8: The Darkness Index
# -----------------------------------------------------------------------------
with tab8:
    st.subheader("Map 8: The Darkness Index (Horror/Thriller vs. Lighthearted Cinema)")
    st.caption(r"📐 **How it's calculated:** $\text{Dark Ratio \%} = \frac{\text{Dark Genres (Horror, Thriller, Crime, Mystery)}}{\text{Dark Genres + Light Genres (Comedy, Animation, Family, Romance)}} \times 100$. Purple/Red = Dark-focused; Yellow = Lighthearted.")
    
    t8_html = """
    <div style="font-family: sans-serif; font-size: 12px; width: 200px;">
        <b style="font-size: 15px; color: #ffb400;">{country}</b><br><br>
        💀 <b>Dark Genre Ratio:</b> {darkness_score}
    </div>
    """
    st.pydeck_chart(build_pydeck_map("properties.darkness_color", t8_html), use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 9: Taste Twin Finder
# -----------------------------------------------------------------------------
with tab9:
    st.subheader("Map 9: Cinematic Taste Twin Finder")
    st.caption(r"📐 **How it's calculated:** Calculates Cosine Similarity between normalized genre distribution vectors ($V_A \cdot V_B / (\|V_A\| \|V_B\|)$) of the reference country and all other nations. Scale spread across 70% to 100%.")
    
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

    twin_geojson = requests.get(GEOJSON_URL).json()
    for feature in twin_geojson['features']:
        orig = feature['properties']['name']
        cn = COUNTRY_NAME_FIXES.get(orig, orig)
        feature['properties']['country'] = cn
        score = similarity_dict.get(cn, 0.0)
        feature['properties']['similarity_score'] = f"{score}%"
        
        if cn == ref_country:
            feature['properties']['twin_color'] = [255, 180, 0, 240]
        else:
            s_norm = min(max((score - 70.0) / 30.0, 0.0), 1.0)
            if s_norm <= 0.40:
                t = s_norm / 0.40
                feature['properties']['twin_color'] = [int(245 - 105 * t), int(245 - 105 * t), int(245 - 95 * t), 180]
            else:
                t = (s_norm - 0.40) / 0.60
                feature['properties']['twin_color'] = [int(140 - 94 * t), int(140 + 64 * t), int(150 - 37 * t), 200]

    twin_html = "<b>📍 {country}</b><br>Taste Similarity to " + ref_country + ": <b>{similarity_score}</b>"
    st.pydeck_chart(build_pydeck_map("properties.twin_color", twin_html, custom_geojson=twin_geojson), use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 10: Slow Cinema Index
# -----------------------------------------------------------------------------
with tab10:
    st.subheader("Map 10: The Slow Cinema / Patience Index")
    st.caption(r"📐 **How it's calculated:** Measures average feature film runtime ($\bar{R}$) in minutes. Calibrated across 90m (Ice Blue), 102m (Slate Blue), 115m (Indigo), to 130m+ (Deep Electric Violet).")
    
    t10_html = """
    <div style="font-family: sans-serif; font-size: 12px; width: 200px;">
        <b style="font-size: 15px; color: #ffb400;">{country}</b><br><br>
        ⏳ <b>140+ Min Epics Ratio:</b> {slow_cinema_pct}<br>
        ⏱️ <b>Average Runtime:</b> {avg_runtime} mins
    </div>
    """
    st.pydeck_chart(build_pydeck_map("properties.slow_color", t10_html), use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 11: Futurism & Cyberpunk Index
# -----------------------------------------------------------------------------
with tab11:
    st.subheader("Map 11: Futurism & Cyberpunk Index")
    st.caption(r"📐 **How it's calculated:** $\text{Sci-Fi Share \%} = \frac{\text{Science Fiction Genre Entries}}{\text{Total Catalog Genre Entries}} \times 100$. Piecewise gradient calibrated across 0% (Dark Slate), 2.0% (Deep Blue), 4.5% (Cyber Cyan), to 6.5%+ (Electric Turquoise).")
    
    t11_html = """
    <div style="font-family: sans-serif; font-size: 12px; width: 200px;">
        <b style="font-size: 15px; color: #ffb400;">{country}</b><br><br>
        🛸 <b>Sci-Fi Genre Share:</b> {futurism_score}
    </div>
    """
    st.pydeck_chart(build_pydeck_map("properties.futurism_color", t11_html), use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 12: Tears & Melodrama Index
# -----------------------------------------------------------------------------
with tab12:
    st.subheader("Map 12: The Tears & Melodrama Index")
    st.caption(r"📐 **How it's calculated:** $\text{Melodrama Share \%} = \frac{\text{Romance + Drama Genre Entries}}{\text{Total Catalog Genre Entries}} \times 100$. Color gradient calibrated across 15% (White) to 35%+ (Crimson Red).")
    
    t12_html = """
    <div style="font-family: sans-serif; font-size: 12px; width: 200px;">
        <b style="font-size: 15px; color: #ffb400;">{country}</b><br><br>
        💔 <b>Romance & Drama Share:</b> {melodrama_score}
    </div>
    """
    st.pydeck_chart(build_pydeck_map("properties.melodrama_color", t12_html), use_container_width=True)

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