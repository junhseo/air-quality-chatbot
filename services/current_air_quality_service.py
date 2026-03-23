from typing import Any, Dict
import pandas as pd

from config.settings import settings
from services.location_resolver import resolve_location
from services.station_service import find_nearest_station
from services.openaq_client import fetch_current_openaq


def load_station_data() -> pd.DataFrame:
    return pd.read_csv(settings.paths.station_metadata_path)


def get_current_air_quality_for_city(raw_location: str) -> Dict[str, Any]:
    try:
        station_data = load_station_data()

        resolved = resolve_location(raw_location)
        if not resolved["success"]:
            return {
                "success": False,
                "query_location": raw_location,
                "resolved_location": None,
                "latitude": None,
                "longitude": None,
                "nearest_station": None,
                "distance_km": None,
                "pm25": None,
                "observed_time": None,
                "location_confidence": 0.0,
                "location_candidates": [],
                "needs_clarification": False,
                "error": resolved["error"],
            }

        if resolved["needs_clarification"]:
            return {
                "success": False,
                "query_location": raw_location,
                "resolved_location": None,
                "latitude": None,
                "longitude": None,
                "nearest_station": None,
                "distance_km": None,
                "pm25": None,
                "observed_time": None,
                "location_confidence": resolved["confidence"],
                "location_candidates": resolved["candidates"],
                "needs_clarification": True,
                "error": (
                    f"Location is ambiguous. Did you mean one of these: "
                    f"{', '.join(resolved['candidates'])}?"
                ),
            }

        nearest_station, distance_km = find_nearest_station(
            lat=resolved["latitude"],
            lon=resolved["longitude"],
            station_data=station_data,
            intent="current",
        )

        openaq_result = fetch_current_openaq(nearest_station)

        if not openaq_result["success"]:
            return {
                "success": False,
                "query_location": raw_location,
                "resolved_location": resolved["resolved_name"],
                "latitude": resolved["latitude"],
                "longitude": resolved["longitude"],
                "nearest_station": nearest_station.get("sitename"),
                "distance_km": round(distance_km, 2),
                "pm25": None,
                "observed_time": None,
                "location_confidence": resolved["confidence"],
                "location_candidates": resolved["candidates"],
                "needs_clarification": False,
                "error": openaq_result["error"],
            }

        return {
            "success": True,
            "query_location": raw_location,
            "resolved_location": resolved["resolved_name"],
            "latitude": resolved["latitude"],
            "longitude": resolved["longitude"],
            "nearest_station": openaq_result["station_name"],
            "distance_km": round(distance_km, 2),
            "pm25": openaq_result["value"],
            "observed_time": openaq_result["readable_time"],
            "location_confidence": resolved["confidence"],
            "location_candidates": resolved["candidates"],
            "needs_clarification": False,
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "query_location": raw_location,
            "resolved_location": None,
            "latitude": None,
            "longitude": None,
            "nearest_station": None,
            "distance_km": None,
            "pm25": None,
            "observed_time": None,
            "location_confidence": 0.0,
            "location_candidates": [],
            "needs_clarification": False,
            "error": str(e),
        }