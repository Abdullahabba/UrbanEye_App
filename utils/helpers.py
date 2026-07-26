import streamlit.components.v1 as components
import streamlit as st

def get_live_location():
    """
    Forces browser geolocation capture and securely returns coordinates to Streamlit.
    """
    location_html = """
    <div style="font-family: sans-serif; padding: 5px; background: #f0f2f6; border-radius: 5px; margin-bottom: 10px;">
        <span id="gps-status" style="font-size: 13px; color: #31333F;">🛰️ Acquiring live GPS coordinates from browser...</span>
    </div>
    <script>
    const statusEl = document.getElementById('gps-status');

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                statusEl.innerHTML = "✅ Live GPS Locked: (" + lat.toFixed(4) + ", " + lon.toFixed(4) + ")";
                
                // Streamlit component communication protocol
                const data = { lat: lat, lon: lon };
                window.parent.postMessage({ type: 'streamlit:set_component_value', value: data }, "*");
            },
            (error) => {
                statusEl.innerHTML = "⚠️ GPS Access Blocked/Unavailable. Using default sector coordinates.";
                console.warn("Geolocation error: ", error.message);
            },
            { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
        );
    } else {
        statusEl.innerHTML = "❌ Geolocation is not supported by this browser.";
    }
    </script>
    """
    # Render component and return captured dictionary if available
    val = components.html(location_html, height=45)
    return val
