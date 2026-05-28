"""
Feature 4: get_panchang
Computes the five-limbed Vedic almanac (Panchang) for any date and location.
Five limbs: Tithi, Vara, Nakshatra, Yoga, Karana + bonus timing features.
"""
import json
import math
from datetime import datetime

import pytz
import swisseph as swe
from langchain_core.tools import tool

from .birth_chart import SIGNS, _EPHE_PATH, _degree_to_sign

swe.set_ephe_path(_EPHE_PATH)
from .muhurta import (
    NAKSHATRA_LORDS, NITYA_YOGA_NAMES, TITHI_NAMES, VARA_NAMES,
    RAHU_KALAM_PART, HORA_SEQUENCE, WEEKDAY_HORA_START,
    _approx_sunrise_sunset, _get_weekday,
)

NAKSHATRA_NAMES = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu",
    "Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta",
    "Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha",
    "Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha","Purva Bhadrapada",
    "Uttara Bhadrapada","Revati",
]

VARA_LORDS = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]

KARANA_MOVEABLE = ["Bava","Balava","Kaulava","Taitila","Garaja","Vanija","Vishti"]
KARANA_FIXED = {0: "Kimstughna", 57: "Shakuni", 58: "Chatushpada", 59: "Naga"}

NITYA_YOGA_QUALITY = {
    name: ("auspicious" if name in {
        "Priti","Ayushman","Saubhagya","Shobhana","Sukarma","Dhriti","Vriddhi",
        "Dhruva","Harshana","Siddhi","Variyana","Shiva","Siddha","Sadhya",
        "Shubha","Shukla","Brahma","Indra",
    } else "inauspicious")
    for name in NITYA_YOGA_NAMES
}

MOON_PHASES = [
    (0, 45, "New Moon"), (45, 90, "Waxing Crescent"), (90, 135, "First Quarter"),
    (135, 180, "Waxing Gibbous"), (180, 225, "Full Moon"), (225, 270, "Waning Gibbous"),
    (270, 315, "Last Quarter"), (315, 360, "Waning Crescent"),
]


def _datetime_to_jd(date_str: str, tz_str: str) -> float:
    tz = pytz.timezone(tz_str)
    dt = datetime.strptime(f"{date_str} 00:00", "%Y-%m-%d %H:%M")
    dt_aware = tz.localize(dt)
    dt_utc = dt_aware.astimezone(pytz.utc)
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                      dt_utc.hour + dt_utc.minute / 60.0)


def _jd_to_local_time(jd: float, tz_str: str) -> str:
    """Convert JD to local HH:MM string."""
    dt_vals = swe.revjul(jd)
    year, month, day = int(dt_vals[0]), int(dt_vals[1]), int(dt_vals[2])
    frac = dt_vals[3]
    hour = int(frac)
    minute = int((frac - hour) * 60)
    dt_utc = datetime(year, month, day, hour, minute, tzinfo=pytz.utc)
    tz = pytz.timezone(tz_str)
    dt_local = dt_utc.astimezone(tz)
    return dt_local.strftime("%H:%M")


def _compute_panchang(jd: float, lat: float, lon: float, tz_str: str) -> dict:
    sun_xx = swe.calc_ut(jd, swe.SUN)
    moon_xx = swe.calc_ut(jd, swe.MOON)
    sun_lon = float(sun_xx[0][0]) % 360 if isinstance(sun_xx[0], (list, tuple)) else float(sun_xx[0]) % 360
    moon_lon = float(moon_xx[0][0]) % 360 if isinstance(moon_xx[0], (list, tuple)) else float(moon_xx[0]) % 360

    # 1. TITHI — Lunar day
    diff = (moon_lon - sun_lon) % 360
    tithi_num = int(diff / 12) + 1  # 1–30
    paksha = "Shukla" if tithi_num <= 15 else "Krishna"
    tithi_name = "Purnima" if tithi_num == 15 else "Amavasya" if tithi_num == 30 else TITHI_NAMES[(tithi_num - 1) % 15]

    # 2. VARA — Weekday
    weekday = _get_weekday(jd)
    vara = {"name": VARA_NAMES[weekday], "lord": VARA_LORDS[weekday]}

    # 3. NAKSHATRA — Moon's lunar mansion
    nak_idx = int(moon_lon / (360 / 27))
    pada = int((moon_lon % (360 / 27)) / (360 / 27 / 4)) + 1
    nakshatra = {
        "name": NAKSHATRA_NAMES[nak_idx],
        "lord": NAKSHATRA_LORDS[nak_idx],
        "pada": pada,
    }

    # 4. YOGA — Nitya Yoga (Sun + Moon combined)
    yoga_idx = int((sun_lon + moon_lon) % 360 / (360 / 27))
    yoga_name = NITYA_YOGA_NAMES[yoga_idx]
    yoga = {"name": yoga_name, "quality": NITYA_YOGA_QUALITY.get(yoga_name, "neutral")}

    # 5. KARANA — Half-tithi
    karana_num = int(diff / 6)  # 0–59
    if karana_num in KARANA_FIXED:
        karana_name = KARANA_FIXED[karana_num]
    else:
        karana_name = KARANA_MOVEABLE[(karana_num - 1) % 7]

    # Rahu Kalam (sunrise–sunset divided into 8 parts)
    rise_jd, set_jd = _approx_sunrise_sunset(jd, lat, lon)
    part_dur = (set_jd - rise_jd) / 8.0
    rk_part = RAHU_KALAM_PART[weekday]
    rk_start_jd = rise_jd + (rk_part - 1) * part_dur
    rk_end_jd = rise_jd + rk_part * part_dur
    rahu_kalam = {
        "start": _jd_to_local_time(rk_start_jd, tz_str),
        "end": _jd_to_local_time(rk_end_jd, tz_str),
    }

    # Abhijit Muhurta — 24 minutes before and after solar noon
    noon_jd = (rise_jd + set_jd) / 2.0
    abhijit = {
        "start": _jd_to_local_time(noon_jd - 12 / 1440, tz_str),
        "end": _jd_to_local_time(noon_jd + 12 / 1440, tz_str),
    }

    # Brahma Muhurta — ~96 minutes before sunrise
    brahma_muhurta = {
        "start": _jd_to_local_time(rise_jd - 96 / 1440, tz_str),
        "end": _jd_to_local_time(rise_jd - 48 / 1440, tz_str),
    }

    # Current hora
    hours_since_rise = max(0.0, (jd - rise_jd) * 24.0)
    hora_num = int(hours_since_rise)
    start_idx = WEEKDAY_HORA_START[weekday]
    current_hora = HORA_SEQUENCE[(start_idx + hora_num) % 7]

    # Moon phase
    elongation = (moon_lon - sun_lon) % 360
    illumination = round((1 - abs(elongation - 180) / 180) * 100, 1)
    moon_phase_name = next((name for lo, hi, name in MOON_PHASES if lo <= elongation < hi), "Waning Crescent")

    # Day summary
    day_summary = (
        f"Today is {VARA_NAMES[weekday]}, ruled by {VARA_LORDS[weekday]}. "
        f"The Moon graces the nakshatra of {NAKSHATRA_NAMES[nak_idx]} (Pada {pada}), "
        f"under {paksha} Paksha {tithi_name} Tithi. "
        f"The Nitya Yoga is {yoga_name} — a {yoga['quality']} quality. "
        f"Rahu Kalam runs from {rahu_kalam['start']} to {rahu_kalam['end']} — avoid beginning important activities during this period."
    )

    return {
        "tithi": {"number": tithi_num, "name": tithi_name, "paksha": paksha},
        "vara": vara,
        "nakshatra": nakshatra,
        "yoga": yoga,
        "karana": karana_name,
        "rahu_kalam": rahu_kalam,
        "abhijit_muhurta": abhijit,
        "brahma_muhurta": brahma_muhurta,
        "current_hora": current_hora,
        "sunrise": _jd_to_local_time(rise_jd, tz_str),
        "sunset": _jd_to_local_time(set_jd, tz_str),
        "moon_phase": moon_phase_name,
        "moon_illumination_pct": illumination,
        "day_summary": day_summary,
    }


@tool
def get_panchang(date: str, latitude: float, longitude: float, timezone: str) -> str:
    """
    Compute the five-limbed Vedic almanac (Panchang) for a given date and location.
    Returns Tithi (lunar day), Vara (weekday), Nakshatra (Moon's asterism),
    Yoga (Nitya Yoga), Karana (half-tithi), Rahu Kalam, Abhijit Muhurta,
    Brahma Muhurta, current Hora lord, moon phase, and a day summary.

    Args:
        date: Date in ISO format e.g. '2026-05-27'
        latitude: Location latitude (from geocode_place)
        longitude: Location longitude (from geocode_place)
        timezone: Location timezone e.g. 'Asia/Kolkata'
    """
    try:
        jd = _datetime_to_jd(date, timezone)
        result = _compute_panchang(jd + 0.5, latitude, longitude, timezone)  # Use noon for most accurate daily reading
        result["date"] = date
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Panchang computation failed: {str(e)}", "date": date})