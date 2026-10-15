# Smart Waste Management & Collection Optimization System

[![Deploy to Streamlit Cloud](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=Avishkarshinde2005/smart-energy-consumer-dashboard&branch=main&mainModule=app.py)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B.svg)](https://streamlit.io/)
[![OR-Tools](https://img.shields.io/badge/Google-OR--Tools-4285F4.svg)](https://developers.google.com/optimization)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 🚀 **Deploy & Launch App:** [Click here to 1-Click Launch on Streamlit Cloud](https://share.streamlit.io/deploy?repository=Avishkarshinde2005/smart-energy-consumer-dashboard&branch=main&mainModule=app.py)

An end-to-end data-driven municipal and college campus smart waste management platform that transitions traditional fixed-schedule waste collection to dynamic, on-demand, fill-level-based routing. The system ingests sensor/form readings, preprocesses anomalies, ranks urgency using rule-based scoring and machine learning, and generates distance-optimized collection routes using Google OR-Tools and Nearest Neighbor TSP heuristics.

---

## 📑 Table of Contents
1. [Project Overview](#-project-overview)
2. [Key Features](#-key-features)
3. [System Architecture](#-system-architecture)
4. [Complete Directory Structure](#-complete-directory-structure)
5. [Installation & Setup](#-installation--setup)
6. [Running the Application](#-running-the-application)
7. [Running Tests](#-running-tests)
8. [Jupyter Notebooks Walkthrough](#-jupyter-notebooks-walkthrough)
9. [Mathematical Models & Algorithms](#-mathematical-models--algorithms)
10. [College Project Viva Q&A Guide](#-college-project-viva-qa-guide)

---

## 🎯 Project Overview
- **Problem:** Conventional waste collection adheres to rigid, static timetables regardless of whether bins are empty or overflowing. This leads to fuel wastage, excessive carbon emissions, and unhygienic overflow conditions in high-traffic areas.
- **Solution:** A centralized data-driven fleet dispatch platform that monitors bin fill levels in real time, flags critical/overflowing bins into an intelligent priority queue, and optimizes the collection vehicle's route using mathematical Traveling Salesperson Problem (TSP) solvers.
- **Target Impact:** Achieves a **~25% to 45% reduction in total collection vehicle travel distance**, cutting fuel expenditure and municipal carbon emissions.

---

## ✨ Key Features
- **Data Ingestion & Cleaning (FR-1 & FR-2):** Handles CSV / Google Forms data, eliminates duplicates (`bin_id + timestamp`), clips erroneous out-of-range sensor readings ($0\% \le \text{fill} \le 100\%$), and categorizes fill levels (`Low`, `Medium`, `High`, `Critical`).
- **Descriptive Fleet Analytics (FR-3):** Interactive Plotly visualizations for fill-level histograms, waste stream breakdown (Organic, Recyclable, General, Hazardous), temporal fill trends, and zone-level overflow hotspots.
- **Intelligent Priority Scoring (FR-4):** Dual scoring architecture:
  - **Rule-Based Formula (MVP):** Weighted linear combination of current fill percentage, overflow status, and collection frequency.
  - **Machine Learning Alternative:** Random Forest Classifier trained on historical bin usage patterns.
- **Route Optimization (FR-5):** Computes geodesic Haversine distance matrices and solves TSP using both **Nearest Neighbor Heuristic** and **Google OR-Tools RoutingModel** (`PATH_CHEAPEST_ARC`), providing side-by-side fuel and distance savings benchmarks.
- **Geospatial Fleet Map (FR-5.3):** Interactive Folium map with color-coded bin markers, pulse-alert badges for overflows, Depot hub, and sequenced collection path polyline.
- **Executive AI Assistant (FR-7):** Integrates local LLM via Ollama (`llama3.2:3b`) with intelligent rule-based analytical summary fallbacks.
- **Automated Dispatch Manifests (FR-6.3):** Instant export of the day's priority pickup list in CSV and PDF formats.

---

## 🏗️ System Architecture
```
┌─────────────────────┐
│    Data Sources     │ Google Form / CSV upload / Synthetic Data Generator
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     Data Layer      │ SQLite (waste_management.db) / Raw & Cleaned CSVs
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Processing Layer   │ Pandas/NumPy Cleaning, Deduplication, Bounds Clipping
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Analytics/ML Layer  │ scikit-learn (Random Forest), Google OR-Tools (TSP)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Presentation Layer  │ Streamlit Multi-tab UI + Folium Map + Plotly Charts
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Optional LLM Layer  │ Ollama (Llama 3.2 3B) / Local Heuristic Summarizer
└─────────────────────┘
```

---

## 📁 Complete Directory Structure
```
smart-waste-management/
├── app.py                          # Main Streamlit dashboard entry point
├── requirements.txt                # Pinned project dependencies
├── README.md                       # Complete documentation and viva pack
├── .gitignore                      # Git ignore patterns
│
├── data/
│   ├── raw/
│   │   └── bin_readings_raw.csv    # Raw dataset with simulated duplicates & anomalies
│   ├── processed/
│   │   └── bin_readings_cleaned.csv# Cleaned & standardized dataset
│   ├── sample/
│   │   └── sample_bin_data.csv     # Campus sample dataset
│   └── database/
│       └── waste_management.db    # SQLite relational database
│
├── notebooks/                      # Exploratory & Prototyping Jupyter Notebooks
│   ├── 01_data_collection.ipynb    # Data ingestion and SQLite schema setup
│   ├── 02_data_preprocessing.ipynb # Data cleaning, imputation, and validation
│   ├── 03_exploratory_data_analysis.ipynb # Statistical distributions and trends
│   ├── 04_priority_analysis.ipynb  # Rule vs. ML priority scoring models
│   └── 05_route_optimization.ipynb # Haversine distance, Nearest Neighbor & OR-Tools
│
├── src/                            # Modular Backend Packages
│   ├── __init__.py
│   ├── database.py                 # SQLite CRUD, schema migrations, and queries
│   ├── data_loader.py              # CSV loaders and synthetic campus data generator
│   ├── preprocessing.py            # FR-2 Data cleaning, bounds clipping & categorizer
│   ├── analysis.py                 # Descriptive statistics, KPIs & hotspot analytics
│   ├── priority_scoring.py         # FR-4 Rule-based scoring & Random Forest inference
│   ├── route_optimizer.py          # FR-5 Haversine, Nearest Neighbor & OR-Tools TSP
│   ├── forecasting.py              # FR-8 Time-to-critical regression forecaster
│   └── utils.py                    # PDF generator, Haversine math, Ollama LLM client
│
├── models/
│   ├── priority_classifier.pkl     # Serialized Random Forest model
│   └── forecast_model.pkl          # Serialized fill forecaster
│
├── dashboard/                      # UI Components
│   ├── __init__.py
│   ├── charts.py                   # Plotly histograms, pie charts, and trend lines
│   ├── maps.py                     # Folium interactive geospatial map with routes
│   ├── filters.py                  # Streamlit sidebar controls and parameter sliders
│   └── components.py               # Metric cards, alert banners, and export buttons
│
├── reports/
│   ├── priority_collection_list.csv# Exported dispatch CSV
│   └── priority_collection_report.pdf# Exported dispatch PDF manifest
│
├── tests/                          # Automated Pytest / Unittest Suite
│   ├── __init__.py
│   ├── test_preprocessing.py       # Preprocessing and bounds validation unit tests
│   ├── test_priority_scoring.py    # Priority formula and ranking unit tests
│   └── test_route_optimizer.py     # Haversine and TSP solver unit tests
│
├── assets/
│   ├── logo.png                    # Project branding logo
│   └── style.css                   # Modern CSS styling for Streamlit
│
└── docs/
    ├── PRD.md                      # Product Requirements Document
    ├── FRD.md                      # Functional Requirements Document
    ├── TRD.md                      # Technical Requirements Document
    └── architecture_diagram.png    # System architecture block diagram
```

---

## ⚙️ Installation & Setup

### 1. Clone or Open Project Directory
```bash
cd smart-waste-management
```

### 2. Create and Activate Virtual Environment
```bash
# On macOS / Linux
python3 -m venv venv
source venv/bin/activate

# On Windows (cmd)
python -m venv venv
venv\Scripts\activate
```

### 3. Install Required Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

*(Optional)* If you wish to enable the local LLM executive assistant:
1. Install Ollama from [https://ollama.com](https://ollama.com)
2. Run: `ollama pull llama3.2:3b`
*(If Ollama is not installed or running, the dashboard automatically falls back to an intelligent heuristic summarizer).*

---

## 🚀 Running the Application
Launch the interactive Streamlit dashboard:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Running Tests
Execute the automated test suite:
```bash
# Run using Pytest
pytest tests/ -v

# Or run using Python's built-in Unittest runner (zero external dependencies required)
python3 -m unittest discover tests
```

---

## 📓 Jupyter Notebooks Walkthrough
Launch Jupyter to explore step-by-step data science workflows:
```bash
jupyter notebook notebooks/
```
- **`01_data_collection.ipynb`**: Demonstrates campus bin data simulation and SQLite table loading.
- **`02_data_preprocessing.ipynb`**: Step-by-step cleaning: removing duplicates, fixing negative/out-of-bound fill levels, categorizing fill tiers.
- **`03_exploratory_data_analysis.ipynb`**: Exploratory data analysis, distributions, correlation matrices, and overflow hotspot identification.
- **`04_priority_analysis.ipynb`**: Implementation of the rule-based formula and training the Random Forest priority classifier.
- **`05_route_optimization.ipynb`**: Distance matrix generation, comparing Nearest Neighbor vs. Google OR-Tools, and calculating percentage savings.

---

## 📐 Mathematical Models & Algorithms

### 1. Rule-Based Priority Scoring Formula (TRD §5.1)
$$\text{Score} = (w_{\text{fill}} \times \text{fill\_level}) + (w_{\text{overflow}} \times \text{overflow\_status}) + (w_{\text{freq}} \times \text{days\_since\_last\_collection})$$
- **Default Weights:**
  - $w_{\text{fill}} = 0.50$
  - $w_{\text{overflow}} = 35.0$
  - $w_{\text{freq}} = 3.0$
- **Collection Threshold:** Bins with $\text{Score} \ge 40.0$, $\text{fill} \ge 86\%$ (`Critical`), or $\text{overflow\_status} = \text{True}$ are flagged for priority dispatch.

### 2. Haversine Distance Formula (TRD §5.3)
To compute the true geodesic surface distance between coordinates $(\phi_1, \lambda_1)$ and $(\phi_2, \lambda_2)$:
$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1) \cos(\phi_2) \sin^2\left(\frac{\Delta \lambda}{2}\right)$$
$$c = 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1 - a}\right)$$
$$d = R \times c \quad (R = 6371.0\text{ km})$$

### 3. Route Optimization Algorithms
- **Nearest Neighbor Heuristic (Greedy):** Starting at Depot $D$, iteratively visits the closest unvisited bin:
  $$v_{k+1} = \arg\min_{u \in U} \text{dist}(v_k, u)$$
- **Google OR-Tools TSP Solver:** Formulates integer linear programming constraints over the symmetric distance matrix with the `PATH_CHEAPEST_ARC` first-solution heuristic and local search operators.
- **Efficiency Metric:**
  $$\text{Distance Saved (\%)} = \left( \frac{D_{\text{naive}} - D_{\text{optimized}}}{D_{\text{naive}}} \right) \times 100\%$$

---

## 🎓 College Project Viva Q&A Guide

### Q1: What is the core problem your project solves?
**Answer:** Municipal collection vehicles typically follow fixed routes regardless of whether bins are completely empty or overflowing. This results in wasted fuel and vehicle wear visiting empty bins, while overflowing bins in busy areas cause severe environmental and health hazards. Our system dynamically detects bin urgency and generates optimized shortest-path collection routes only for bins that need pickup.

### Q2: Why did you choose Google OR-Tools over a simple heuristic?
**Answer:** The Nearest Neighbor heuristic is fast ($O(N^2)$) but can get trapped in local optima and produce suboptimal zig-zag routes for larger graphs. Google OR-Tools implements sophisticated operations research techniques (Guided Local Search and Tabu Search) that find near-optimal global solutions to NP-hard problems like the Traveling Salesperson Problem (TSP) and Vehicle Routing Problem (VRP).

### Q3: How do you handle out-of-range sensor readings?
**Answer:** In `src/preprocessing.py`, values are bounded between $0\%$ and $100\%$. Values $>100\%$ (caused by optical sensor reflection or false readings) are capped to $100\%$, and negative readings are clipped to $0\%$. Duplicate readings with the identical `(bin_id, timestamp)` are detected and dropped.

### Q4: Why use SQLite instead of a heavy database like MySQL or PostgreSQL?
**Answer:** SQLite is serverless, zero-configuration, and file-based (`waste_management.db`), making it ideal for monolithic, single-machine college project demonstrations. It easily handles tens of thousands of bin records without incurring server overhead or hosting fees.

### Q5: How is fuel and CO2 savings estimated?
**Answer:** We benchmark the optimized TSP route against the naive sequential catalog order route. Assuming an average municipal diesel collection truck consumes approximately $0.25\text{ liters/km}$ and each liter of diesel emits $2.68\text{ kg CO}_2$, saving travel kilometers directly translates to measurable diesel liters saved and carbon emissions avoided.
