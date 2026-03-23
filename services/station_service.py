from typing import Tuple
import numpy as np
import pandas as pd


def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return 6371.0 * c


def find_nearest_station(
    lat: float,
    lon: float,
    station_data: pd.DataFrame,
    intent: str = "current",
) -> Tuple[pd.Series, float]:
    if intent == "current":
        filtered = station_data[station_data["PROJECT_NAME"] == "OpenAQ"].copy()
    else:
        filtered = station_data.copy()

    if filtered.empty:
        raise ValueError("No stations available after filtering.")

    distances = haversine_distance(
        lat, lon,
        filtered["Latitude"].values,
        filtered["Longitude"].values,
    )
    idx = distances.argmin()
    return filtered.iloc[idx], float(distances[idx])