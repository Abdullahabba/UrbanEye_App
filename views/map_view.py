import streamlit as st
import pandas as pd
import pydeck as pdk

def render_map_page():
    st.title("🗺️ Municipal Hazard Heatmap & Map View")
    st.caption("Visualizing high-density risk zones and hazard hotspots across urban sectors.")

    # Mock historical or live detected hazard locations (Lahore / Iqbal Sector coordinates)
    data = pd.DataFrame({
        'lat': [31.4697, 31.4800, 31.4550, 31.5204, 31.5497, 31.4700, 31.4650, 31.5100, 31.4850],
        'lon': [74.2728, 74.2900, 74.2600, 74.3587, 74.3436, 74.2750, 74.2680, 74.3200, 74.2950],
        'weight': [10, 25, 5, 30, 15, 20, 8, 12, 18],
        'hazard': ['Pothole', 'Garbage Dump', 'Broken Pole', 'Illegal Dumping', 'Manhole Cover Missing', 'Pothole', 'Streetlight Out', 'Garbage Dump', 'Road Crack']
    })

    # Toggle between Heatmap and Individual Marker views
    col1, col2 = st.columns([2, 2])
    with col1:
        view_mode = st.radio("Select Map Layer Mode:", ["🔥 Density Heatmap", "📍 Individual Markers"], horizontal=True)
    with col2:
        selected_sector = st.selectbox("Filter by Sector / Zone:", ["All Sectors", "Iqbal Sector", "Gulberg Zone", "DHA Zone"])

    # Center coordinates for Lahore
    midpoint = (data['lat'].mean(), data['lon'].mean())

    if view_mode == "🔥 Density Heatmap":
        # PyDeck Heatmap Layer
        layer = pdk.Layer(
            "HeatmapLayer",
            data=data,
            get_position=["lon", "lat"],
            get_weight="weight",
            radius_pixels=60,
            intensity=1.5,
            threshold=0.1
        )
        tooltip = {"html": "<b>Municipal Hazard Hotspot</b>"}
    else:
        # PyDeck Scatterplot Layer for individual markers
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=data,
            get_position=["lon", "lat"],
            get_color='[220, 50, 50, 180]',
            get_radius=180,
            pickable=True
        )
        tooltip = {
            "html": "<b>Hazard Type:</b> {hazard}<br/><b>Severity Weight:</b> {weight}",
            "style": {"backgroundColor": "navy", "color": "white"}
        }

    # Render Deck Map
    r = pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(
            latitude=midpoint[0],
            longitude=midpoint[1],
            zoom=12.5,
            pitch=45,
        ),
        layers=[layer],
        tooltip=tooltip
    )

    st.pydeck_chart(r, use_container_width=True)

    # Summary Metrics below the map
    st.divider()
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Active Hotspots", "9 Zones")
    m2.metric("Highest Density Area", "Iqbal Sector (Block AA)")
    m3.metric("Response Status", "82% Addressed")
