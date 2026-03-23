import streamlit as st

from config.settings import settings
from services.current_air_quality_service import get_current_air_quality_for_city


def render_success_result(result: dict) -> None:
    st.success("Current air quality retrieved successfully.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("PM2.5", f"{result['pm25']} µg/m³")

    with col2:
        st.metric("Nearest Station", result["nearest_station"])

    with col3:
        st.metric("Distance", f"{result['distance_km']} km")

    st.markdown("### Details")
    st.write(f"**Query location:** {result['query_location']}")
    st.write(f"**Resolved location:** {result['resolved_location']}")
    st.write(f"**Observed at:** {result['observed_time']}")
    st.write(f"**Latitude:** {result['latitude']}")
    st.write(f"**Longitude:** {result['longitude']}")


def render_error_result(result: dict) -> None:
    st.error("Failed to retrieve current air quality.")
    st.write(f"**Query location:** {result.get('query_location')}")
    st.write(f"**Reason:** {result.get('error')}")


def main() -> None:
    st.set_page_config(
        page_title="Air Quality Chatbot",
        page_icon="🌬️",
        layout="wide",
    )

    st.title("🌬️ Air Quality Chatbot")
    st.caption("Current PM2.5 lookup using OpenAQ")

    try:
        settings.validate()
    except Exception as e:
        st.error(f"Configuration error: {e}")
        st.stop()

    with st.sidebar:
        st.header("Settings")
        st.write("**Data source:** OpenAQ")
        st.write(f"**API base URL:** {settings.api.openaq.base_url}")
        st.write(f"**Station metadata:** {settings.paths.station_metadata_path}")

    st.markdown("## Current Air Quality")
    city_name = st.text_input(
        "Enter a city or location",
        value="Washington, DC",
        placeholder="e.g. Washington, DC; Seoul; Nairobi",
    )

    if st.button("Get Current PM2.5", use_container_width=True):
        if not city_name.strip():
            st.warning("Please enter a city or location.")
            st.stop()

        with st.spinner("Fetching current air quality..."):
            result = get_current_air_quality_for_city(city_name.strip())

        if result["success"]:
            render_success_result(result)
        else:
            render_error_result(result)


if __name__ == "__main__":
    main()