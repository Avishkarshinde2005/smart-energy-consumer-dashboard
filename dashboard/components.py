"""
Reusable UI Components for Streamlit Dashboard.
Implements KPI metric cards, status badges, alert banners, and export buttons.
"""

from typing import Dict, Any, List
import pandas as pd
import streamlit as st


def render_kpi_cards(kpis: Dict[str, Any], route_metrics: Dict[str, Any]) -> None:
    """
    Render top KPI metric cards with modern styling.
    """
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Total Active Bins",
            value=kpis.get("total_bins", 0),
            delta="Monitored Fleet"
        )

    with col2:
        st.metric(
            label="Critical Bins (≥86%)",
            value=kpis.get("critical_bins", 0),
            delta=f"{kpis.get('overflow_bins', 0)} Overflows",
            delta_color="inverse"
        )

    with col3:
        st.metric(
            label="Fleet Avg Fill Level",
            value=f"{kpis.get('avg_fill', 0.0)}%",
            delta=f"Median {kpis.get('median_fill', 0.0)}%"
        )

    with col4:
        st.metric(
            label="Optimized Route Dist.",
            value=f"{route_metrics.get('optimized_distance_km', 0.0)} km",
            delta=f"-{route_metrics.get('distance_reduction_km', 0.0)} km vs naive"
        )

    with col5:
        st.metric(
            label="Route Efficiency Gain",
            value=f"{route_metrics.get('distance_reduction_pct', 0.0)}%",
            delta=f"~{route_metrics.get('estimated_fuel_saved_liters', 0.0)}L Fuel Saved"
        )


def render_alert_banner(overflow_count: int, critical_count: int) -> None:
    """
    Render attention-grabbing banner if critical or overflow situations exist.
    """
    if overflow_count > 0:
        st.error(
            f"🚨 **URGENT ATTENTION REQUIRED:** **{overflow_count} waste bins are currently OVERFLOWING** "
            f"and **{critical_count} bins** have reached critical capacity. Collection vehicle dispatch recommended immediately!"
        )
    elif critical_count > 0:
        st.warning(
            f"⚠️ **HIGH CAPACITY ALERT:** **{critical_count} waste bins** have reached critical capacity (≥86%). "
            "Please dispatch collection fleet to priority route."
        )
    else:
        st.success("✅ **ALL CLEAR:** Fleet capacity within normal operating limits. No urgent overflow risks detected.")


def render_priority_table(priority_df: pd.DataFrame) -> None:
    """
    Render formatted priority collection queue.
    """
    if priority_df.empty:
        st.info("No bins currently flagged for priority pickup under current filter criteria.")
        return

    display_cols = [
        "rank", "bin_id", "location_name", "waste_type", "fill_level",
        "fill_category", "overflow_status", "priority_score"
    ]
    cols_present = [c for c in display_cols if c in priority_df.columns]
    
    st.dataframe(
        priority_df[cols_present],
        column_config={
            "rank": st.column_config.NumberColumn("Rank", format="#%d"),
            "bin_id": st.column_config.TextColumn("Bin ID"),
            "location_name": st.column_config.TextColumn("Location"),
            "waste_type": st.column_config.TextColumn("Type"),
            "fill_level": st.column_config.ProgressColumn("Fill Level (%)", min_value=0, max_value=100, format="%.1f%%"),
            "fill_category": st.column_config.TextColumn("Category"),
            "overflow_status": st.column_config.CheckboxColumn("Overflow?"),
            "priority_score": st.column_config.NumberColumn("Priority Score", format="%.2f")
        },
        use_container_width=True,
        hide_index=True
    )


def render_export_buttons(priority_df: pd.DataFrame, pdf_path: str = "reports/priority_collection_report.pdf") -> None:
    """
    Provide one-click download buttons for CSV and PDF dispatch reports (FR-6.3).
    """
    col1, col2 = st.columns(2)

    with col1:
        csv_bytes = priority_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Priority List (CSV)",
            data=csv_bytes,
            file_name="priority_collection_list.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col2:
        try:
            import os
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    label="📄 Download Dispatch Report (PDF)",
                    data=pdf_bytes,
                    file_name="priority_collection_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.button("📄 PDF Generating...", disabled=True, use_container_width=True)
        except Exception as e:
            st.warning(f"PDF export temporarily unavailable: {e}")
