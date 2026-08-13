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
*Ranks a nation's top 10 films and directors (min. 3 films). Calculates shared catalog overlap across 0 to 20,000+ shared titles using a logarithmic scale:*

$$\text{Shared Movies} = |M_A \cap M_B|$$

![Map 3: Global Reach](assets/map3.png)

---

### 4. Genre Capitals of the World
*Evaluates the mode (most frequent) genre entry across all feature films in each country's catalog.*
![Map 4: Genre Capitals](assets/map4.png)

---

### 5. Hollywood Dependence Index
*Measures the proportion of US-produced films in each country's catalog:*

$$\text{Hollywood Share} = \left( \frac{\text{USA Movies in Catalog}}{\text{Total Catalog Movies}} \right) \times 100\%$$

![Map 5: Hollywood Dependence](assets/map5.png)

---

### 6. The Nostalgia Index (Vintage vs. Modern Taste)
*Computes the average release year ($\bar{Y}$) of the top 20 highest-rated films in a nation's catalog. Purple = Pre-1985 (Classic Era); Yellow = Post-2005 (Modern Era).*
![Map 6: Nostalgia Index](assets/map6.png)

---

### 7. The Sin City & Crime Index
*Ranks countries by crime, action, thriller, and mystery focus:*

$$\text{Crime Share} = \left( \frac{\text{Crime + Action + Thriller + Mystery Entries}}{\text{Total Genre Entries}} \right) \times 100\%$$

![Map 7: Sin City Index](assets/map7.png)

---

### 8. The Darkness Index
*Compares dark genres against lighthearted genres:*

$$\text{Dark Ratio} = \left( \frac{\text{Horror + Thriller + Crime + Mystery}}{\text{Dark Genres + Light Genres}} \right) \times 100\%$$

![Map 8: Darkness Index](assets/map8.png)

---

### 9. Cinematic Taste Twin Finder
*Calculates Cosine Similarity between normalized genre distribution vectors to locate every country's closest cinema taste twin:*

$$\text{Similarity}(V_A, V_B) = \frac{V_A \cdot V_B}{\|V_A\| \cdot \|V_B\|}$$

![Map 9: Taste Twin Finder](assets/map9.png)

---

### 10. The Slow Cinema / Patience Index
*Measures average feature film runtime ($\bar{R}$) in minutes. Calibrated from 90m (Ice Blue) to 130m+ (Deep Violet).*
![Map 10: Slow Cinema Index](assets/map10.png)

---

### 11. Futurism & Cyberpunk Index
*Measures the share of Science Fiction in national catalogs:*

$$\text{Sci-Fi Share} = \left( \frac{\text{Science Fiction Entries}}{\text{Total Genre Entries}} \right) \times 100\%$$

![Map 11: Futurism Index](assets/map11.png)

---

### 12. The Tears & Melodrama Index
*Calculates emotional melodrama focus:*

$$\text{Melodrama Share} = \left( \frac{\text{Romance + Drama Entries}}{\text{Total Genre Entries}} \right) \times 100\%$$

![Map 12: Melodrama Index](assets/map12.png)