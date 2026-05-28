"""
Feature 1: find_muhurta
Scans a 30-day window and scores 1440 half-hour slots using classical
Vedic Muhurta rules. Returns the top 3 most auspicious time slots.
"""
import json
import math
from datetime import datetime, timedelta
from typing import Optional

import pytz
import swisseph as swe
from langchain_core.tools import tool

from .birth_chart import SIGNS, NAKSHATRA_NAMES, _EPHE_PATH, _degree_to_sign

swe.set_ephe_path(_EPHE_PATH)

# ── Lookup tables ─────────────────────────────────────────────────────────────

HORA_SEQUENCE = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
WEEKDAY_HORA_START = [0, 3, 6, 2, 5, 1, 4]  # Sun=0,Mon=3,Tue=6,Wed=2,Thu=5,Fri=1,Sat=4

RAHU_KALAM_PART = {0: 8, 1: 2, 2: 7, 3: 5, 4: 6, 5: 4, 6: 3}  # weekday → 1-indexed part

NAKSHATRA_LORDS = [
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
]

NITYA_YOGA_NAMES = [
    "Vishkambha","Priti","Ayushman","Saubhagya","Shobhana","Atiganda","Sukarma",
    "Dhriti","Shula","Ganda","Vriddhi","Dhruva","Vyaghata","Harshana","Vajra",
    "Siddhi","Vyatipata","Variyana","Parigha","Shiva","Siddha","Sadhya","Shubha",
    "Shukla","Brahma","Indra","Vaidhriti",
]

AUSPICIOUS_YOGA_NAMES = {
    "Priti","Ayushman","Saubhagya","Shobhana","Sukarma","Dhriti","Vriddhi",
    "Dhruva","Harshana","Siddhi","Variyana","Shiva","Siddha","Sadhya","Shubha",
    "Shukla","Brahma","Indra",
}

INAUSPICIOUS_TITHIS = {4, 8, 9, 14, 29, 30}  # Chaturthi, Ashtami, Navami, Chaturdashi, Krishna, Amavasya

TITHI_NAMES = [
    "Pratipada","Dwitiya","Tritiya","Chaturthi","Panchami","Shashthi","Saptami",
    "Ashtami","Navami","Dashami","Ekadashi","Dwadashi","Trayodashi","Chaturdashi",
    "Purnima",
]

INTENT_FAVORABLE_NAKSHATRAS = {
    "business_launch":    {"Rohini","Pushya","Uttara Phalguni","Hasta","Chitra","Anuradha","Uttara Ashadha","Shravana","Dhanishtha"},
    "travel":             {"Ashwini","Mrigashira","Punarvasu","Swati","Anuradha","Shravana","Revati"},
    "marriage":           {"Rohini","Mrigashira","Magha","Uttara Phalguni","Hasta","Swati","Anuradha","Uttara Ashadha","Uttara Bhadrapada","Revati"},
    "medical_procedure":  {"Ashwini","Mrigashira","Punarvasu","Pushya","Hasta","Chitra","Swati","Anuradha","Shravana"},
    "signing_contracts":  {"Rohini","Mrigashira","Uttara Phalguni","Hasta","Chitra","Anuradha","Uttara Ashadha","Shravana"},
    "property_purchase":  {"Rohini","Hasta","Uttara Phalguni","Uttara Ashadha","Shravana"},
    "education_start":    {"Ashwini","Punarvasu","Pushya","Hasta","Chitra","Shravana","Revati"},
    "spiritual_initiation": {"Pushya","Ashwini","Revati","Mrigashira","Hasta","Shravana"},
}

INTENT_WEEKDAYS = {
    "business_launch":    {2, 3},   # Wed, Thu
    "travel":             {2, 4},   # Wed, Fri
    "marriage":           {3, 1, 4}, # Thu, Mon, Fri
    "medical_procedure":  {1, 2},   # Mon, Wed
    "signing_contracts":  {2, 3},   # Wed, Thu
    "property_purchase":  {2, 3},   # Wed, Thu
    "education_start":    {3, 2},   # Thu, Wed
    "spiritual_initiation": {3, 1},  # Thu, Mon
}

BENEFIC_MOON_SIGNS = {"Taurus","Cancer","Leo","Sagittarius","Pisces"}

INTENT_DISPLAY = {
    "business_launch": "start a business", "travel": "travel",
    "marriage": "marriage", "medical_procedure": "medical procedure",
    "signing_contracts": "sign contracts", "property_purchase": "purchase property",
    "education_start": "begin studies", "spiritual_initiation": "spiritual initiation",
}

VARA_NAMES = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]


# ── Helper functions ──────────────────────────────────────────────────────────

def _approx_sunrise_sunset(jd: float, lat: float, lon: float) -> tuple[float, float]:
    """Approximate sunrise and sunset Julian Days using solar equations."""
    dt = swe.revjul(jd)
    year, month, day = int(dt[0]), int(dt[1]), int(dt[2])
    day_of_year = datetime(year, month, day).timetuple().tm_yday
    declination = 23.45 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))
    lat_r, decl_r = math.radians(lat), math.radians(declination)
    cos_h = -math.tan(lat_r) * math.tan(decl_r)
    cos_h = max(-1.0, min(1.0, cos_h))
    h = math.degrees(math.acos(cos_h))
    noon_jd = int(jd) + 0.5 - lon / 360.0
    rise_jd = noon_jd - h / 360.0
    set_jd = noon_jd + h / 360.0
    return rise_jd, set_jd


def _get_weekday(jd: float) -> int:
    """Return weekday 0=Sunday … 6=Saturday from Julian Day."""
    return int(jd + 1.5) % 7


def _is_rahu_kalam(jd: float, lat: float, lon: float) -> bool:
    rise_jd, set_jd = _approx_sunrise_sunset(jd, lat, lon)
    part = (set_jd - rise_jd) / 8.0
    weekday = _get_weekday(jd)
    rk_part = RAHU_KALAM_PART[weekday]
    rk_start = rise_jd + (rk_part - 1) * part
    rk_end = rise_jd + rk_part * part
    return rk_start <= jd <= rk_end


def _is_yamagandam(jd: float, lat: float, lon: float) -> bool:
    rise_jd, set_jd = _approx_sunrise_sunset(jd, lat, lon)
    part = (set_jd - rise_jd) / 8.0
    weekday = _get_weekday(jd)
    ym_parts = {0: 4, 1: 7, 2: 3, 3: 6, 4: 2, 5: 5, 6: 1}
    ym_part = ym_parts[weekday]
    ym_start = rise_jd + (ym_part - 1) * part
    ym_end = rise_jd + ym_part * part
    return ym_start <= jd <= ym_end


def _get_hora_lord(jd: float, lat: float, lon: float) -> str:
    rise_jd, _ = _approx_sunrise_sunset(jd, lat, lon)
    hours_since_sunrise = max(0.0, (jd - rise_jd) * 24.0)
    hora_number = int(hours_since_sunrise)
    weekday = _get_weekday(jd)
    start_idx = WEEKDAY_HORA_START[weekday]
    return HORA_SEQUENCE[(start_idx + hora_number) % 7]


def _score_slot(jd: float, lat: float, lon: float, intent: str, natal_chart: dict) -> tuple[int, dict]:
    """Score a single 30-minute muhurta slot (0–100)."""
    score = 0
    details: dict = {}

    # Moon position
    moon_xx = swe.calc_ut(jd, swe.MOON)
    moon_lon = float(moon_xx[0][0]) % 360 if isinstance(moon_xx[0], (list, tuple)) else float(moon_xx[0]) % 360
    nakshatra_idx = int(moon_lon / (360 / 27))
    nakshatra = NAKSHATRA_NAMES[nakshatra_idx]
    moon_sign, _ = _degree_to_sign(moon_lon)

    # Sun position (for Tithi and Nitya Yoga)
    sun_xx = swe.calc_ut(jd, swe.SUN)
    sun_lon = float(sun_xx[0][0]) % 360 if isinstance(sun_xx[0], (list, tuple)) else float(sun_xx[0]) % 360

    # 1. Nakshatra check (+20 if benefic for intent)
    favorable_naks = INTENT_FAVORABLE_NAKSHATRAS.get(intent, set())
    if nakshatra in favorable_naks:
        score += 20
    details["moon_nakshatra"] = nakshatra

    # 2. Moon sign check (+10)
    if moon_sign in BENEFIC_MOON_SIGNS:
        score += 10

    # 3. Weekday (+10)
    weekday = _get_weekday(jd)
    if weekday in INTENT_WEEKDAYS.get(intent, set()):
        score += 10
    details["vara"] = VARA_NAMES[weekday]

    # 4. Hora lord (+15 if Jupiter or Venus)
    hora_lord = _get_hora_lord(jd, lat, lon)
    if hora_lord in ("Jupiter", "Venus"):
        score += 15
    details["hora_lord"] = hora_lord

    # 5. Rahu Kalam penalty (−30)
    in_rahu = _is_rahu_kalam(jd, lat, lon)
    if in_rahu:
        score -= 30
    details["in_rahu_kalam"] = in_rahu

    # 6. Yamagandam penalty (−20)
    if _is_yamagandam(jd, lat, lon):
        score -= 20

    # 7. Nitya Yoga (+10 if auspicious)
    yoga_idx = int((sun_lon + moon_lon) % 360 / (360 / 27))
    yoga_name = NITYA_YOGA_NAMES[yoga_idx]
    if yoga_name in AUSPICIOUS_YOGA_NAMES:
        score += 10
    details["nitya_yoga"] = yoga_name

    # 8. Tithi (+10 if not inauspicious)
    tithi_num = int((moon_lon - sun_lon) % 360 / 12) + 1
    tithi_name = TITHI_NAMES[(tithi_num - 1) % 15]
    if tithi_num not in INAUSPICIOUS_TITHIS:
        score += 10
    details["tithi"] = tithi_name

    # 9. Personal chart alignment (+15)
    if natal_chart:
        natal_sun_lon = natal_chart.get("tropical", {}).get("planets", {}).get("Sun", {}).get("longitude", -1)
        if natal_sun_lon >= 0:
            diff = abs(moon_lon - natal_sun_lon) % 360
            if diff > 180:
                diff = 360 - diff
            if diff < 30:  # Moon near natal Sun — favorable
                score += 15

    return max(0, score), details


def _jd_to_local_str(jd: float, tz_str: str) -> str:
    """Convert Julian Day to local datetime string."""
    dt_vals = swe.revjul(jd)
    year, month, day = int(dt_vals[0]), int(dt_vals[1]), int(dt_vals[2])
    frac_hour = dt_vals[3]
    hour = int(frac_hour)
    minute = int((frac_hour - hour) * 60)
    dt_utc = datetime(year, month, day, hour, minute, tzinfo=pytz.utc)
    tz = pytz.timezone(tz_str)
    dt_local = dt_utc.astimezone(tz)
    return dt_local.strftime("%Y-%m-%dT%H:%M:%S%z")


# ── Tool ──────────────────────────────────────────────────────────────────────

@tool
def find_muhurta(
    intent: str,
    start_date: str,
    latitude: float,
    longitude: float,
    timezone: str,
    natal_chart_json: str = "null",
) -> str:
    """
    Find the top 3 most auspicious time slots in the next 30 days for a given intent.
    Uses classical Vedic Muhurta rules: nakshatra quality, hora lord, Rahu Kalam avoidance,
    Nitya Yoga, Tithi auspiciousness, and personal chart alignment.

    Args:
        intent: One of: business_launch, travel, marriage, medical_procedure,
                signing_contracts, property_purchase, education_start, spiritual_initiation
        start_date: ISO date string e.g. '2026-05-27'
        latitude: Location latitude (from geocode_place)
        longitude: Location longitude (from geocode_place)
        timezone: Location timezone e.g. 'Asia/Kolkata'
        natal_chart_json: Optional natal chart JSON string for personal alignment scoring
    """
    try:
        # Normalize intent
        intent_normalized = intent.lower().replace(" ", "_").replace("-", "_")
        if intent_normalized not in INTENT_FAVORABLE_NAKSHATRAS:
            intent_normalized = "business_launch"

        natal_chart = json.loads(natal_chart_json) if natal_chart_json not in ("null", "{}") else None

        # Build start JD at local midnight
        tz = pytz.timezone(timezone)
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        start_local = tz.localize(start_dt)
        start_utc = start_local.astimezone(pytz.utc)
        start_jd = swe.julday(start_utc.year, start_utc.month, start_utc.day, 0.0)

        # Scan 30 days × 48 half-hour slots = 1440 slots
        slot_duration = 0.5 / 24.0  # 30 minutes in Julian Days
        slots: list[dict] = []

        for i in range(1440):
            slot_jd = start_jd + i * slot_duration
            score, details = _score_slot(slot_jd, latitude, longitude, intent_normalized, natal_chart)
            if score >= 50:  # Only keep reasonably auspicious slots
                slots.append({
                    "jd": slot_jd,
                    "score": score,
                    "details": details,
                })

        # Sort by score, take top 3
        slots.sort(key=lambda x: x["score"], reverse=True)
        top_slots = []

        # Deduplicate: skip slots within 4 hours of an already-selected slot
        selected_jds: list[float] = []
        for slot in slots:
            too_close = any(abs(slot["jd"] - s) < 4 / 24 for s in selected_jds)
            if not too_close:
                selected_jds.append(slot["jd"])
                local_dt_str = _jd_to_local_str(slot["jd"], timezone)
                top_slots.append({
                    "datetime_local": local_dt_str,
                    "score": slot["score"],
                    "moon_nakshatra": slot["details"]["moon_nakshatra"],
                    "hora_lord": slot["details"]["hora_lord"],
                    "tithi": slot["details"]["tithi"],
                    "nitya_yoga": slot["details"]["nitya_yoga"],
                    "vara": slot["details"]["vara"],
                    "in_rahu_kalam": slot["details"]["in_rahu_kalam"],
                })
                if len(top_slots) == 3:
                    break

        return json.dumps({
            "intent": INTENT_DISPLAY.get(intent_normalized, intent),
            "window_days": 30,
            "top_slots": top_slots,
            "total_slots_scanned": 1440,
            "slots_above_threshold": len(slots),
        })

    except Exception as e:
        return json.dumps({"error": f"Muhurta computation failed: {str(e)}"})