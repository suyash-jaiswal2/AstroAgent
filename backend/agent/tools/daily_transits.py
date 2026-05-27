"""
Tool 3: get_daily_transits
Computes current planetary positions for a given date and calculates
aspects to a natal chart (if provided). Returns moon phase, current sky,
and active transits as JSON.
"""
import json
from datetime import datetime, date as date_type

import pytz
import swisseph as swe
from langchain_core.tools import tool

from .birth_chart import (
    SIGNS, PLANET_IDS, _calc_planet, _degree_to_sign, _EPHE_PATH,
)

swe.set_ephe_path(_EPHE_PATH)

# Aspect definitions: (name, angle, orb_tolerance)
ASPECTS = [
    ("conjunction", 0.0, 8.0),
    ("sextile", 60.0, 6.0),
    ("square", 90.0, 6.0),
    ("trine", 120.0, 6.0),
    ("opposition", 180.0, 8.0),
]

MOON_PHASES = [
    (0, 45, "New Moon"), (45, 90, "Waxing Crescent"), (90, 135, "First Quarter"),
    (135, 180, "Waxing Gibbous"), (180, 225, "Full Moon"), (225, 270, "Waning Gibbous"),
    (270, 315, "Last Quarter"), (315, 360, "Waning Crescent"),
]

PLANET_GLYPHS = {
    "Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀", "Mars": "♂",
    "Jupiter": "♃", "Saturn": "♄", "Uranus": "♅", "Neptune": "♆",
    "Pluto": "♇", "Rahu": "☊", "Ketu": "☋",
}


def _angle_diff(a: float, b: float) -> float:
    """Shortest angular distance between two ecliptic longitudes."""
    diff = abs(a - b) % 360
    return 360 - diff if diff > 180 else diff


def _get_aspect(lon_a: float, lon_b: float) -> tuple[str, float] | None:
    """Return (aspect_name, orb) if within tolerance, else None."""
    for name, angle, orb in ASPECTS:
        diff = _angle_diff(lon_a, lon_b)
        actual_orb = abs(diff - angle)
        if actual_orb <= orb:
            return name, round(actual_orb, 2)
    return None


def _moon_phase(sun_lon: float, moon_lon: float) -> tuple[str, float]:
    """Compute moon phase name and illumination percentage."""
    elongation = (moon_lon - sun_lon) % 360
    illumination = round((1 - abs(elongation - 180) / 180) * 100, 1)
    for lo, hi, name in MOON_PHASES:
        if lo <= elongation < hi:
            return name, illumination
    return "Waning Crescent", illumination


def _compute_current_sky(target_date: str) -> dict:
    """Compute planetary positions for a given date at noon UTC."""
    dt = datetime.strptime(target_date, "%Y-%m-%d")
    jd = swe.julday(dt.year, dt.month, dt.day, 12.0)

    sky: dict = {}
    swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)  # Tropical

    for name, planet_id in PLANET_IDS.items():
        lon, retro = _calc_planet(jd, planet_id)
        sign, deg = _degree_to_sign(lon)
        sky[name] = {
            "longitude": round(lon, 4), "sign": sign,
            "degree": round(deg, 4), "retrograde": retro,
            "glyph": PLANET_GLYPHS.get(name, ""),
        }

    # Add Ketu
    rahu_lon = sky["Rahu"]["longitude"]
    ketu_lon = (rahu_lon + 180) % 360
    sign, deg = _degree_to_sign(ketu_lon)
    sky["Ketu"] = {"longitude": round(ketu_lon, 4), "sign": sign,
                   "degree": round(deg, 4), "retrograde": False, "glyph": "☋"}

    return sky, jd


@tool
def get_daily_transits(date: str, natal_chart_json: str = "null") -> str:
    """
    Get current planetary sky positions and compute aspects to a natal chart.
    Call this tool for daily horoscope questions, transit analysis, moon phase questions,
    or any question about current planetary energies.

    Args:
        date: Date to compute transits for, in ISO format e.g. '2026-05-27'.
              Use today's date for current energy questions.
        natal_chart_json: Optional. JSON string of a natal chart (from compute_birth_chart).
                          Pass this to get personalized transit-to-natal aspects.
                          Pass 'null' if not available.
    """
    try:
        # Use today if date is empty or 'today'
        if not date or date.lower() == "today":
            date = date_type.today().isoformat()

        sky, jd = _compute_current_sky(date)
        natal_chart = json.loads(natal_chart_json) if natal_chart_json not in ("null", "{}") else None

        # Moon phase
        sun_lon = sky["Sun"]["longitude"]
        moon_lon = sky["Moon"]["longitude"]
        moon_phase, moon_illumination = _moon_phase(sun_lon, moon_lon)

        # Transit-to-natal aspects
        active_transits: list = []
        if natal_chart:
            natal_planets = natal_chart.get("tropical", {}).get("planets", {})
            for transit_planet, tdata in sky.items():
                if transit_planet in ("Ketu",):
                    continue
                for natal_planet, ndata in natal_planets.items():
                    asp = _get_aspect(tdata["longitude"], ndata["longitude"])
                    if asp:
                        aspect_name, orb = asp
                        active_transits.append({
                            "transiting": transit_planet,
                            "natal": natal_planet,
                            "aspect": aspect_name,
                            "orb": orb,
                            "transit_sign": tdata["sign"],
                            "natal_sign": ndata["sign"],
                            "intensity": "strong" if orb < 2.0 else ("moderate" if orb < 4.0 else "wide"),
                        })
            # Sort by tightest orb
            active_transits.sort(key=lambda x: x["orb"])

        result = {
            "date": date,
            "current_sky": sky,
            "moon_phase": moon_phase,
            "moon_illumination_pct": moon_illumination,
            "active_transits_to_natal": active_transits[:10] if active_transits else [],
            "transit_count": len(active_transits),
            "standout_energy": (
                active_transits[0]["transiting"] + " " + active_transits[0]["aspect"] +
                " natal " + active_transits[0]["natal"]
                if active_transits else "No exact transits active today"
            ),
        }
        return json.dumps(result)

    except Exception as e:
        return json.dumps({"error": f"Transit computation failed: {str(e)}", "date": date})