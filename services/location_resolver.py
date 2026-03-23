from typing import Dict, List, Optional

from services.geocoding_client import geocode_candidates


FAST_ALIASES = {
    "dc": "Washington, DC, United States",
    "d.c.": "Washington, DC, United States",
    "nyc": "New York City, New York, United States",
    "la": "Los Angeles, California, United States",
    "sf": "San Francisco, California, United States",
}


def _normalize_raw_text(text: str) -> str:
    return " ".join(text.strip().split())


def _fast_alias_lookup(text: str) -> Optional[str]:
    key = text.strip().lower()
    return FAST_ALIASES.get(key)


def _score_candidate(raw_query: str, candidate_display_name: str) -> float:
    """
    Simple deterministic scoring.
    Higher is better.
    """
    score = 0.0
    raw_lower = raw_query.lower().strip()
    display_lower = candidate_display_name.lower()

    if raw_lower in display_lower:
        score += 2.0

    # Favor explicit U.S. city resolution for common cases like DC, NYC
    if raw_lower in {"dc", "d.c.", "nyc", "la", "sf"} and "united states" in display_lower:
        score += 2.0

    # Favor exact city-like prefix matches
    first_token = raw_lower.split()[0] if raw_lower.split() else raw_lower
    if first_token and first_token in display_lower:
        score += 1.0

    return score


def resolve_location(raw_location: str) -> Dict:
    """
    Resolve a raw user location string into a validated normalized location.

    Current strategy:
    1. Normalize text
    2. Apply small high-confidence alias shortcut
    3. Fetch geocoding candidates
    4. Score and select best candidate
    5. Return structured result with confidence

    Later this can be upgraded to:
    - LLM normalization
    - LLM + geocoder reranking
    - ambiguity clarification
    """
    cleaned = _normalize_raw_text(raw_location)

    # Step 1: fast alias expansion
    alias_expanded = _fast_alias_lookup(cleaned)
    query_for_geocoder = alias_expanded or cleaned

    geo = geocode_candidates(query_for_geocoder, limit=5)
    if not geo["success"]:
        return {
            "success": False,
            "raw_location": raw_location,
            "normalized_query": query_for_geocoder,
            "resolved_name": None,
            "latitude": None,
            "longitude": None,
            "confidence": 0.0,
            "candidates": [],
            "needs_clarification": False,
            "error": geo["error"],
        }

    candidates = geo["candidates"]
    if not candidates:
        return {
            "success": False,
            "raw_location": raw_location,
            "normalized_query": query_for_geocoder,
            "resolved_name": None,
            "latitude": None,
            "longitude": None,
            "confidence": 0.0,
            "candidates": [],
            "needs_clarification": False,
            "error": f"No geocoding candidates found for '{raw_location}'.",
        }

    scored = []
    for cand in candidates:
        score = _score_candidate(cleaned, cand["display_name"])
        scored.append((score, cand))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best = scored[0]

    # Ambiguity policy
    needs_clarification = False
    if len(scored) > 1:
        second_score = scored[1][0]
        if abs(best_score - second_score) < 0.5 and best_score < 2.5:
            needs_clarification = True

    confidence = min(1.0, max(0.2, best_score / 4.0))

    return {
        "success": True,
        "raw_location": raw_location,
        "normalized_query": query_for_geocoder,
        "resolved_name": best["display_name"],
        "latitude": best["latitude"],
        "longitude": best["longitude"],
        "confidence": round(confidence, 2),
        "candidates": [c["display_name"] for _, c in scored[:3]],
        "needs_clarification": needs_clarification,
        "error": None,
    }