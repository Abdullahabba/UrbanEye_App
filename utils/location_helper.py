import streamlit as st
import streamlit.components.v1 as components

def get_live_location():
    """
    Captures browser GPS coordinates and reloads the page with query parameters.
    """
    # 1. Check if GPS coordinates already exist in URL query parameters
    params = st.query_params
    if "lat" in params and "lon" in params:
        try:
            lat = float(params["lat"])
            lon = float(params["lon"])
            return lat, lon
        except ValueError:
            pass

    # 2. HTML/JS Component with a button to force GPS capture and update URL
    location_html = """
    <div style="font-family: sans-serif; padding: 10px; background: #f0f2f6; border-radius: 8px; text-align: center; border: 1px solid #d6d6d6;">
        <p id="gps-status" style="font-size: 13px; color: #31333F; margin: 0 0 8px 0; font-weight: 500;">🛰️ Live GPS Location Required</p>
        <button onclick="getGPS()" style="background: #FF4B4B; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">📍 Detect My Live GPS</button>
    </div>
    <script>
    function getGPS() {
        const statusEl = document.getElementById('gps-status');
        if (navigator.geolocation) {
            statusEl.innerHTML = "🛰️ Connecting to satellite / GPS...";
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    statusEl.innerHTML = "✅ GPS Locked! Updating app...";
                    
                    // Append coordinates to URL query parameters and reload page
                    const url = new URL(window.parent.location.href);
                    url.searchParams.set('lat', lat);
                    url.searchParams.set('lon', lon);
                    window.parent.location.href = url.toString();
                },
                (error) => {
                    statusEl.innerHTML = "⚠️ Location permission denied. Please allow location in browser.";
                    console.warn("Geolocation error: ", error.message);
                },
                { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
            );
        } else {
            statusEl.innerHTML = "❌ Geolocation is not supported by this browser.";
        }
    }
    </script>
    """
    components.html(location_html, height=90)
    return None, None
