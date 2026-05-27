"""
Tool 2: compute_birth_chart
Computes natal chart using Swiss Ephemeris (pyswisseph).
Returns both tropical (Western/Placidus) and sidereal (Vedic/Lahiri, Whole Sign) charts.
"""
import json
import os
from datetime import datetime

import pytz
import swisseph as swe
from langchain_core.tools import tool

# ── Ephemeris path setup ──────────────────────────────────────────────────────
_EPHE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "ephemeris_data")
)
swe.set_ephe_path(_EPHE_PATH)

# ── Constants ─────────────────────────────────────────────────────────────────
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

PLANET_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
    "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO, "Rahu": swe.TRUE_NODE,
}


def _degree_to_sign(longitude: float) -> tuple[str, float]:
    """Convert ecliptic longitude to (sign_name, degree_within_sign)."""
    lon = longitude % 360
    idx = int(lon / 30)
    return SIGNS[idx], round(lon % 30, 4)


def _calc_planet(jd: float, planet_id: int, flags: int = 0) -> tuple[float, bool]:
    """Calculate planet longitude and retrograde status."""
    result = swe.calc_ut(jd, planet_id, flags)
    # Handle both (xx, retflag) and xx-only return formats across pyswisseph versions
    xx = result[0] if (isinstance(result, tuple) and isinstance(result[0], (list, tuple))) else result
    longitude = float(xx[0]) % 360
    retrograde = float(xx[3]) < 0  # Negative speed = retrograde
    return longitude, retrograde


def _assign_house_placidus(planet_lon: float, cusps: tuple) -> int:
    """Assign planet to Placidus house based on cusp longitudes."""
    planet_lon = planet_lon % 360
    for h in range(1, 12):
        c1 = cusps[h] % 360
        c2 = cusps[h + 1] % 360
        if c1 > c2:
            # House crosses 0° Aries
            if planet_lon >= c1 or planet_lon < c2:
                return h
        else:
            if c1 <= planet_lon < c2:
                return h
    return 12


def _assign_house_whole_sign(planet_lon: float, asc_lon: float) -> int:
    """Assign planet to Whole Sign house based on sidereal ASC longitude."""
    planet_sign = int((planet_lon % 360) / 30)
    asc_sign = int((asc_lon % 360) / 30)
    return (planet_sign - asc_sign) % 12 + 1

def _normalize_cusps(cusps_raw) -> tuple:
    """
    Normalize swe.houses() cusp output to always be 1-indexed (13 elements).
    pyswisseph can return EITHER format depending on version and OS:
      - 13 elements: cusps[0]=0.0 (unused), cusps[1]–cusps[12] = houses 1–12
      - 12 elements: cusps[0]–cusps[11] = houses 1–12 (0-indexed)
    This function always returns the 13-element 1-indexed form.
    """
    if len(cusps_raw) >= 13:
        return tuple(cusps_raw)
    # 12-element: prepend a dummy 0.0 so index 1 = house 1
    return (0.0,) + tuple(cusps_raw)


def _compute_whole_sign_houses(asc_lon: float) -> dict:
    """Compute 12 Whole Sign house cusps from sidereal ASC longitude."""
    asc_sign_idx = int((asc_lon % 360) / 30)
    houses = {}
    for i in range(1, 13):
        sign_idx = (asc_sign_idx + i - 1) % 12
        houses[str(i)] = {
            "sign": SIGNS[sign_idx],
            "cusp_longitude": round(sign_idx * 30.0, 4),
        }
    return houses


def _datetime_to_jd_utc(date: str, time: str, timezone: str) -> float:
    """Convert local datetime string to Julian Day in UTC."""
    tz = pytz.timezone(timezone)
    dt_local = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    dt_aware = tz.localize(dt_local, is_dst=None)
    dt_utc = dt_aware.astimezone(pytz.utc)
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
    )


def _compute_chart(
    date: str,
    time: str | None,
    latitude: float,
    longitude: float,
    timezone: str,
) -> dict:
    """Core chart computation. Returns tropical + sidereal chart dicts."""
    time_unknown = time is None
    effective_time = time if time else "12:00"

    jd = _datetime_to_jd_utc(date, effective_time, timezone)

    # ── TROPICAL CHART (Western, Placidus houses) ─────────────────────────────
    swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)  # Reset — tropical uses no ayanamsa
    tropical_planets: dict = {}

    for name, planet_id in PLANET_IDS.items():
        lon, retro = _calc_planet(jd, planet_id)
        sign, deg = _degree_to_sign(lon)
        tropical_planets[name] = {
            "longitude": round(lon, 4),
            "sign": sign,
            "degree": round(deg, 4),
            "retrograde": retro,
        }

    # Ketu = Rahu + 180°
    rahu_lon = tropical_planets["Rahu"]["longitude"]
    ketu_lon = (rahu_lon + 180.0) % 360
    sign, deg = _degree_to_sign(ketu_lon)
    tropical_planets["Ketu"] = {
        "longitude": round(ketu_lon, 4), "sign": sign,
        "degree": round(deg, 4), "retrograde": False,
    }

# Placidus house cusps
    cusps_raw, ascmc = swe.houses(jd, latitude, longitude, b"P")

    # Normalize to 1-indexed regardless of pyswisseph version/OS behavior
    cusps = _normalize_cusps(cusps_raw)

    # Always read ASC and MC from ascmc (reliable across all versions)
    asc_lon_tropical = float(ascmc[0]) % 360
    mc_lon = float(ascmc[1]) % 360
    asc_sign, asc_deg = _degree_to_sign(asc_lon_tropical)
    mc_sign, mc_deg = _degree_to_sign(mc_lon)

    tropical_houses: dict = {}
    for i in range(1, 13):
        h_lon = float(cusps[i]) % 360  # Now safe: cusps is always 13-element
        h_sign, h_deg = _degree_to_sign(h_lon)
        tropical_houses[str(i)] = {
            "cusp_longitude": round(h_lon, 4),
            "sign": h_sign,
            "degree": round(h_deg, 4),
        }

    # Assign Placidus houses to tropical planets
    for name in tropical_planets:
        tropical_planets[name]["house"] = _assign_house_placidus(
            tropical_planets[name]["longitude"], cusps
        )

    # ── SIDEREAL CHART (Vedic/Jyotish, Lahiri Ayanamsa, Whole Sign houses) ────
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsa = swe.get_ayanamsa_ut(jd)
    sidereal_planets: dict = {}

    for name, planet_id in PLANET_IDS.items():
        lon, retro = _calc_planet(jd, planet_id, swe.FLG_SIDEREAL)
        sign, deg = _degree_to_sign(lon)
        sidereal_planets[name] = {
            "longitude": round(lon, 4),
            "sign": sign,
            "degree": round(deg, 4),
            "retrograde": retro,
        }

    rahu_lon_sid = sidereal_planets["Rahu"]["longitude"]
    ketu_lon_sid = (rahu_lon_sid + 180.0) % 360
    sign, deg = _degree_to_sign(ketu_lon_sid)
    sidereal_planets["Ketu"] = {
        "longitude": round(ketu_lon_sid, 4), "sign": sign,
        "degree": round(deg, 4), "retrograde": False,
    }

    # Sidereal ASC = tropical ASC − ayanamsa
    asc_lon_sidereal = (asc_lon_tropical - ayanamsa) % 360
    asc_sign_sid, asc_deg_sid = _degree_to_sign(asc_lon_sidereal)

    vedic_houses = _compute_whole_sign_houses(asc_lon_sidereal)

    for name in sidereal_planets:
        sidereal_planets[name]["house"] = _assign_house_whole_sign(
            sidereal_planets[name]["longitude"], asc_lon_sidereal
        )

    return {
        "tropical": {
            "planets": tropical_planets,
            "houses": tropical_houses,
            "ascendant": {
                "sign": asc_sign, "degree": round(asc_deg, 4),
                "longitude": round(asc_lon_tropical, 4),
            },
            "mc": {"sign": mc_sign, "degree": round(mc_deg, 4),
                   "longitude": round(mc_lon, 4)},
        },
        "sidereal": {
            "planets": sidereal_planets,
            "houses": vedic_houses,
            "ascendant": {
                "sign": asc_sign_sid, "degree": round(asc_deg_sid, 4),
                "longitude": round(asc_lon_sidereal, 4),
            },
            "ayanamsa": round(ayanamsa, 4),
        },
        "meta": {
            "time_unknown": time_unknown,
            "time_unknown_note": (
                "Birth time not provided — chart cast for solar noon (12:00). "
                "Ascendant and houses are approximate." if time_unknown else None
            ),
            "computed_at": datetime.utcnow().isoformat(),
            "julian_day": round(jd, 6),
        },
    }


@tool
def compute_birth_chart(
    date: str,
    time: str,
    latitude: float,
    longitude: float,
    timezone: str,
) -> str:
    """
    Compute a natal (birth) chart using the Swiss Ephemeris.
    Returns both tropical (Western, Placidus houses) and sidereal (Vedic, Lahiri ayanamsa,
    Whole Sign houses) charts with all planet positions, signs, degrees, houses, and the
    Ascendant. ALWAYS call this tool instead of guessing planetary positions.

    Args:
        date: Birth date in ISO format, e.g. '1990-08-15'
        time: Birth time in 24-hour format, e.g. '14:30'. Use 'unknown' if not known.
        latitude: Birth place latitude (get from geocode_place tool)
        longitude: Birth place longitude (get from geocode_place tool)
        timezone: Birth place timezone, e.g. 'Asia/Kolkata' (get from geocode_place tool)
    """
    try:
        effective_time = None if time.lower() in ("unknown", "null", "") else time
        result = _compute_chart(date, effective_time, latitude, longitude, timezone)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Chart computation failed: {str(e)}"})