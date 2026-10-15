"""
Smart Waste Management & Collection Optimization Dashboard.
Main Streamlit Application Entry Point.
"""

import os
import sys

# Ensure repository root is in python module search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import pandas as pd
import streamlit as st

# Setup page config
st.set_page_config(
    page_title="Smart Waste Management System",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Project module imports
from src.database import DatabaseManager, DEFAULT_DB_PATH
from src.preprocessing import clean_and_preprocess
from src.data_loader import generate_synthetic_dataset, save_dataset_to_csv, BASE_LAT, BASE_LON
from src.analysis import compute_summary_kpis, compute_zone_statistics, compute_waste_type_breakdown
from src.priority_scoring import calculate_rule_based_priority, predict_ml_priority
from src.route_optimizer import DEFAULT_DEPOT, solve_ortools_tsp, solve_nearest_neighbor_tsp, compare_routes
from src.forecasting import batch_forecast_all_bins
from src.utils import generate_pdf_report, query_ollama_llm, generate_heuristic_executive_summary
from dashboard.filters import render_sidebar_filters
from dashboard.components import render_kpi_cards, render_alert_banner, render_priority_table, render_export_buttons
from dashboard.charts import (
    plot_fill_distribution, plot_waste_type_breakdown,
    plot_fill_trend_over_time, plot_overflow_hotspots, plot_route_comparison
)
from dashboard.maps import render_collection_map, display_map


@st.cache_data(ttl=60)
def load_db_data():
    """Load latest records and historical readings from SQLite database."""
    db = DatabaseManager(DEFAULT_DB_PATH)
    latest_df = db.get_latest_readings_df()
    all_readings_df = db.get_all_readings_df()
    return latest_df, all_readings_df


def main():
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 10px;">
            <h1 style="margin: 0; color: #1b5e20;">♻️ Smart Waste Management & Collection Optimization</h1>
        </div>
        <p style="color: #555; margin-top: -5px;">
            Data-Driven Municipal & Campus Fleet Monitoring, Rule/ML Priority Scoring, and Heuristic Route Optimization
        </p>
        """,
        unsafe_allow_html=True
    )

    # 1. Load Data
    try:
        latest_df, all_readings_df = load_db_data()
    except Exception as e:
        st.error(f"Error accessing database: {e}. Falling back to sample dataset.")
        sample_path = "data/sample/sample_bin_data.csv"
        if os.path.exists(sample_path):
            latest_df = pd.read_csv(sample_path).drop_duplicates(subset=["bin_id"], keep="last")
            all_readings_df = pd.read_csv(sample_path)
        else:
            latest_df, all_readings_df = pd.DataFrame(), pd.DataFrame()

    if latest_df.empty:
        st.warning("No bin data found in database. Generating synthetic fleet data...")
        synth_df = generate_synthetic_dataset(num_bins=25, days_of_history=3)
        cleaned_synth, _ = clean_and_preprocess(synth_df)
        db = DatabaseManager(DEFAULT_DB_PATH)
        bins_meta = cleaned_synth.drop_duplicates(subset=["bin_id"])[
            ["bin_id", "location_name", "latitude", "longitude", "waste_type", "collection_frequency"]
        ].to_dict(orient="records")
        db.bulk_insert_bins(bins_meta)
        db.bulk_insert_readings(cleaned_synth[["bin_id", "fill_level", "fill_category", "overflow_status", "timestamp"]].to_dict(orient="records"))
        st.rerun()

    # 2. Sidebar Filters
    filtered_df, filter_params = render_sidebar_filters(latest_df)

    # Database quick refresh button in sidebar
    if st.sidebar.button("🔄 Refresh Data / Clear Cache"):
        st.cache_data.clear()
        st.rerun()

    # Model choice toggle
    model_choice = st.sidebar.selectbox(
        "Priority Model Type",
        options=["Rule-Based Formula (MVP)", "Random Forest ML Classifier"],
        index=0
    )

    # 3. Calculate Priority Scores
    if model_choice == "Random Forest ML Classifier":
        scored_df = predict_ml_priority(filtered_df)
    else:
        scored_df = calculate_rule_based_priority(
            filtered_df,
            threshold_score=filter_params.get("priority_threshold", 40.0)
        )

    priority_bins = scored_df[scored_df["needs_collection"]].to_dict(orient="records")

    # 4. Route Optimization
    return_to_depot = filter_params.get("return_to_depot", True)
    if filter_params.get("routing_algo") == "Nearest Neighbor Heuristic":
        opt_route_res = solve_nearest_neighbor_tsp(DEFAULT_DEPOT, priority_bins, return_to_depot)
    else:
        opt_route_res = solve_ortools_tsp(DEFAULT_DEPOT, priority_bins, return_to_depot)

    route_comparison = compare_routes(DEFAULT_DEPOT, priority_bins, opt_route_res)
    kpis = compute_summary_kpis(scored_df)

    # 5. Top Alert Banner & Metric Cards
    render_alert_banner(kpis["overflow_bins"], kpis["critical_bins"])
    render_kpi_cards(kpis, route_comparison)
    st.markdown("<br/>", unsafe_allow_html=True)

    # 6. Tabbed Dashboard Layout
    tab_map, tab_queue, tab_analytics, tab_route, tab_forecast, tab_ai, tab_db = st.tabs([
        "🗺️ Fleet Map & Routes",
        "📋 Priority Dispatch Queue",
        "📊 Exploratory Analytics",
        "⚡ Route Optimization Benchmark",
        "🔮 Fill Forecasting (Stretch)",
        "🤖 AI Summary & Assistant",
        "💾 Data Ingestion & Database"
    ])

    # --- TAB 1: FLEET MAP & ROUTES ---
    with tab_map:
        st.subheader("Interactive Collection Dispatch Map")
        st.caption("Live spatial view of bins color-coded by fill category with optimized vehicle sequence.")

        col_map_view, col_route_list = st.columns([2.2, 1])
        with col_map_view:
            folium_map = render_collection_map(
                bins_df=scored_df,
                route_points=opt_route_res["route"],
                depot_info=DEFAULT_DEPOT,
                center_coords=(DEFAULT_DEPOT["latitude"], DEFAULT_DEPOT["longitude"])
            )
            display_map(folium_map, height=520)

        with col_route_list:
            st.markdown("#### 🚚 Route Turn-by-Turn Order")
            st.info(f"**Solver:** {opt_route_res['method']}\\n\\n**Total Distance:** {opt_route_res['total_distance_km']} km")
            
            route_stops = []
            for idx, stop in enumerate(opt_route_res["route"]):
                route_stops.append({
                    "Stop #": idx,
                    "Bin ID": stop.get("bin_id"),
                    "Location": stop.get("location_name")[:20],
                    "Fill %": f"{stop.get('fill_level', 0.0):.1f}%" if stop.get("bin_id") != "DEPOT" else "Depot"
                })
            st.dataframe(pd.DataFrame(route_stops), hide_index=True, use_container_width=True, height=440)

    # --- TAB 2: PRIORITY DISPATCH QUEUE ---
    with tab_queue:
        st.subheader("Ranked Priority Collection List")
        st.caption("Sorted queue of bins requiring immediate collection based on fill levels and overflow status.")
        render_priority_table(scored_df)
        st.markdown("---")
        render_export_buttons(scored_df[scored_df["needs_collection"]])

    # --- TAB 3: EXPLORATORY ANALYTICS ---
    with tab_analytics:
        st.subheader("Descriptive Fleet Analytics")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.plotly_chart(plot_fill_distribution(scored_df), use_container_width=True)
        with col_c2:
            st.plotly_chart(plot_waste_type_breakdown(scored_df), use_container_width=True)

        col_c3, col_c4 = st.columns(2)
        with col_c3:
            st.plotly_chart(plot_overflow_hotspots(scored_df), use_container_width=True)
        with col_c4:
            st.plotly_chart(plot_fill_trend_over_time(all_readings_df), use_container_width=True)

    # --- TAB 4: ROUTE OPTIMIZATION BENCHMARK ---
    with tab_route:
        st.subheader("Route Efficiency & Savings Comparison")
        st.caption("Benchmark comparing the optimized TSP route against conventional naive sequential pickup order.")

        col_b1, col_b2 = st.columns([1.5, 1])
        with col_b1:
            st.plotly_chart(plot_route_comparison(route_comparison), use_container_width=True)
        with col_b2:
            st.markdown("#### 📈 Key Optimization Gains")
            st.write(f"- **Naive Route Distance:** {route_comparison['naive_distance_km']} km")
            st.write(f"- **Optimized Route Distance:** {route_comparison['optimized_distance_km']} km")
            st.write(f"- **Net Distance Saved:** {route_comparison['distance_reduction_km']} km")
            st.write(f"- **Efficiency Gain:** **{route_comparison['distance_reduction_pct']}%**")
            st.write(f"- **Est. Diesel Fuel Saved:** ~{route_comparison['estimated_fuel_saved_liters']} Liters")
            st.write(f"- **CO2 Emissions Avoided:** ~{route_comparison['estimated_co2_avoided_kg']} kg")
            st.success("Significant fleet fuel and operational expenditure reduction demonstrated!")

    # --- TAB 5: PREDICTIVE FILL FORECASTING ---
    with tab_forecast:
        st.subheader("Predictive Fill-Level Forecasting (Stretch Goal)")
        st.caption("Linear trend analysis modeling rate of accumulation to predict time until Critical fill (≥86%).")
        forecast_df = batch_forecast_all_bins(all_readings_df)
        if not forecast_df.empty:
            st.dataframe(
                forecast_df,
                column_config={
                    "bin_id": st.column_config.TextColumn("Bin ID"),
                    "location_name": st.column_config.TextColumn("Location"),
                    "current_fill": st.column_config.ProgressColumn("Current Fill", min_value=0, max_value=100, format="%.1f%%"),
                    "hourly_rate": st.column_config.NumberColumn("Hourly Rate (%/hr)", format="%.2f"),
                    "hours_to_critical": st.column_config.NumberColumn("Hours to Critical", format="%.1f hrs"),
                    "urgency": st.column_config.TextColumn("Urgency Level")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Insufficient historical time-series data to run forecasting.")

    # --- TAB 6: AI SUMMARY & ASSISTANT ---
    with tab_ai:
        st.subheader("AI Executive Summary & Fleet Assistant")
        st.caption("Automated report generation powered by Ollama (Llama 3.2 3B) or intelligent rule-based analytics engine.")

        col_ai_btn, _ = st.columns([1, 2])
        with col_ai_btn:
            run_ai = st.button("✨ Generate Fresh Executive AI Summary", use_container_width=True)

        if run_ai or "ai_summary" not in st.session_state:
            # Check Ollama first
            prompt = (
                f"You are an AI Smart Waste Operations Assistant. Summarize this daily status in 3 concise bullet points:\\n"
                f"Total Bins: {kpis['total_bins']}, Critical Bins: {kpis['critical_bins']}, "
                f"Active Overflows: {kpis['overflow_bins']}, Route Distance: {route_comparison['optimized_distance_km']} km, "
                f"Efficiency Gain: {route_comparison['distance_reduction_pct']}%. Recommend immediate operational dispatch actions."
            )
            ollama_res = query_ollama_llm(prompt)
            if ollama_res.get("success"):
                st.session_state["ai_summary"] = ollama_res["response"]
                st.session_state["ai_source"] = ollama_res["source"]
            else:
                st.session_state["ai_summary"] = generate_heuristic_executive_summary(
                    {**kpis, **route_comparison}
                )
                st.session_state["ai_source"] = "Analytics Heuristic Engine (Ollama Offline)"

        st.markdown(st.session_state.get("ai_summary", ""))
        st.caption(f"Generated via: *{st.session_state.get('ai_source', 'Heuristic')}*")

    # --- TAB 7: DATA INGESTION & DATABASE ---
    with tab_db:
        st.subheader("Data Ingestion & SQLite Management")
        st.caption("Upload fresh Google Forms or CSV exports to clean, validate, and synchronize directly into SQLite.")

        uploaded_file = st.file_uploader("Upload Bin Readings (CSV / Google Form Export)", type=["csv"])
        if uploaded_file is not None:
            raw_upload = pd.read_csv(uploaded_file)
            st.write("Uploaded Raw Data Preview:", raw_upload.head(4))
            if st.button("🚀 Clean & Ingest into Database"):
                cleaned_upload, rep = clean_and_preprocess(raw_upload)
                st.write("Preprocessing Ingestion Report:", rep)
                db = DatabaseManager(DEFAULT_DB_PATH)
                if not cleaned_upload.empty:
                    bins_meta = cleaned_upload.drop_duplicates(subset=["bin_id"])[
                        ["bin_id", "location_name", "latitude", "longitude", "waste_type", "collection_frequency"]
                    ].to_dict(orient="records")
                    db.bulk_insert_bins(bins_meta)
                    db.bulk_insert_readings(cleaned_upload[["bin_id", "fill_level", "fill_category", "overflow_status", "timestamp"]].to_dict(orient="records"))
                    st.success("Successfully processed and saved to database!")
                    st.cache_data.clear()

        st.markdown("---")
        st.markdown("#### Live SQLite Database Tables")
        show_table = st.selectbox("Inspect Table:", ["bins", "bin_readings", "priority_scores"])
        db = DatabaseManager(DEFAULT_DB_PATH)
        with db.get_connection() as conn:
            table_preview = pd.read_sql_query(f"SELECT * FROM {show_table} LIMIT 50;", conn)
        st.dataframe(table_preview, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 📦 Download Entire Project Package")
        st.caption("Download the complete source code, sample datasets, SQLite database, notebooks, and models as a single ZIP file.")
        zip_file_path = os.path.join(os.path.dirname(__file__), "smart-waste-management.zip")
        if os.path.exists(zip_file_path):
            with open(zip_file_path, "rb") as zf:
                st.download_button(
                    label="📦 Download Complete Project (.zip)",
                    data=zf.read(),
                    file_name="smart-waste-management.zip",
                    mime="application/zip",
                    use_container_width=True
                )
        else:
            st.info("ZIP package archive being prepared...")


if __name__ == "__main__":
    main()
