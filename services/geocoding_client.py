from typing import Dict, List
import requests


def geocode_candidates(query: str, timeout: int = 10, limit: int = 5) -> Dict:
    """
    Return multiple geocoding candidates for a query.
    """
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query,
                "format": "json",
                "limit": limit,
                "addressdetails": 1,
            },
            headers={"User-Agent": "air-quality-chatbot/0.1"},
            timeout=timeout,
        )
        resp.raise_for_status()
        results = resp.json()

        candidates: List[Dict] = []
        for item in results:
            candidates.append({
                "display_name": item.get("display_name"),
                "latitude": float(item["lat"]),
                "longitude": float(item["lon"]),
                "raw": item,
            })

        return {
            "success": True,
            "query": query,
            "candidates": candidates,
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "query": query,
            "candidates": [],
            "error": str(e),
        }