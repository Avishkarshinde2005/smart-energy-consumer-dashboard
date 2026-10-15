# Technical Requirements Document (TRD)
## Smart Waste Management & Collection Optimization

### 1. System Architecture
Single-machine, monolithic architecture — appropriate for a TY college project:
- **Data Sources:** Google Form / CSV upload / Synthetic data generator
- **Data Layer:** SQLite (waste_management.db) / CSV storage
- **Processing Layer:** Pandas/NumPy preprocessing, cleaning, categorization
- **Analytics/ML Layer:** scikit-learn (Random Forest priority classifier), Google OR-Tools (TSP routing)
- **Presentation Layer:** Streamlit dashboard + Folium map + Plotly charts
- **Optional LLM Layer:** Ollama (Llama 3.2 3B) local REST API

---

### 2. Technology Stack Details
- **Language:** Python 3.10+
- **Data Handling:** Pandas, NumPy, SQLite (sqlite3)
- **Machine Learning:** scikit-learn (RandomForestClassifier, StandardScaler)
- **Route Optimization:** Google OR-Tools (RoutingIndexManager, RoutingModel), NetworkX
- **Visualization:** Plotly, Matplotlib, Seaborn
- **Mapping:** Folium + OpenStreetMap tiles (streamlit-folium)
- **Dashboard:** Streamlit
- **PDF Generation:** ReportLab
- **Testing:** Pytest

---

### 3. Data Model Schema
#### Table: bins
- bin_id: TEXT PRIMARY KEY
- location_name: TEXT NOT NULL
- latitude: REAL NOT NULL
- longitude: REAL NOT NULL
- waste_type: TEXT (Organic, Recyclable, General, Hazardous)
- collection_frequency: TEXT (Daily, Alternate Days, Bi-Weekly)

#### Table: bin_readings
- reading_id: INTEGER PRIMARY KEY AUTOINCREMENT
- bin_id: TEXT FOREIGN KEY -> bins.bin_id
- fill_level: REAL (0 to 100)
- fill_category: TEXT (Low, Medium, High, Critical)
- overflow_status: BOOLEAN (0 or 1)
- timestamp: DATETIME NOT NULL

#### Table: priority_scores (computed view or table)
- bin_id: TEXT
- priority_score: REAL
- rank: INTEGER
- needs_collection: BOOLEAN

---

### 4. Core Algorithms
- **Rule-Based Priority Scoring:**
  score = (0.50 * fill_level) + (35.0 * overflow_status) + (3.0 * days_since_last_collection)
- **Machine Learning Priority Model:**
  Random Forest Classifier with 100 estimators predicting binary collection requirement from fill level, waste type, days since last collection, and overflow history.
- **Route Optimization:**
  - Haversine distance matrix computation:
    d = 2R * arcsin(sqrt(sin^2(dlat/2) + cos(lat1)*cos(lat2)*sin^2(dlon/2)))
  - Heuristic: Nearest Neighbor algorithm starting from Depot.
  - Enhanced TSP: Google OR-Tools RoutingModel using PATH_CHEAPEST_ARC first solution strategy.
