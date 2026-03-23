import streamlit as st

from config.settings import settings
from services.advisory_service import recommend_outdoor_activity
from services.current_air_quality_service import get_current_air_quality_for_city
from services.historical_air_quality_service import get_historical_comparison_for_cities
from services.plot_service import build_pm25_timeseries_plot
from services.query_understanding import understand_query


WELCOME_MESSAGE = """Hello! I can help with air quality questions.

Examples:
- What is the current air quality in Washington, DC?
- Do you recommend outdoor activity in DC today?
- Compare DC and NYC over the last 10 days
- What is PM2.5?
"""


def ensure_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": WELCOME_MESSAGE,
            }
        ]

    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None


def reset_chat() -> None:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": WELCOME_MESSAGE,
        }
    ]
    st.session_state.analysis_result = None


def add_message(role: str, content: str) -> None:
    st.session_state.messages.append({"role": role, "content": content})


def render_messages() -> None:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def render_current_analysis(payload: dict) -> None:
    if not payload["success"]:
        st.error(payload["error"])
        return

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("PM2.5", f"{payload['pm25']} µg/m³")

    with c2:
        st.metric("Nearest Station", payload["nearest_station"])

    with c3:
        st.metric("Distance", f"{payload['distance_km']} km")

    st.markdown("### Details")
    st.write(f"**Resolved location:** {payload['resolved_location']}")
    st.write(f"**Observed at:** {payload['observed_time']}")
    st.write(f"**Location confidence:** {payload['location_confidence']}")


def render_historical_analysis(payload: dict) -> None:
    if not payload["success"]:
        st.error(payload["error"])
        return

    fig = build_pm25_timeseries_plot(payload["dataframe"])
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Summary")
    st.dataframe(payload["summary"], use_container_width=True)


def render_general_explanation(payload: dict) -> None:
    st.info(payload["message"])


def render_analysis_space() -> None:
    st.markdown("---")
    st.subheader("Analysis Space")

    result = st.session_state.analysis_result
    if result is None:
        st.info("Charts, tables, and air quality analysis outputs will appear here.")
        return

    result_type = result["type"]
    payload = result["payload"]

    if result_type in {"current", "current_advisory"}:
        render_current_analysis(payload)
    elif result_type == "historical_compare":
        render_historical_analysis(payload)
    elif result_type == "general_explanation":
        render_general_explanation(payload)
    else:
        st.warning("No analysis renderer is available for this result type.")


def handle_general_explanation() -> None:
    message = (
        "PM2.5 refers to fine particulate matter with a diameter of 2.5 micrometers "
        "or smaller. These particles can penetrate deep into the lungs and may affect "
        "health, especially for sensitive groups."
    )
    add_message("assistant", message)
    st.session_state.analysis_result = {
        "type": "general_explanation",
        "payload": {"message": message},
    }


def handle_current_lookup(location_texts: list[str], advisory: bool = False) -> None:
    if not location_texts:
        assistant_text = (
            "I could not identify a location in your question. "
            "Please specify a city or place, for example: "
            "**Do you recommend outdoor activity in Washington, DC today?**"
        )
        add_message("assistant", assistant_text)
        st.session_state.analysis_result = None
        return

    raw_location = location_texts[0]
    result = get_current_air_quality_for_city(raw_location)

    if result["success"]:
        if advisory:
            recommendation = recommend_outdoor_activity(result["pm25"])
            assistant_text = (
                f"Current PM2.5 near **{result['query_location']}** is "
                f"**{result['pm25']} µg/m³**.\n\n"
                f"**Recommendation:** {recommendation}\n\n"
                f"- Resolved location: {result['resolved_location']}\n"
                f"- Nearest station: {result['nearest_station']} ({result['distance_km']} km)\n"
                f"- Observed at: {result['observed_time']}\n"
                f"- Location confidence: {result['location_confidence']}"
            )
        else:
            assistant_text = (
                f"Current PM2.5 near **{result['query_location']}** is "
                f"**{result['pm25']} µg/m³**.\n\n"
                f"- Resolved location: {result['resolved_location']}\n"
                f"- Nearest station: {result['nearest_station']} ({result['distance_km']} km)\n"
                f"- Observed at: {result['observed_time']}\n"
                f"- Location confidence: {result['location_confidence']}"
            )
    else:
        assistant_text = (
            "I could not retrieve air quality information.\n\n"
            f"Reason: {result['error']}"
        )

    add_message("assistant", assistant_text)
    st.session_state.analysis_result = {
        "type": "current_advisory" if advisory else "current",
        "payload": result,
    }


def handle_historical_compare(location_texts: list[str], days: int) -> None:
    if len(location_texts) < 1:
        add_message(
            "assistant",
            "I could not identify the location(s) to compare. Please specify one or two cities."
        )
        st.session_state.analysis_result = None
        return

    result = get_historical_comparison_for_cities(
        raw_locations=location_texts,
        days=days,
    )

    if result["success"]:
        station_lines = "\n".join(
            f"- {row['query_location']} → {row['resolved_location']} | "
            f"{row['station_name']} ({row['distance_km']} km)"
            for _, row in result["summary"].iterrows()
        )

        assistant_text = (
            f"I compared **daily average PM2.5** over the last **{days} calendar days**.\n\n"
            f"Locations and stations used:\n{station_lines}"
        )
    else:
        assistant_text = (
            "I could not generate the requested comparison.\n\n"
            f"Reason: {result['error']}"
        )

    add_message("assistant", assistant_text)
    st.session_state.analysis_result = {
        "type": "historical_compare",
        "payload": result,
    }


def handle_query(user_input: str) -> None:
    parsed = understand_query(user_input)
    intent = parsed["intent"]

    if intent == "general_explanation":
        handle_general_explanation()
        return

    if intent == "current_lookup":
        handle_current_lookup(
            location_texts=parsed["location_texts"],
            advisory=False,
        )
        return

    if intent == "current_advisory":
        handle_current_lookup(
            location_texts=parsed["location_texts"],
            advisory=True,
        )
        return

    if intent == "historical_compare":
        handle_historical_compare(
            location_texts=parsed["location_texts"],
            days=parsed["days"],
        )
        return

    add_message(
        "assistant",
        "I can help with current air quality, outdoor activity recommendations, and recent PM2.5 comparisons."
    )
    st.session_state.analysis_result = None


def main() -> None:
    st.set_page_config(
        page_title=settings.ui.title,
        page_icon=settings.ui.page_icon,
        layout="wide",
    )

    try:
        settings.validate()
    except Exception as e:
        st.error(f"Configuration error: {e}")
        st.stop()

    ensure_state()

    with st.sidebar:
        st.title("Air Quality Chatbot")
        st.caption("OpenAQ demo")

        if st.button("New Chat", use_container_width=True):
            reset_chat()
            st.rerun()

        st.markdown("---")
        st.write("**Capabilities**")
        st.write("- Current PM2.5 lookup")
        st.write("- Outdoor activity recommendation")
        st.write("- Recent PM2.5 comparison plot")

    st.title("🌬️ Air Quality Chatbot")
    st.caption("Chat-based OpenAQ demo with an integrated analysis workspace")

    render_messages()
    render_analysis_space()

    user_input = st.chat_input(
        "Ask about air quality, outdoor activity, or PM2.5 comparisons..."
    )

    if user_input:
        add_message("user", user_input)
        handle_query(user_input)
        st.rerun()


if __name__ == "__main__":
    main()