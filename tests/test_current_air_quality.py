from config.settings import settings
from services.current_air_quality_service import (
    get_current_air_quality_for_city,
    format_current_air_quality_response,
)


def main():
    settings.validate()

    city_name = "Washington, DC"
    result = get_current_air_quality_for_city(city_name)

    print("Normalized Result:\n")
    for key, value in result.items():
        print(f"{key}: {value}")

    print("\nFormatted Response:\n")
    print(format_current_air_quality_response(result))


if __name__ == "__main__":
    main()