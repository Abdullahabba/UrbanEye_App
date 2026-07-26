import streamlit.components.v1 as components
import streamlit as st

def get_live_location():
    """
    Fetches real-time authentic GPS coordinates from the user's browser.
    """
    location_component = """
    <div>
        <p id="status" style="font-size: 14px; color: #555; font-family: sans-serif;">Fetching real-time GPS location...</p>
    </div>
    <script>
    function getLocation() {
        const status = document.getElementById('status');
        if (!navigator.geolocation) {
            status.innerHTML = "Geolocation is not supported by your browser";
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                status.innerHTML = "✅ Live GPS Location Acquired!";
                
                // Send data back to Streamlit via parent window postMessage
                const data = { lat: lat, lon: lon };
                window.parent.postMessage({ type: 'streamlit:set_component_value', value: data }, "*");
            },
            (error) => {
                status.innerHTML = "⚠️ Location access denied or unavailable. Using default.";
                console.warn(`ERROR(${error.code}): ${error.message}`);
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    }
    getLocation();
    </script>
    """
    # Render component and catch returned value
    loc_data = components.html(location_component, height=40)
    return loc_data
