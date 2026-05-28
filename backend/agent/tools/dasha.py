"""
Feature 5: compute_dasha_timeline
Computes the complete Vimshottari Dasha system from birth — the most important
predictive tool in Vedic astrology. Returns the 120-year life period timeline
with current Mahadasha, Antardasha, and upcoming transitions.
"""
import json
from datetime import datetime, timedelta

import swisseph as swe
from langchain_core.tools import tool

VIMSHOTTARI_ORDER = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}

NAKSHATRA_NAMES = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu",
    "Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta",
    "Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha",
    "Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha","Purva Bhadrapada",
    "Uttara Bhadrapada","Revati",
]

NAKSHATRA_LORDS = [
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
]

PLANET_COLORS = {
    "Ketu": "#9B59B6", "Venus": "#F0E6FF", "Sun": "#FFB347", "Moon": "#C8D6E5",
    "Mars": "#CC2936", "Rahu": "#2C3E50", "Jupiter": "#F4D03F", "Saturn": "#7F7F7F",
    "Mercury": "#2ECC71",
}


def _compute_antardasha(maha_planet: str, maha_start: datetime, maha_end: datetime) -> list[dict]:
    """Compute all 9 antardashas within a Mahadasha."""
    maha_total_days = (maha_end - maha_start).days
    start_idx = VIMSHOTTARI_ORDER.index(maha_planet)

    antardashas = []
    current = maha_start

    for i in range(9):
        antar_planet = VIMSHOTTARI_ORDER[(start_idx + i) % 9]
        antar_years = VIMSHOTTARI_YEARS[antar_planet]
        antar_days = int(maha_total_days * antar_years / 120)
        antar_end = current + timedelta(days=antar_days)

        antardashas.append({
            "planet": antar_planet,
            "start": current.strftime("%Y-%m-%d"),
            "end": antar_end.strftime("%Y-%m-%d"),
            "years": round(antar_years * maha_total_days / 120 / 365.25, 2),
        })
        current = antar_end

    # Adjust last antardasha to exactly end when mahadasha ends
    if antardashas:
        antardashas[-1]["end"] = maha_end.strftime("%Y-%m-%d")

    return antardashas


def _find_current_period(timeline: list[dict], target_date: datetime) -> tuple[dict | None, dict | None]:
    for dasha in timeline:
        start = datetime.fromisoformat(dasha["start"])
        end = datetime.fromisoformat(dasha["end"])
        if start <= target_date <= end:
            current_antardasha = None
            for ad in dasha.get("antardasha", []):
                ad_start = datetime.fromisoformat(ad["start"])
                ad_end = datetime.fromisoformat(ad["end"])
                if ad_start <= target_date <= ad_end:
                    current_antardasha = ad
                    break
            return dasha, current_antardasha
    return None, None


@tool
def compute_dasha_timeline(natal_chart_json: str, target_date: str = "") -> str:
    """
    Compute the complete Vimshottari Dasha timeline — the 120-year sequence of
    planetary life periods in Vedic astrology. Returns all Mahadashas with their
    Antardashas, identifies the current period and its interpretation key,
    and notes upcoming transitions.

    Args:
        natal_chart_json: JSON string of the natal chart from compute_birth_chart
        target_date: Date to find current period for. Defaults to today.
                     Format: 'YYYY-MM-DD'
    """
    try:
        natal_chart = json.loads(natal_chart_json)
        birth_details = natal_chart.get("birth_details", {})

        birth_date_str = birth_details.get("date", "")
        birth_time_str = birth_details.get("time") or "12:00"
        if not birth_date_str:
            return json.dumps({"error": "Birth date missing from natal chart"})

        birth_dt = datetime.strptime(f"{birth_date_str} {birth_time_str}", "%Y-%m-%d %H:%M")

        # Birth Moon longitude (sidereal)
        moon_lon = natal_chart.get("sidereal", {}).get("planets", {}).get("Moon", {}).get("longitude", 0)
        moon_lon = float(moon_lon) % 360

        # Birth nakshatra
        nak_idx = int(moon_lon / (360 / 27))
        birth_nak = NAKSHATRA_NAMES[nak_idx]
        birth_dasha_lord = NAKSHATRA_LORDS[nak_idx]

        # Balance of first dasha
        nak_start_lon = nak_idx * (360 / 27)
        fraction_traversed = (moon_lon - nak_start_lon) / (360 / 27)
        full_years = VIMSHOTTARI_YEARS[birth_dasha_lord]
        years_elapsed = fraction_traversed * full_years
        years_remaining = full_years - years_elapsed

        # Build complete timeline
        timeline: list[dict] = []
        current_dt = birth_dt

        # First dasha (partial)
        first_end = current_dt + timedelta(days=years_remaining * 365.25)
        antardashas = _compute_antardasha(birth_dasha_lord, current_dt, first_end)
        timeline.append({
            "planet": birth_dasha_lord,
            "start": current_dt.strftime("%Y-%m-%d"),
            "end": first_end.strftime("%Y-%m-%d"),
            "years": round(years_remaining, 2),
            "partial": True,
            "color": PLANET_COLORS.get(birth_dasha_lord, "#888888"),
            "antardasha": antardashas,
        })
        current_dt = first_end

        # Remaining 8 full dashas
        start_idx = (VIMSHOTTARI_ORDER.index(birth_dasha_lord) + 1) % 9
        for i in range(8):
            planet = VIMSHOTTARI_ORDER[(start_idx + i) % 9]
            years = VIMSHOTTARI_YEARS[planet]
            dasha_end = current_dt + timedelta(days=years * 365.25)
            antardashas = _compute_antardasha(planet, current_dt, dasha_end)
            timeline.append({
                "planet": planet,
                "start": current_dt.strftime("%Y-%m-%d"),
                "end": dasha_end.strftime("%Y-%m-%d"),
                "years": years,
                "partial": False,
                "color": PLANET_COLORS.get(planet, "#888888"),
                "antardasha": antardashas,
            })
            current_dt = dasha_end

        # Final partial dasha — completes the 120-year cycle.
        # The birth lord's period was entered mid-way at birth (years_elapsed was
        # already consumed). That consumed fraction wraps back at the end of the
        # cycle: partial_first(years_remaining) + 8_full(120-Y) + partial_last(years_elapsed) = 120.
        if years_elapsed > 0:
            final_end = current_dt + timedelta(days=years_elapsed * 365.25)
            antardashas = _compute_antardasha(birth_dasha_lord, current_dt, final_end)
            timeline.append({
                "planet": birth_dasha_lord,
                "start": current_dt.strftime("%Y-%m-%d"),
                "end": final_end.strftime("%Y-%m-%d"),
                "years": round(years_elapsed, 2),
                "partial": True,
                "color": PLANET_COLORS.get(birth_dasha_lord, "#888888"),
                "antardasha": antardashas,
            })

        # Current period
        target_dt = datetime.strptime(target_date, "%Y-%m-%d") if target_date else datetime.utcnow()
        current_maha, current_antar = _find_current_period(timeline, target_dt)

        # Next transition
        next_transition = None
        if current_maha:
            maha_end = datetime.fromisoformat(current_maha["end"])
            days_remaining = (maha_end - target_dt).days
            next_transition = {
                "from_planet": current_maha["planet"],
                "to_planet": None,
                "date": current_maha["end"],
                "days_away": days_remaining,
            }
            maha_idx = next((i for i, d in enumerate(timeline) if d["planet"] == current_maha["planet"] and d["start"] == current_maha["start"]), -1)
            if maha_idx >= 0 and maha_idx < len(timeline) - 1:
                next_transition["to_planet"] = timeline[maha_idx + 1]["planet"]

        return json.dumps({
            "birth_nakshatra": birth_nak,
            "birth_dasha_lord": birth_dasha_lord,
            "dasha_balance_at_birth": f"{round(years_remaining, 1)} years of {birth_dasha_lord} remaining at birth",
            "timeline": timeline,
            "current_period": {
                "mahadasha": current_maha,
                "antardasha": current_antar,
                "interpretation_key": (
                    f"{current_maha['planet'].lower()}_mahadasha_"
                    f"{current_antar['planet'].lower()}_antardasha"
                    if current_maha and current_antar else "unknown"
                ),
            },
            "next_transition": next_transition,
        })

    except Exception as e:
        return json.dumps({"error": f"Dasha computation failed: {str(e)}"})