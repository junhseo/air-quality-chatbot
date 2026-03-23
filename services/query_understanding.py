import re
from typing import Dict, List


ADVISORY_KEYWORDS = [
    "recommend",
    "safe",
    "outdoor",
    "go outside",
    "run",
    "exercise",
    "walk",
    "jog",
    "mask",
    "wear a mask",
]

COMPARE_KEYWORDS = [
    "compare",
    "comparison",
    "plot",
    "trend",
    "last",
    "days",
    "show",
]

CURRENT_KEYWORDS = [
    "today",
    "now",
    "current",
    "right now",
    "latest",
]

GENERAL_EXPLANATION_KEYWORDS = [
    "what is pm2.5",
    "what does aqi mean",
    "explain pm2.5",
    "explain aqi",
]


def _clean_location_text(text: str) -> str:
    text = text.strip(" .,?!;:")
    text = re.sub(r"\s+", " ", text)
    return text


def _extract_compare_locations(user_text: str) -> List[str]:
    match = re.search(
        r"compare\s+(.+?)\s+and\s+(.+?)\s+(?:over|for)\s+the\s+last\s+\d+\s+days",
        user_text,
        flags=re.IGNORECASE,
    )
    if not match:
        return []

    loc1 = _clean_location_text(match.group(1))
    loc2 = _clean_location_text(match.group(2))
    return [loc1, loc2]


def _extract_single_location(user_text: str) -> List[str]:
    patterns = [
        r"\bin\s+([A-Za-z0-9.,\-\s]+?)(?:\s+today|\s+now|\s+right now|\?|$)",
        r"\bfor\s+([A-Za-z0-9.,\-\s]+?)(?:\s+today|\s+now|\s+right now|\?|$)",
        r"\bnear\s+([A-Za-z0-9.,\-\s]+?)(?:\s+today|\s+now|\s+right now|\?|$)",
    ]

    candidates = []
    for pattern in patterns:
        matches = re.findall(pattern, user_text, flags=re.IGNORECASE)
        for m in matches:
            cleaned = _clean_location_text(m)
            if cleaned:
                candidates.append(cleaned)

    # fallback for very short forms like "DC today"
    if not candidates:
        short_match = re.search(
            r"\b(DC|NYC|LA|SF|Seoul|Beijing|Delhi|London|Paris|Tokyo)\b",
            user_text,
            flags=re.IGNORECASE,
        )
        if short_match:
            candidates.append(_clean_location_text(short_match.group(1)))

    # deduplicate preserving order
    unique = []
    for c in candidates:
        if c not in unique:
            unique.append(c)

    return unique


def understand_query(user_text: str) -> Dict:
    text = user_text.strip()
    lower = text.lower()

    if any(k in lower for k in GENERAL_EXPLANATION_KEYWORDS):
        return {
            "domain": "air_quality",
            "intent": "general_explanation",
            "location_texts": [],
            "days": None,
            "time_text": None,
            "needs_recommendation": False,
            "needs_plot": False,
            "needs_current_data": False,
            "needs_historical_data": False,
        }

    compare_locations = _extract_compare_locations(text)
    days_match = re.search(r"last\s+(\d+)\s+days", lower)

    if compare_locations and days_match:
        return {
            "domain": "air_quality",
            "intent": "historical_compare",
            "location_texts": compare_locations,
            "days": int(days_match.group(1)),
            "time_text": "last_n_days",
            "needs_recommendation": False,
            "needs_plot": True,
            "needs_current_data": False,
            "needs_historical_data": True,
        }

    locations = _extract_single_location(text)
    is_advisory = any(k in lower for k in ADVISORY_KEYWORDS)

    if is_advisory:
        return {
            "domain": "air_quality",
            "intent": "current_advisory",
            "location_texts": locations,
            "days": None,
            "time_text": "today" if "today" in lower else "current",
            "needs_recommendation": True,
            "needs_plot": False,
            "needs_current_data": True,
            "needs_historical_data": False,
        }

    return {
        "domain": "air_quality",
        "intent": "current_lookup",
        "location_texts": locations,
        "days": None,
        "time_text": "today" if "today" in lower else "current",
        "needs_recommendation": False,
        "needs_plot": False,
        "needs_current_data": True,
        "needs_historical_data": False,
    }