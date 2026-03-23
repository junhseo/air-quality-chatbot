from config.settings import settings
from services.current_air_quality_service import load_station_data
from services.location_resolver import resolve_location
from services.station_service import find_nearest_station
from services.openaq_client import (
    fetch_current_openaq,
    fetch_raw_measurements_by_sensor,
    build_recent_daily_average,
)


def test_city(city_name: str, days: int = 10):
    print("=" * 80)
    print(f"Testing city: {city_name}")
    print("=" * 80)

    resolved = resolve_location(city_name)
    print("\n[1] Location resolution")
    print(resolved)

    if not resolved["success"]:
        print("Location resolution failed.")
        return

    station_data = load_station_data()
    nearest_station, distance_km = find_nearest_station(
        lat=resolved["latitude"],
        lon=resolved["longitude"],
        station_data=station_data,
        intent="current",
    )

    print("\n[2] Nearest station")
    print(f"sitename    : {nearest_station.get('sitename')}")
    print(f"locationId  : {nearest_station.get('locationId')}")
    print(f"sensorId    : {nearest_station.get('sensorId')}")
    print(f"distance_km : {distance_km:.2f}")

    sensor_id = int(nearest_station["sensorId"])

    latest = fetch_current_openaq(nearest_station)
    print("\n[3] Current latest")
    print(latest)

    raw_df = fetch_raw_measurements_by_sensor(sensor_id=sensor_id, days=days, limit=1000)
    print("\n[4] Raw measurements")
    print(f"row_count: {len(raw_df)}")

    if not raw_df.empty:
        print("min datetime:", raw_df["datetime_local"].min())
        print("max datetime:", raw_df["datetime_local"].max())
        print(raw_df.head())
        print(raw_df.tail())
    else:
        print("No raw measurements returned.")

    daily_df = build_recent_daily_average(raw_df, days=days)
    print(f"\n[5] Daily average for last {days} days")
    print(f"row_count: {len(daily_df)}")

    if not daily_df.empty:
        print("min date:", daily_df["date"].min())
        print("max date:", daily_df["date"].max())
        print(daily_df)
    else:
        print("No recent daily data in requested window.")


def main():
    settings.validate()
    test_city("Washington, DC", days=10)
    test_city("New York City", days=10)


if __name__ == "__main__":
    main()