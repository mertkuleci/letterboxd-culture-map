# 🎬 Letterboxd World Cinema Dashboard

An interactive, multi-index global cinema dashboard powered by **Streamlit**, **Folium**, and **Letterboxd / TMDb metadata**.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://letterboxd-culture-map.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Created with ❤️ by **[mertkuleci](https://github.com/mertkuleci)**

---

## 📌 Project Overview

The **Letterboxd World Cinema Dashboard** provides a quantitative and visual exploration of international film preferences, release origins, regional genre capitalizations, and cultural film indexes across **100+ countries**.

- 🌐 **Live Interactive App:** [letterboxd-culture-map.streamlit.app](https://letterboxd-culture-map.streamlit.app)
- 📊 **Dataset Coverage:** Archive spanning **1900 – 2024** (Letterboxd & TMDb Metadata Snapshot)
- 📱 **Mobile & Desktop Optimized:** Built using a 2D Leaflet rendering engine (`folium`) for 100% stability across Android, iOS, and Web browsers.

---

## 🗺️ Visual Map Showcase (Results)

### 1. World Favorites
*Identifies the highest Letterboxd-rated feature film (60–220 min) released in each nation's catalog. Countries that share the exact same top film share the exact same color.*
![Map 1: World Favorites](assets/map1.png)

---

### 2. Film Domestic vs. Foreign Origin
*Cross-references distribution countries with production origins. Green indicates a domestic or co-produced top film; Red indicates a foreign import.*
![Map 2: Domestic vs Foreign](assets/map2.png)

---

### 3. Country Spotlight & Global Reach
*Ranks a nation's top 10 films and directors (min. 3 films). Calculates shared catalog overlap ($|M_A \cap M_B|$) across 0 to 20,000+ shared titles using a logarithmic scale.*
![Map 3: Global Reach](assets/map3.png)

---

### 4. Genre Capitals of the World
*Evaluates the mode (most frequent) genre entry across all feature films in each country's catalog.*
![Map 4: Genre Capitals](assets/map4.png)

---

### 5. Hollywood Dependence Index
*Measures the proportion of US-produced films in each country's catalog: $\text{Hollywood Share \%} = \frac{\text{USA Movies}}{\text{Total Catalog}} \times 100$.*
![Map 5: Hollywood Dependence](assets/map5.png)

---

### 6. The Nostalgia Index (Vintage vs. Modern Taste)
*Computes the average release year ($\bar{Y}$) of the top 20 highest-rated films in a nation's catalog. Purple = Pre-1985 (Classic Era); Yellow = Post-2005 (Modern Era).*
![Map 6: Nostalgia Index](assets/map6.png)

---

### 7. The Sin City & Crime Index
*Ranks countries by crime, action, thriller, and mystery focus: $\text{Crime Share \%} = \frac{\text{Crime + Action + Thriller + Mystery}}{\text{Total Genre Entries}} \times 100$.*
![Map 7: Sin City Index](assets/map7.png)

---

### 8. The Darkness Index
*Compares dark genres against lighthearted genres: $\text{Dark Ratio \%} = \frac{\text{Horror + Thriller + Crime + Mystery}}{\text{Dark Genres + Light Genres}} \times 100$.*
![Map 8: Darkness Index](assets/map8.png)

---

### 9. Cinematic Taste Twin Finder
*Calculates Cosine Similarity between normalized genre distribution vectors ($V_A \cdot V_B / (\|V_A\| \|V_B\|)$) to locate every country's closest cinema taste twin.*
![Map 9: Taste Twin Finder](assets/map9.png)

---

### 10. The Slow Cinema / Patience Index
*Measures average feature film runtime ($\bar{R}$) in minutes. Calibrated from 90m (Ice Blue) to 130m+ (Deep Violet).*
![Map 10: Slow Cinema Index](assets/map10.png)

---

### 11. Futurism & Cyberpunk Index
*Measures the share of Science Fiction in national catalogs: $\text{Sci-Fi Share \%} = \frac{\text{Sci-Fi Entries}}{\text{Total Genre Entries}} \times 100$.*
![Map 11: Futurism Index](assets/map11.png)

---

### 12. The Tears & Melodrama Index
*Calculates emotional melodrama focus: $\text{Melodrama Share \%} = \frac{\text{Romance + Drama Entries}}{\text{Total Genre Entries}} \times 100$.*
![Map 12: Melodrama Index](assets/map12.png)

---

## 🛠️ Data Pipeline & Architecture

```text
raw_datasets/ (Kaggle TMDb/Letterboxd)
  ├── movies.csv, crew.csv, genres.csv, releases.csv
  │
  ▼  [data_processing.py]
data/processed_movies.csv & data/processed_releases.csv
  │
  ▼  [analytics.py]
data/country_summary.csv  (Lightweight summary file)
  │
  ▼  [app.py]
Streamlit Web App + Folium Map Engine
```

---

## 💻 Local Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/mertkuleci/letterboxd-culture-map.git](https://github.com/mertkuleci/letterboxd-culture-map.git)
   cd letterboxd-culture-map
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Streamlit application locally:**
   ```bash
   streamlit run app.py
   ```

---

## 📄 License & Attribution

- Created by **[mertkuleci](https://github.com/mertkuleci)**.
- Data provided by **[Letterboxd](https://letterboxd.com)** & **[Kaggle TMDb Datasets](https://www.kaggle.com/datasets)**.
- Released under the [MIT License](LICENSE).