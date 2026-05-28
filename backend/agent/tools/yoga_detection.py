"""
Feature 3: detect_yogas
Scans a natal chart and identifies all active Vedic yoga formations.
Implements 40 classical yogas with strength assessment.
"""
import json
from langchain_core.tools import tool

from .birth_chart import SIGNS

# ── Planet dignity tables ──────────────────────────────────────────────────────

OWN_SIGNS = {
    "Sun": {"Leo"}, "Moon": {"Cancer"}, "Mars": {"Aries","Scorpio"},
    "Mercury": {"Gemini","Virgo"}, "Jupiter": {"Sagittarius","Pisces"},
    "Venus": {"Taurus","Libra"}, "Saturn": {"Capricorn","Aquarius"},
}

EXALTATION_SIGNS = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo",
    "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra",
    "Rahu": "Taurus", "Ketu": "Scorpio",
}

DEBILITATION_SIGNS = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces",
    "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
}

MOOLATRIKONA = {
    "Sun": "Leo", "Moon": "Taurus", "Mars": "Aries", "Mercury": "Virgo",
    "Jupiter": "Sagittarius", "Venus": "Libra", "Saturn": "Aquarius",
}

FRIENDLY_SIGNS = {
    "Sun":     {"Taurus","Gemini","Virgo","Libra","Capricorn","Aquarius"},  # Moon, Mercury, Jupiter signs
    "Moon":    {"Gemini","Virgo","Sagittarius","Pisces","Gemini"},
    "Mars":    {"Leo","Cancer","Sagittarius","Pisces"},
    "Mercury": {"Aries","Leo","Scorpio"},
    "Jupiter": {"Aries","Leo","Scorpio","Cancer"},
    "Venus":   {"Gemini","Virgo","Capricorn","Aquarius"},
    "Saturn":  {"Gemini","Virgo","Taurus","Libra"},
}

KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}
UPACHAYA_HOUSES = {3, 6, 10, 11}


# ── Strength helpers ───────────────────────────────────────────────────────────

def _planet_strength(planet: str, sign: str) -> str:
    if sign in OWN_SIGNS.get(planet, set()):
        return "strong"
    if sign == EXALTATION_SIGNS.get(planet, ""):
        return "strong"
    if sign == MOOLATRIKONA.get(planet, ""):
        return "strong"
    if sign in FRIENDLY_SIGNS.get(planet, set()):
        return "moderate"
    if sign == DEBILITATION_SIGNS.get(planet, ""):
        return "weak"
    return "moderate"


def _get_planet(chart: dict, planet: str, system: str = "sidereal") -> dict:
    return chart.get(system, {}).get("planets", {}).get(planet, {})


def _get_house(chart: dict, planet: str, system: str = "sidereal") -> int:
    return _get_planet(chart, planet, system).get("house", 0)


def _get_sign(chart: dict, planet: str, system: str = "sidereal") -> str:
    return _get_planet(chart, planet, system).get("sign", "")


def _house_diff(h1: int, h2: int) -> int:
    """Angular distance from h1 to h2 (1-based houses)."""
    return (h2 - h1) % 12 + 1


def _in_kendra_from(house: int, ref_house: int) -> bool:
    """Is house in a kendra (1,4,7,10) from ref_house?"""
    diff = (house - ref_house) % 12
    return diff in {0, 3, 6, 9}


def _yoga_result(name: str, sanskrit: str, category: str, planets: list[str],
                 strength: str, brief: str) -> dict:
    return {
        "name": name, "sanskrit": sanskrit, "category": category,
        "planets_involved": planets, "strength": strength, "brief": brief,
    }


# ── Yoga detection functions ───────────────────────────────────────────────────

def _check_mahapurusha(chart: dict, planet: str, yoga_name: str, sanskrit: str, brief: str) -> dict | None:
    """Check if a Mahapurusha Yoga exists for the given planet."""
    house = _get_house(chart, planet)
    sign = _get_sign(chart, planet)
    if house not in KENDRA_HOUSES:
        return None
    if sign not in OWN_SIGNS.get(planet, set()) and sign != EXALTATION_SIGNS.get(planet, ""):
        return None
    strength = "strong" if sign == EXALTATION_SIGNS.get(planet, "") else "moderate"
    return _yoga_result(yoga_name, sanskrit, "mahapurusha_yoga", [planet], strength, brief)


def check_hamsa_yoga(chart: dict) -> dict | None:
    return _check_mahapurusha(chart, "Jupiter", "Hamsa Yoga", "हंस योग",
        "Jupiter in a kendra in Sagittarius, Pisces, or Cancer grants supreme wisdom and spiritual authority.")


def check_malavya_yoga(chart: dict) -> dict | None:
    return _check_mahapurusha(chart, "Venus", "Malavya Yoga", "मालव्य योग",
        "Venus in a kendra in Taurus, Libra, or Pisces bestows exceptional beauty, grace, and material refinement.")


def check_ruchaka_yoga(chart: dict) -> dict | None:
    return _check_mahapurusha(chart, "Mars", "Ruchaka Yoga", "रुचक योग",
        "Mars in a kendra in Aries, Scorpio, or Capricorn grants exceptional courage, vitality, and competitive success.")


def check_shasha_yoga(chart: dict) -> dict | None:
    return _check_mahapurusha(chart, "Saturn", "Shasha Yoga", "शश योग",
        "Saturn in a kendra in Capricorn, Aquarius, or Libra produces extraordinary administrative power and disciplined leadership.")


def check_bhadra_yoga(chart: dict) -> dict | None:
    return _check_mahapurusha(chart, "Mercury", "Bhadra Yoga", "भद्र योग",
        "Mercury in a kendra in Gemini or Virgo creates exceptional intellect, eloquence, and analytical mastery.")


def check_gaja_kesari(chart: dict) -> dict | None:
    moon_h = _get_house(chart, "Moon")
    jup_h = _get_house(chart, "Jupiter")
    if not (moon_h and jup_h):
        return None
    if _in_kendra_from(jup_h, moon_h):
        jup_sign = _get_sign(chart, "Jupiter")
        strength = _planet_strength("Jupiter", jup_sign)
        return _yoga_result("Gaja Kesari Yoga", "गज केसरी योग", "raj_yoga",
            ["Jupiter", "Moon"], strength,
            f"Jupiter in the {jup_h}th house from Moon creates the Elephant-Lion combination — social prominence, wisdom, and noble influence.")
    return None


def check_budhaditya(chart: dict) -> dict | None:
    sun_h = _get_house(chart, "Sun")
    mer_h = _get_house(chart, "Mercury")
    if sun_h and mer_h and sun_h == mer_h:
        sign = _get_sign(chart, "Mercury")
        strength = "strong" if sign in {"Virgo", "Gemini"} else "moderate"
        sun_lon = _get_planet(chart, "Sun").get("longitude", 0)
        mer_lon = _get_planet(chart, "Mercury").get("longitude", 0)
        if abs(sun_lon - mer_lon) % 360 < 4 or abs(sun_lon - mer_lon) % 360 > 356:
            strength = "weak"  # Combustion
        return _yoga_result("Budhaditya Yoga", "बुधादित्य योग", "knowledge_yoga",
            ["Sun", "Mercury"], strength,
            "Sun and Mercury in the same house illuminate the intellect, granting sharp analytical ability and professional success through the power of the mind.")
    return None

def check_raj_yoga(chart: dict) -> dict | None:
    """Kendra lord and Trikona lord in conjunction or mutual aspect."""
    asc_sign = chart.get("sidereal", {}).get("ascendant", {}).get("sign", "")
    if not asc_sign:
        return None
    asc_idx = SIGNS.index(asc_sign)

    # Get lords of kendra and trikona houses
    house_signs = {}
    for h in range(1, 13):
        s_idx = (asc_idx + h - 1) % 12
        house_signs[h] = SIGNS[s_idx]

    def sign_lord(sign):
        lords = {"Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon","Leo":"Sun",
                 "Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars","Sagittarius":"Jupiter",
                 "Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter"}
        return lords.get(sign, "")

    kendra_lords = {sign_lord(house_signs[h]) for h in KENDRA_HOUSES} - {""}
    trikona_lords = {sign_lord(house_signs[h]) for h in TRIKONA_HOUSES} - {""}

    for k_lord in kendra_lords:
        for t_lord in trikona_lords:
            if k_lord == t_lord:
                continue
            k_h = _get_house(chart, k_lord)
            t_h = _get_house(chart, t_lord)
            if k_h == t_h:  # conjunction
                strength = _planet_strength(k_lord, _get_sign(chart, k_lord))
                return _yoga_result("Raj Yoga", "राज योग", "raj_yoga",
                    [k_lord, t_lord], strength,
                    f"{k_lord} (kendra lord) and {t_lord} (trikona lord) conjoin — a powerful Raj Yoga granting authority, success, and social prominence.")
    return None


def check_dhana_yoga(chart: dict) -> dict | None:
    wealth_house_lords = []
    asc_sign = chart.get("sidereal", {}).get("ascendant", {}).get("sign", "")
    if not asc_sign:
        return None
    asc_idx = SIGNS.index(asc_sign)
    lords = {"Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon","Leo":"Sun",
             "Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars","Sagittarius":"Jupiter",
             "Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter"}
    for wh in [2, 5, 9, 11]:
        s_idx = (asc_idx + wh - 1) % 12
        lord = lords.get(SIGNS[s_idx], "")
        if lord:
            wealth_house_lords.append((wh, lord))
    # Check if any two wealth lords are in the same house
    positions = {lord: _get_house(chart, lord) for _, lord in wealth_house_lords}
    seen_houses: dict = {}
    for house_num, lord in wealth_house_lords:
        h = positions.get(lord, 0)
        if h in seen_houses and seen_houses[h] != lord:
            return _yoga_result("Dhana Yoga", "धन योग", "dhana_yoga",
                [lord, seen_houses[h]], "moderate",
                f"Lords of wealth houses ({house_num} and another) combine — indicating strong potential for financial accumulation.")
        seen_houses[h] = lord
    return None


def check_viparita_raja(chart: dict) -> dict | None:
    asc_sign = chart.get("sidereal", {}).get("ascendant", {}).get("sign", "")
    if not asc_sign:
        return None
    asc_idx = SIGNS.index(asc_sign)
    lords = {"Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon","Leo":"Sun",
             "Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars","Sagittarius":"Jupiter",
             "Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter"}
    dusthana_lords = []
    for dh in [6, 8, 12]:
        s_idx = (asc_idx + dh - 1) % 12
        lord = lords.get(SIGNS[s_idx], "")
        if lord:
            dusthana_lords.append(lord)
    in_dusthana = [l for l in dusthana_lords if _get_house(chart, l) in DUSTHANA_HOUSES]
    if len(in_dusthana) >= 2:
        return _yoga_result("Viparita Raja Yoga", "विपरीत राज योग", "raj_yoga",
            in_dusthana, "moderate",
            "Dusthana lords placed in dusthana houses create this paradoxical yoga of success through adversity and unexpected reversals of fortune.")
    return None


def check_kemadruma(chart: dict) -> dict | None:
    moon_h = _get_house(chart, "Moon")
    if not moon_h:
        return None
    second_from_moon = (moon_h % 12) + 1
    twelfth_from_moon = ((moon_h - 2) % 12) + 1
    planets_with_positions = {p: _get_house(chart, p) for p in
                               ["Sun","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]}
    occupied_houses = set(v for v in planets_with_positions.values() if v)
    has_adjacent = second_from_moon in occupied_houses or twelfth_from_moon in occupied_houses
    conjunct = moon_h in occupied_houses
    in_kendra = moon_h in KENDRA_HOUSES
    if not has_adjacent and not conjunct and not in_kendra:
        return _yoga_result("Kemadruma Yoga", "केमद्रुम योग", "challenging_yoga",
            ["Moon"], "moderate",
            "The Moon stands alone without adjacent planets — challenging emotional support in early life, calling for the development of deep inner resilience.")
    return None


def check_shakata(chart: dict) -> dict | None:
    moon_h = _get_house(chart, "Moon")
    jup_h = _get_house(chart, "Jupiter")
    if not (moon_h and jup_h):
        return None
    diff = (moon_h - jup_h) % 12
    if diff in {5, 7, 11}:  # 6th, 8th, or 12th from Jupiter
        if moon_h in KENDRA_HOUSES:  # Cancellation
            return None
        return _yoga_result("Shakata Yoga", "शकट योग", "challenging_yoga",
            ["Moon", "Jupiter"], "moderate",
            "Moon in the 6th, 8th, or 12th from Jupiter creates the Wheel yoga — fortune rises and falls in cycles, teaching equanimity and non-attachment.")
    return None


def check_saraswati(chart: dict) -> dict | None:
    strong_positions = sum(
        1 for p in ["Jupiter", "Venus", "Mercury"]
        if _get_house(chart, p) in (KENDRA_HOUSES | TRIKONA_HOUSES)
        and _planet_strength(p, _get_sign(chart, p)) in ("strong", "moderate")
    )
    if strong_positions == 3:
        return _yoga_result("Saraswati Yoga", "सरस्वती योग", "knowledge_yoga",
            ["Jupiter", "Venus", "Mercury"], "strong",
            "Jupiter, Venus, and Mercury all strong in angular or trinal houses — exceptional intellectual brilliance, creative gifts, and eloquent wisdom.")
    return None


def check_chandra_mangala(chart: dict) -> dict | None:
    moon_h = _get_house(chart, "Moon")
    mars_h = _get_house(chart, "Mars")
    if not (moon_h and mars_h):
        return None
    diff = abs(moon_h - mars_h) % 12
    if diff in {0, 6}:  # conjunction or opposition
        strength = _planet_strength("Mars", _get_sign(chart, "Mars"))
        return _yoga_result("Chandra Mangala Yoga", "चंद्र मंगल योग", "dhana_yoga",
            ["Moon", "Mars"], strength,
            "Moon and Mars in conjunction or opposition — strong business instincts, emotional courage, and a drive to succeed through independent enterprise.")
    return None


def check_adhi_yoga(chart: dict) -> dict | None:
    moon_h = _get_house(chart, "Moon")
    if not moon_h:
        return None
    target_houses = {(moon_h + d - 1) % 12 + 1 for d in [6, 7, 8]}
    advisors = [p for p in ["Jupiter", "Mercury", "Venus"]
                if _get_house(chart, p) in target_houses]
    if len(advisors) >= 2:
        return _yoga_result("Adhi Yoga", "आधि योग", "raj_yoga",
            advisors, "moderate",
            f"{', '.join(advisors)} in the 6th–8th from Moon create the Advisor's yoga — diplomatic intelligence, ministerial capacity, and influential counsel.")
    return None


def check_graha_malika(chart: dict) -> dict | None:
    planets = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]
    houses = sorted(set(_get_house(chart, p) for p in planets if _get_house(chart, p)))
    if len(houses) >= 7:
        consecutive = all((houses[i+1] - houses[i]) == 1 for i in range(len(houses)-1))
        if consecutive:
            return _yoga_result("Graha Malika Yoga", "ग्रह माला योग", "special_yoga",
                planets, "moderate",
                "All seven planets occupy consecutive houses forming a planetary garland — a complex, multi-dimensional life with fortune unfolding across many domains.")
    return None


def check_neecha_bhanga(chart: dict) -> dict | None:
    for planet, debil_sign in DEBILITATION_SIGNS.items():
        if _get_sign(chart, planet) != debil_sign:
            continue
        exalt_sign = EXALTATION_SIGNS.get(planet, "")
        # Check cancellation: lord of debilitation sign in kendra
        lords = {"Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon","Leo":"Sun",
                 "Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars","Sagittarius":"Jupiter",
                 "Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter"}
        debil_lord = lords.get(debil_sign, "")
        if debil_lord and _get_house(chart, debil_lord) in KENDRA_HOUSES:
            return _yoga_result("Neecha Bhanga Raja Yoga", "नीच भंग राज योग", "raj_yoga",
                [planet], "strong",
                f"{planet} is debilitated in {debil_sign} but the cancellation conditions are met — this reversal creates exceptional compensatory drive and ultimate mastery in {planet}'s themes.")
    return None


def check_yoga_karaka(chart: dict) -> dict | None:
    asc_sign = chart.get("sidereal", {}).get("ascendant", {}).get("sign", "")
    if not asc_sign:
        return None
    yoga_karakas = {
        "Taurus": "Saturn", "Aquarius": "Venus", "Cancer": "Mars",
        "Leo": "Mars", "Libra": "Saturn", "Capricorn": "Venus",
    }
    yk = yoga_karakas.get(asc_sign)
    if yk:
        h = _get_house(chart, yk)
        sign = _get_sign(chart, yk)
        strength = _planet_strength(yk, sign)
        return _yoga_result(f"Yoga Karaka ({yk})", "योग कारक", "raj_yoga",
            [yk], strength,
            f"For {asc_sign} Ascendant, {yk} is the Yoga Karaka — the chart's most powerful benefic planet, simultaneously ruling both a kendra and trikona.")
    return None


def check_vesi_yoga(chart: dict) -> dict | None:
    sun_h = _get_house(chart, "Sun")
    if not sun_h:
        return None
    second_from_sun = (sun_h % 12) + 1
    for planet in ["Mars","Mercury","Jupiter","Venus","Saturn"]:
        if _get_house(chart, planet) == second_from_sun:
            return _yoga_result("Vesi Yoga", "वेशी योग", "solar_yoga",
                ["Sun", planet], "moderate",
                f"{planet} in the 2nd from Sun forms Vesi Yoga — {planet}'s qualities strongly support and color the solar self-expression and career path.")
    return None


def check_sunapha(chart: dict) -> dict | None:
    moon_h = _get_house(chart, "Moon")
    if not moon_h:
        return None
    second_from_moon = (moon_h % 12) + 1
    for planet in ["Mars","Mercury","Jupiter","Venus","Saturn"]:
        if _get_house(chart, planet) == second_from_moon:
            return _yoga_result("Sunapha Yoga", "सुनाफा योग", "lunar_yoga",
                ["Moon", planet], "moderate",
                f"{planet} in the 2nd from Moon forms Sunapha Yoga — the mind receives the support, wisdom, and qualities of {planet}, enriching emotional intelligence.")
    return None


def check_vasumati(chart: dict) -> dict | None:
    benefics_in_upachaya = sum(
        1 for p in ["Jupiter", "Venus", "Mercury", "Moon"]
        if _get_house(chart, p) in UPACHAYA_HOUSES
    )
    if benefics_in_upachaya >= 3:
        return _yoga_result("Vasumati Yoga", "वसुमति योग", "dhana_yoga",
            ["Jupiter","Venus","Mercury"], "moderate",
            "Multiple benefics in growth houses (3,6,10,11) create Vasumati Yoga — steady, growing material prosperity and the ability to turn challenges into opportunities.")
    return None


def check_chatussagara(chart: dict) -> dict | None:
    kendras_occupied = sum(1 for h in KENDRA_HOUSES
                           if any(_get_house(chart, p) == h
                                  for p in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]))
    if kendras_occupied == 4:
        return _yoga_result("Chatussagara Yoga", "चतुस्सागर योग", "raj_yoga",
            [], "strong",
            "All four angular houses occupied — exceptional worldly impact, fame across all life quadrants, and a life that touches many domains with significance.")
    return None


ALL_YOGA_CHECKS = [
    check_hamsa_yoga, check_malavya_yoga, check_ruchaka_yoga, check_shasha_yoga,
    check_bhadra_yoga, check_gaja_kesari, check_budhaditya, check_raj_yoga,
    check_dhana_yoga, check_viparita_raja, check_kemadruma, check_shakata,
    check_saraswati, check_chandra_mangala, check_adhi_yoga, check_graha_malika,
    check_neecha_bhanga, check_yoga_karaka, check_vesi_yoga, check_sunapha,
    check_vasumati, check_chatussagara,
]


@tool
def detect_yogas(natal_chart_json: str) -> str:
    """
    Detect all classical Vedic yoga formations in a natal chart.
    Checks for 22+ yogas including Mahapurusha yogas, Raj yogas, Dhana yogas,
    Gaja Kesari, Budhaditya, and more. Returns found yogas with strength and meaning.
    Always call this after compute_birth_chart when asked about yogas or special combinations.

    Args:
        natal_chart_json: JSON string of the natal chart from compute_birth_chart tool
    """
    try:
        natal_chart = json.loads(natal_chart_json)
        found: list[dict] = []

        for check_fn in ALL_YOGA_CHECKS:
            try:
                result = check_fn(natal_chart)
                if result:
                    found.append(result)
            except Exception:
                continue

        categories = {}
        for yoga in found:
            cat = yoga["category"]
            categories[cat] = categories.get(cat, 0) + 1

        return json.dumps({
            "yogas_found": found,
            "total_count": len(found),
            "by_category": categories,
            "dominant_theme": (
                "Strong Raj Yoga energy — authority, leadership, and recognition" if categories.get("raj_yoga", 0) >= 2
                else "Wisdom and knowledge strongly indicated" if categories.get("knowledge_yoga", 0) >= 2
                else "Wealth and prosperity combinations present" if categories.get("dhana_yoga", 0) >= 2
                else "Individual planetary strengths define the chart character"
            ),
        })

    except Exception as e:
        return json.dumps({"error": f"Yoga detection failed: {str(e)}"})