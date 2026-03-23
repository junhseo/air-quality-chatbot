from typing import Optional


def recommend_outdoor_activity(pm25: Optional[float]) -> str:
    if pm25 is None:
        return "I could not determine a recommendation because PM2.5 data is unavailable."

    if pm25 <= 12:
        return "Outdoor activity is generally fine for most people today."
    elif pm25 <= 35.4:
        return (
            "Outdoor activity is generally acceptable, but sensitive groups may want "
            "to reduce prolonged or intense exertion."
        )
    elif pm25 <= 55.4:
        return (
            "Consider limiting prolonged or intense outdoor activity, especially if "
            "you are sensitive to air pollution."
        )
    else:
        return (
            "I do not recommend prolonged outdoor activity today, especially for "
            "sensitive groups."
        )