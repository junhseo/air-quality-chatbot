import pandas as pd

from config.settings import settings
from services.station_service import find_nearest_station
from services.openaq_client import fetch_current_openaq


def main():
    settings.validate()

    station_data = pd.read_csv(settings.paths.station_metadata_path)

    # Example: Washington, DC
    lat = 38.9072
    lon = -77.0369

    nearest_station, distance_km = find_nearest_station(
        lat=lat,
        lon=lon,
        station_data=station_data,
        intent="current",
    )

    print(f"Nearest station: {nearest_station.get('sitename', 'Unknown')}")
    print(f"Distance: {distance_km:.2f} km")
    print(f"locationId: {nearest_station.get('locationId')}")
    print(f"sensorId: {nearest_station.get('sensorId')}")

    result = fetch_current_openaq(nearest_station)

    print("\nOpenAQ Result:")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()