"""
Tool 1: geocode_place
Resolves a place name to latitude, longitude, and timezone.
Uses Nominatim (OpenStreetMap) + timezonefinder.
Caches results in SQLite to avoid repeat API calls.
"""
import asyncio
import json
import os
from typing import Any

import httpx
from langchain_core.tools import tool
from timezonefinder import TimezoneFinder

# Module-level in-memory cache (survives within a process lifetime)
_geocode_cache: dict[str, dict] = {}
_tf = TimezoneFinder()

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "AstroAgent/1.0 (aradhana-internship-assignment)"


async def _geocode_impl(place_name: str) -> dict:
    """Internal async implementation with caching."""
    normalized = place_name.lower().strip()

    # 1. In-memory cache (fastest)
    if normalized in _geocode_cache:
        return _geocode_cache[normalized]

    # 2. SQLite cache (persistent across restarts)
    try:
        from db.database import AsyncSessionLocal
        from db.crud import get_cached_geocode, save_geocode_cache
        async with AsyncSessionLocal() as db:
            cached = await get_cached_geocode(db, normalized)
            if cached:
                _geocode_cache[normalized] = cached
                return cached
    except Exception:
        pass  # DB not yet initialized — continue to API

    # 3. Nominatim API call (rate limited: 1 req/sec)
    await asyncio.sleep(1.1)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                NOMINATIM_URL,
                params={"q": place_name, "format": "json", "limit": 3},
                headers={"User-Agent": USER_AGENT},
            )
        resp.raise_for_status()
        results = resp.json()
    except httpx.TimeoutException:
        # Retry once on timeout
        await asyncio.sleep(2.0)
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                NOMINATIM_URL,
                params={"q": place_name, "format": "json", "limit": 3},
                headers={"User-Agent": USER_AGENT},
            )
        results = resp.json()

    if not results:
        raise ValueError(
            f"Could not find location: '{place_name}'. "
            f"Try adding a country name, e.g., 'Mumbai, India' or 'London, UK'."
        )

    best = results[0]
    lat = float(best["lat"])
    lon = float(best["lon"])

    # 4. Timezone via timezonefinder (offline, instant)
    tz = _tf.timezone_at(lng=lon, lat=lat)
    if not tz:
        tz = "UTC"

    result: dict[str, Any] = {
        "latitude": lat,
        "longitude": lon,
        "timezone": tz,
        "display_name": best.get("display_name", place_name),
        "confidence": float(best.get("importance", 0.5)),
    }

    # 5. Persist to both caches
    _geocode_cache[normalized] = result
    try:
        from db.database import AsyncSessionLocal
        from db.crud import save_geocode_cache
        async with AsyncSessionLocal() as db:
            await save_geocode_cache(db, place_name, result)
    except Exception:
        pass

    return result


@tool
async def geocode_place(place_name: str) -> str:
    """
    Resolve a place name to its geographic coordinates and timezone.
    Use this whenever you need the latitude, longitude, or timezone for a birth place
    or any location. Returns JSON with latitude, longitude, timezone, and display_name.

    Args:
        place_name: City and country name, e.g. 'Mumbai, India' or 'London, UK'
    """
    try:
        result = await _geocode_impl(place_name)
        return json.dumps(result)
    except ValueError as e:
        return json.dumps({"error": str(e), "place_name": place_name})
    except Exception as e:
        return json.dumps({"error": f"Geocoding failed: {str(e)}", "place_name": place_name})