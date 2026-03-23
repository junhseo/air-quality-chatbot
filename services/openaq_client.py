from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import pandas as pd
import requests

from config.settings import settings


def convert_iso_to_readable_datetime(iso_string: str) -> str:
    dt_object = datetime.fromisoformat(iso_string)
    return dt_object.strftime("%B %d, %Y at %I:%M %p")


def fetch_current_openaq(nearest_station) -> Dict[str, Any]:
    try:
        location_id = int(nearest_station["locationId"])
        sensor_id = int(nearest_station["sensorId"])

        resp = requests.get(
            f"{settings.api.openaq.base_url}/locations/{location_id}/latest",
            headers=settings.api.openaq.headers,
            timeout=settings.api.openaq.timeout,
        )
        resp.raise_for_status()
        response = resp.json()

        matched = [
            item for item in response.get("results", [])
            if int(item.get("sensorsId", -1)) == sensor_id
        ]

        if not matched:
            return {
                "success": False,
                "value": None,
                "local_time": None,
                "readable_time": None,
                "station_name": nearest_station.get("sitename", str(location_id)),
                "error": "No PM2.5 sensor data found for this station.",
            }

        result = matched[0]
        local_time = result["datetime"]["local"]
        pm25_value = result["value"]

        return {
            "success": True,
            "value": pm25_value,
            "local_time": local_time,
            "readable_time": convert_iso_to_readable_datetime(local_time),
            "station_name": nearest_station.get("sitename", str(location_id)),
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "value": None,
            "local_time": None,
            "readable_time": None,
            "station_name": None,
            "error": str(e),
        }


def fetch_raw_measurements_by_sensor(sensor_id: int, days: int, limit: int = 1000) -> pd.DataFrame:
    """
    Fetch raw PM2.5 measurements only within the requested recent window.

    Important:
    - We use datetime_from / datetime_to so we do NOT accidentally fetch
      old pages of historical data.
    - For 10 days of hourly-ish data, limit=1000 is usually enough.
    """
    safe_limit = min(limit, 1000)

    now_utc = datetime.now(timezone.utc)
    start_utc = now_utc - timedelta(days=days - 1)

    params = {
        "limit": safe_limit,
        "page": 1,
        "datetime_from": start_utc.isoformat(),
        "datetime_to": now_utc.isoformat(),
    }

    resp = requests.get(
        f"{settings.api.openaq.base_url}/sensors/{int(sensor_id)}/measurements",
        headers=settings.api.openaq.headers,
        params=params,
        timeout=settings.api.openaq.timeout,
    )
    resp.raise_for_status()
    payload = resp.json()

    rows = []
    for item in payload.get("results", []):
        dt_local = (
            item.get("period", {}).get("datetimeFrom", {}).get("local")
            or item.get("datetime", {}).get("local")
        )
        value = item.get("value")

        if dt_local is not None and value is not None:
            rows.append({
                "datetime_local_raw": dt_local,
                "value": value,
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["datetime_local_raw", "datetime_local", "value"])

    df["datetime_local"] = pd.to_datetime(
        df["datetime_local_raw"],
        utc=True,
        errors="coerce",
    )
    df = df.dropna(subset=["datetime_local"]).copy()

    return df


def build_recent_daily_average(df: pd.DataFrame, days: int) -> pd.DataFrame:
    """
    Build daily average PM2.5 over the last N calendar days from raw measurements.
    """
    if df.empty:
        return pd.DataFrame(columns=["date", "pm25"])

    work = df.copy()
    work["datetime_local"] = pd.to_datetime(work["datetime_local"], utc=True, errors="coerce")
    work = work.dropna(subset=["datetime_local"]).copy()

    if work.empty:
        return pd.DataFrame(columns=["date", "pm25"])

    work["date"] = work["datetime_local"].dt.floor("D")

    today = pd.Timestamp.now(tz="UTC").floor("D")
    start_date = today - pd.Timedelta(days=days - 1)

    work = work[(work["date"] >= start_date) & (work["date"] <= today)].copy()
    if work.empty:
        return pd.DataFrame(columns=["date", "pm25"])

    daily_df = (
        work.groupby("date", as_index=False)["value"]
        .mean()
        .rename(columns={"value": "pm25"})
        .sort_values("date")
        .reset_index(drop=True)
    )

    daily_df["date"] = pd.to_datetime(daily_df["date"], utc=True, errors="coerce")
    daily_df = daily_df.dropna(subset=["date"]).copy()

    return daily_df