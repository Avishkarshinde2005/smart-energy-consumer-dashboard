# Functional Requirements Document (FRD)
## Smart Waste Management & Collection Optimization

### 1. Introduction & Scope
This document specifies the functional requirements for the Smart Waste Management and Collection Optimization system. It defines what the system must do — inputs, processing, and outputs — for each module.

---

### 2. Functional Requirements

#### FR-1: Data Ingestion
- **FR-1.1:** System shall accept bin data via CSV upload or Google Form export.
- **FR-1.2:** Required fields: Bin ID, Location (lat/long or area name), Fill Level (%), Waste Type, Collection Frequency, Overflow Status, Timestamp.
- **FR-1.3:** System shall reject/flag records missing mandatory fields (Bin ID, Fill Level).

#### FR-2: Data Preprocessing
- **FR-2.1:** System shall detect and remove duplicate Bin ID + Timestamp entries.
- **FR-2.2:** System shall handle missing values (impute or drop, based on field).
- **FR-2.3:** System shall categorize Fill Level into:
  - Low (0–25%)
  - Medium (26–60%)
  - High (61–85%)
  - Critical (86–100%)
- **FR-2.4:** System shall validate and correct obviously erroneous entries (e.g. fill level > 100% capped to 100%, negative values clipped to 0).

#### FR-3: Data Analysis & Visualization
- **FR-3.1:** System shall generate descriptive statistics (mean, median fill level per zone/waste type).
- **FR-3.2:** System shall display fill-level distribution as a histogram.
- **FR-3.3:** System shall display waste-type breakdown as a pie chart.
- **FR-3.4:** System shall display fill-level trend over time as a line chart.
- **FR-3.5:** System shall display overflow frequency by location as a bar chart / heatmap.

#### FR-4: Priority Bin Identification
- **FR-4.1:** System shall assign a priority score to each bin based on Fill Level category and Overflow Status.
- **FR-4.2:** System shall rank bins and output a sorted 'Priority Collection List' (Critical first).
- **FR-4.3:** (Optional/ML) System shall support a trained Random Forest classifier as an alternative to rule-based scoring.

#### FR-5: Route Optimization
- **FR-5.1:** System shall take the Priority Collection List and generate a visiting order that minimizes total travel distance.
- **FR-5.2:** System shall support single-vehicle route (Nearest Neighbor heuristic or Google OR-Tools TSP solver).
- **FR-5.3:** System shall display the generated route on an interactive OpenStreetMap/Folium map.
- **FR-5.4:** System shall estimate and display total route distance and compare against a naive/fixed-order route (% distance reduction).

#### FR-6: Dashboard
- **FR-6.1:** System shall present all visualizations, priority list, and the route on a single Streamlit dashboard.
- **FR-6.2:** System shall allow filtering by date range, zone, or waste type.
- **FR-6.3:** System shall allow export of the Priority Collection List as CSV/PDF.

#### FR-7: Reporting & Insights (Optional LLM-assisted)
- **FR-7.1:** System may generate a natural-language summary of the day's priority bins and trends using a local LLM (Llama 3.2 3B via Ollama).
- **FR-7.2:** System shall provide fallback analytical summaries when local LLM is offline.

#### FR-8: Forecasting (Stretch Goal)
- **FR-8.1:** System may predict when a bin will reach Critical fill level based on historical trends (regression/time-series model).
