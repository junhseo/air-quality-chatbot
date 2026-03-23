from typing import Any, Dict, List

import pandas as pd

from config.settings import settings
from services.current_air_quality_service import load_station_data
from services.location_resolver import resolve_location
from services.openaq_client import (
    fetch_raw_measurements_by_sensor,
    build_recent_daily_average,
)
from services.station_service import find_nearest_station


def get_historical_comparison_for_cities(raw_locations: List[str], days: int) -> Dict[str, Any]:
    try:
        days = max(1, min(days, settings.query.max_days))
        station_data = load_station_data()

        series_frames = []
        summary_rows = []

        for raw_location in raw_locations:
            resolved = resolve_location(raw_location)
            if not resolved["success"]:
                return {
                    "success": False,
                    "message": f"Could not resolve location: {raw_location}",
                    "dataframe": None,
                    "summary": None,
                    "error": resolved["error"],
                }

            if resolved["needs_clarification"]:
                return {
                    "success": False,
                    "message": f"Location is ambiguous: {raw_location}",
                    "dataframe": None,
                    "summary": None,
                    "error": f"Did you mean one of these: {', '.join(resolved['candidates'])}?",
                }

            nearest_station, distance_km = find_nearest_station(
                lat=resolved["latitude"],
                lon=resolved["longitude"],
                station_data=station_data,
                intent="current",
            )

            sensor_id = int(nearest_station["sensorId"])
            station_name = nearest_station.get("sitename", raw_location)

            raw_df = fetch_raw_measurements_by_sensor(
                sensor_id=sensor_id,
                days=days,
                limit=1000,
            )

            daily_df = build_recent_daily_average(raw_df, days=days)

            if daily_df.empty:
                return {
                    "success": False,
                    "message": f"No recent PM2.5 data available for {raw_location}.",
                    "dataframe": None,
                    "summary": None,
                    "error": (
                        f"The nearest station '{station_name}' does not have usable data "
                        f"in the last {days} calendar days."
                    ),
                }

            daily_df = daily_df.copy()
            daily_df["city"] = resolved["resolved_name"]
            daily_df["station_name"] = station_name
            daily_df["distance_km"] = round(distance_km, 2)

            series_frames.append(daily_df)

            summary_rows.append({
                "query_location": raw_location,
                "resolved_location": resolved["resolved_name"],
                "station_name": station_name,
                "distance_km": round(distance_km, 2),
                "mean_pm25": round(daily_df["pm25"].mean(), 2),
                "max_pm25": round(daily_df["pm25"].max(), 2),
                "min_pm25": round(daily_df["pm25"].min(), 2),
                "num_days_returned": len(daily_df),
                "location_confidence": resolved["confidence"],
            })

        combined = pd.concat(series_frames, ignore_index=True)
        combined["date"] = pd.to_datetime(combined["date"], utc=True, errors="coerce")
        combined = combined.dropna(subset=["date"]).copy()

        summary_df = pd.DataFrame(summary_rows)

        return {
            "success": True,
            "message": (
                f"Compared daily PM2.5 for {', '.join(raw_locations)} "
                f"over the last {days} calendar days."
            ),
            "dataframe": combined,
            "summary": summary_df,
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Historical comparison failed.",
            "dataframe": None,
            "summary": None,
            "error": str(e),
        }