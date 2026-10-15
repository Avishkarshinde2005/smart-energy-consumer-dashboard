"""
Geospatial Mapping Module for Streamlit Dashboard.
Implements Functional Requirement FR-5.3:
- Interactive OpenStreetMap via Folium
- Color-coded bin status markers
- Depot icon marker
- Optimized collection route polyline with numbered waypoint badges
"""

from typing import List, Dict, Any, Optional
import folium
from folium import plugins
import streamlit as st


COLOR_LOOKUP = {
    "Low": "green",
    "Medium": "blue",
    "High": "orange",
    "Critical": "red"
}


def render_collection_map(
    bins_df: Any,
    route_points: Optional[List[Dict[str, Any]]] = None,
    depot_info: Optional[Dict[str, Any]] = None,
    center_coords: tuple = (18.5204, 73.8567),
    zoom_start: int = 14
) -> folium.Map:
    """
    Build Folium Map with bin markers, depot, and collection path.
    """
    m = folium.Map(
        location=center_coords,
        zoom_start=zoom_start,
        tiles="OpenStreetMap"
    )

    # 1. Add Depot Marker
    if depot_info:
        folium.Marker(
            location=[depot_info["latitude"], depot_info["longitude"]],
            popup=f"<b>DEPOT:</b> {depot_info.get('location_name', 'Main Depot')}",
            tooltip="Central Collection Depot",
            icon=folium.Icon(color="black", icon="home", prefix="fa")
        ).add_to(m)

    # 2. Add All Bin Markers
    if not bins_df.empty:
        for _, row in bins_df.iterrows():
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            b_id = str(row["bin_id"])
            loc = str(row.get("location_name", "Unknown"))
            fill = float(row.get("fill_level", 0.0))
            cat = str(row.get("fill_category", "Low"))
            ovf = bool(row.get("overflow_status", False))
            score = float(row.get("priority_score", 0.0))

            color = "darkred" if ovf else COLOR_LOOKUP.get(cat, "blue")
            icon_name = "exclamation-triangle" if ovf else ("trash" if cat == "Critical" else "info-circle")

            popup_html = f"""
            <div style="font-family: sans-serif; min-width: 160px;">
                <h4 style="margin: 0 0 5px 0; color: #1b5e20;">{b_id}</h4>
                <b>Location:</b> {loc}<br/>
                <b>Fill Level:</b> {fill:.1f}% ({cat})<br/>
                <b>Overflow:</b> {'<span style="color:red;font-weight:bold;">YES</span>' if ovf else 'No'}<br/>
                <b>Priority Score:</b> {score:.1f}<br/>
                <b>Waste Type:</b> {row.get('waste_type', 'General')}
            </div>
            """

            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"{b_id}: {fill:.1f}% ({cat})",
                icon=folium.Icon(color=color, icon=icon_name, prefix="fa")
            ).add_to(m)

    # 3. Add Route Polyline and Sequenced Waypoint Badges
    if route_points and len(route_points) > 1:
        poly_coords = [[p["latitude"], p["longitude"]] for p in route_points]
        
        # Route path line
        folium.PolyLine(
            locations=poly_coords,
            color="#1565c0",
            weight=4,
            opacity=0.85,
            dash_array="6, 8"
        ).add_to(m)

        # Numbered stops
        for step_num, pt in enumerate(route_points):
            if pt.get("bin_id") == "DEPOT":
                continue
            folium.map.Marker(
                [pt["latitude"], pt["longitude"]],
                icon=folium.DivIcon(
                    icon_size=(24, 24),
                    icon_anchor=(12, 12),
                    html=f'<div style="font-size: 11pt; font-weight: bold; color: white; background-color: #0d47a1; border-radius: 50%; text-align: center; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">{step_num}</div>'
                )
            ).add_to(m)

    # Add Fullscreen & Layer control
    plugins.Fullscreen().add_to(m)
    return m


def display_map(m: folium.Map, height: int = 520) -> None:
    """
    Render Folium map in Streamlit.
    Uses streamlit_folium if available, otherwise falls back to native HTML component.
    """
    try:
        from streamlit_folium import folium_static
        folium_static(m, height=height)
    except ImportError:
        import streamlit.components.v1 as components
        html_data = m._repr_html_()
        components.html(html_data, height=height + 20)
