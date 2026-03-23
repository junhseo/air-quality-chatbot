import re
from typing import Dict


def parse_chat_query(user_text: str) -> Dict:
    text = user_text.strip()
    lower = text.lower()

    compare_match = re.search(
        r"compare\s+(.+?)\s+and\s+(.+?)\s+(?:over|for)\s+the\s+last\s+(\d+)\s+days",
        lower,
    )
    if compare_match:
        raw_city1 = text[compare_match.start(1):compare_match.end(1)].strip()
        raw_city2 = text[compare_match.start(2):compare_match.end(2)].strip()
        days = int(compare_match.group(3))
        return {
            "intent": "historical_compare",
            "raw_locations": [raw_city1, raw_city2],
            "days": days,
        }

    single_plot_match = re.search(
        r"(?:plot|show).+last\s+(\d+)\s+days.+(?:in|for)\s+(.+)$",
        lower,
    )
    if single_plot_match:
        days = int(single_plot_match.group(1))
        raw_city = text[single_plot_match.start(2):single_plot_match.end(2)].strip()
        return {
            "intent": "historical_compare",
            "raw_locations": [raw_city],
            "days": days,
        }

    current_match = re.search(
        r"(?:current|air quality|pm2\.?5|aqi).+(?:in|for|near)\s+(.+)$",
        lower,
    )
    if current_match:
        raw_city = text[current_match.start(1):current_match.end(1)].strip()
        return {
            "intent": "current",
            "raw_location": raw_city,
        }

    return {
        "intent": "current",
        "raw_location": text,
    }