"""
Feature 2: compute_compatibility
Computes full Ashtakoot (36-point) matching + Western synastry aspects.
Requires two natal charts. Used for relationship and marriage compatibility analysis.
"""
import json
from langchain_core.tools import tool

NAKSHATRA_NAMES = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu",
    "Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta",
    "Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha",
    "Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha","Purva Bhadrapada",
    "Uttara Bhadrapada","Revati",
]

# Nadi: 0=Adi, 1=Madhya, 2=Antya
NAKSHATRA_NADI = [
    0,1,2, 0,1,2, 0,1,2, 0,1,2, 0,1,2, 0,1,2, 0,1,2, 0,1,2, 0,1,2,
]

NADI_NAMES = ["Adi (Vata)","Madhya (Pitta)","Antya (Kapha)"]

# Gana: 0=Deva, 1=Manushya, 2=Rakshasa
NAKSHATRA_GANA = [
    0,1,2, 1,0,1, 0,0,2, 2,1,1, 0,2,0, 2,0,2, 2,1,1, 0,2,0, 1,1,0,
]

GANA_NAMES = ["Deva","Manushya","Rakshasa"]

# Varna: 0=Shudra,1=Vaishya,2=Kshatriya,3=Brahmin
NAKSHATRA_VARNA = [
    3,2,3, 0,2,2, 0,2,0, 0,1,2, 3,2,3, 0,2,0, 0,1,1, 0,2,0, 3,2,3,
]

VARNA_NAMES = ["Shudra","Vaishya","Kshatriya","Brahmin"]

NAKSHATRA_YONI = [
    ("horse","M"),("elephant","M"),("sheep","F"),("serpent","M"),("serpent","F"),
    ("dog","F"),("cat","F"),("sheep","M"),("cat","M"),("rat","M"),("rat","F"),
    ("cow","M"),("buffalo","F"),("tiger","F"),("buffalo","M"),("tiger","M"),
    ("hare","F"),("hare","M"),("dog","M"),("monkey","M"),("mongoose","M"),
    ("monkey","F"),("lion","F"),("horse","F"),("lion","M"),("cow","F"),("elephant","F"),
]

YONI_ENEMIES = {
    "cow":"tiger","tiger":"cow","elephant":"lion","lion":"elephant",
    "horse":"buffalo","buffalo":"horse","dog":"hare","hare":"dog",
    "serpent":"mongoose","mongoose":"serpent","cat":"rat","rat":"cat",
    "sheep":"monkey","monkey":"sheep",
}

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

SIGN_LORD = {
    "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon","Leo":"Sun",
    "Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars","Sagittarius":"Jupiter",
    "Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter",
}

PLANET_FRIENDS = {
    "Sun":["Moon","Mars","Jupiter"],"Moon":["Sun","Mercury"],
    "Mars":["Sun","Moon","Jupiter"],"Mercury":["Sun","Venus"],
    "Jupiter":["Sun","Moon","Mars"],"Venus":["Mercury","Saturn"],
    "Saturn":["Mercury","Venus"],
}
PLANET_ENEMIES = {
    "Sun":["Saturn","Venus"],"Moon":[],"Mars":["Mercury"],"Mercury":["Moon"],
    "Jupiter":["Mercury","Venus"],"Venus":["Sun","Moon"],"Saturn":["Sun","Moon","Mars"],
}

ASPECTS = [("conjunction",0,8),("sextile",60,6),("square",90,6),("trine",120,6),("opposition",180,8)]


def _nak_idx(lon: float) -> int:
    return int((lon % 360) / (360 / 27))


def _get_relationship(p_a: str, p_b: str) -> str:
    if p_b in PLANET_FRIENDS.get(p_a, []):
        return "friend"
    if p_b in PLANET_ENEMIES.get(p_a, []):
        return "enemy"
    return "neutral"


def _compute_varna(nak_a: int, nak_b: int) -> dict:
    v_a, v_b = NAKSHATRA_VARNA[nak_a], NAKSHATRA_VARNA[nak_b]
    score = 1 if v_a >= v_b else 0
    return {"score": score, "max": 1, "varna_a": VARNA_NAMES[v_a], "varna_b": VARNA_NAMES[v_b]}


def _compute_vashya(sign_a: str, sign_b: str) -> dict:
    VASHYA = {
        "Aries":["Leo","Scorpio"],"Taurus":["Cancer","Libra"],"Gemini":["Virgo"],
        "Cancer":["Scorpio","Sagittarius"],"Leo":["Libra"],"Virgo":["Pisces","Gemini"],
        "Libra":["Capricorn","Virgo"],"Scorpio":["Cancer"],"Sagittarius":["Pisces"],
        "Capricorn":["Aries","Aquarius"],"Aquarius":["Aries"],"Pisces":["Capricorn"],
    }
    a_to_b = sign_b in VASHYA.get(sign_a, [])
    b_to_a = sign_a in VASHYA.get(sign_b, [])
    score = 2 if (a_to_b and b_to_a) else 1 if (a_to_b or b_to_a) else 0
    return {"score": score, "max": 2}


def _compute_tara(nak_a: int, nak_b: int) -> dict:
    FAVORABLE = {2, 4, 6, 8, 9}
    count_ab = (nak_b - nak_a) % 27 + 1
    count_ba = (nak_a - nak_b) % 27 + 1
    tara_ab = ((count_ab - 1) % 9) + 1
    tara_ba = ((count_ba - 1) % 9) + 1
    score = (1.5 if tara_ab in FAVORABLE else 0) + (1.5 if tara_ba in FAVORABLE else 0)
    return {"score": score, "max": 3}


def _compute_yoni(nak_a: int, nak_b: int) -> dict:
    animal_a, gender_a = NAKSHATRA_YONI[nak_a]
    animal_b, gender_b = NAKSHATRA_YONI[nak_b]
    if animal_a == animal_b:
        score = 4 if gender_a != gender_b else 0
    elif YONI_ENEMIES.get(animal_a) == animal_b:
        score = 0
    elif gender_a != gender_b:
        score = 3
    else:
        score = 2
    return {"score": score, "max": 4, "yoni_a": f"{animal_a} ({gender_a})", "yoni_b": f"{animal_b} ({gender_b})"}


def _compute_graha_maitri(sign_a: str, sign_b: str) -> dict:
    lord_a = SIGN_LORD.get(sign_a, "")
    lord_b = SIGN_LORD.get(sign_b, "")
    rel_ab = _get_relationship(lord_a, lord_b)
    rel_ba = _get_relationship(lord_b, lord_a)
    scores = {"friend": 1, "neutral": 0.5, "enemy": 0}
    score = scores[rel_ab] * 2.5 + scores[rel_ba] * 2.5
    return {"score": min(5, score), "max": 5, "lord_a": lord_a, "lord_b": lord_b}


def _compute_gana(nak_a: int, nak_b: int) -> dict:
    g_a, g_b = NAKSHATRA_GANA[nak_a], NAKSHATRA_GANA[nak_b]
    if g_a == g_b:
        score = 6
    elif (g_a == 0 and g_b == 1) or (g_a == 1 and g_b == 0):
        score = 5
    elif (g_a == 1 and g_b == 2) or (g_a == 2 and g_b == 1):
        score = 1
    else:  # Deva-Rakshasa
        score = 0
        return {"score": score, "max": 6, "gana_a": GANA_NAMES[g_a], "gana_b": GANA_NAMES[g_b], "dosha": True}
    return {"score": score, "max": 6, "gana_a": GANA_NAMES[g_a], "gana_b": GANA_NAMES[g_b]}


def _compute_bhakoot(sign_a: str, sign_b: str) -> dict:
    idx_a = SIGNS.index(sign_a) if sign_a in SIGNS else 0
    idx_b = SIGNS.index(sign_b) if sign_b in SIGNS else 0
    diff = (idx_b - idx_a) % 12 + 1
    rev = (idx_a - idx_b) % 12 + 1
    dosha = (diff == 2 and rev == 12) or (diff == 12 and rev == 2) or \
            (diff == 6 and rev == 8) or (diff == 8 and rev == 6)
    score = 0 if dosha else 7
    return {"score": score, "max": 7, "dosha": dosha,
            "dosha_type": "Bhakoot Dosha (2-12 axis)" if dosha and abs(diff - rev) == 10 else
                          "Bhakoot Dosha (6-8 axis)" if dosha else None}


def _compute_nadi(nak_a: int, nak_b: int) -> dict:
    nadi_a = NAKSHATRA_NADI[nak_a]
    nadi_b = NAKSHATRA_NADI[nak_b]
    dosha = nadi_a == nadi_b
    score = 0 if dosha else 8
    return {"score": score, "max": 8, "nadi_a": NADI_NAMES[nadi_a], "nadi_b": NADI_NAMES[nadi_b],
            "dosha": dosha, "dosha_type": "Nadi Dosha" if dosha else None}


def _compute_synastry(chart_a: dict, chart_b: dict) -> list[dict]:
    aspects = []
    planets_a = chart_a.get("tropical", {}).get("planets", {})
    planets_b = chart_b.get("tropical", {}).get("planets", {})
    for pa, da in planets_a.items():
        for pb, db in planets_b.items():
            for asp_name, angle, orb in ASPECTS:
                diff = abs(float(da.get("longitude", 0)) - float(db.get("longitude", 0))) % 360
                if diff > 180:
                    diff = 360 - diff
                actual_orb = abs(diff - angle)
                if actual_orb <= orb:
                    aspects.append({
                        "planet_a": pa, "planet_b": pb, "aspect": asp_name,
                        "orb": round(actual_orb, 2),
                        "nature": "harmonious" if asp_name in ("trine","sextile") else
                                  "tense" if asp_name in ("square","opposition") else "powerful",
                    })
    aspects.sort(key=lambda x: x["orb"])
    return aspects[:10]


@tool
def compute_compatibility(
    chart_a_json: str,
    chart_b_json: str,
    name_a: str = "Person A",
    name_b: str = "Person B",
) -> str:
    """
    Compute full Vedic Ashtakoot compatibility (36 points) plus Western synastry
    between two natal charts. Checks all 8 Kutas: Varna, Vashya, Tara, Yoni,
    Graha Maitri, Gana, Bhakoot, and Nadi. Identifies Doshas. Returns total score,
    breakdown, and synastry aspects.

    Args:
        chart_a_json: JSON string of natal chart for Person A (from compute_birth_chart)
        chart_b_json: JSON string of natal chart for Person B (from compute_birth_chart)
        name_a: Name of Person A
        name_b: Name of Person B
    """
    try:
        chart_a = json.loads(chart_a_json)
        chart_b = json.loads(chart_b_json)

        moon_lon_a = float(chart_a.get("sidereal",{}).get("planets",{}).get("Moon",{}).get("longitude", 0))
        moon_lon_b = float(chart_b.get("sidereal",{}).get("planets",{}).get("Moon",{}).get("longitude", 0))
        moon_sign_a = chart_a.get("sidereal",{}).get("planets",{}).get("Moon",{}).get("sign","")
        moon_sign_b = chart_b.get("sidereal",{}).get("planets",{}).get("Moon",{}).get("sign","")

        nak_a = _nak_idx(moon_lon_a)
        nak_b = _nak_idx(moon_lon_b)

        scores = {
            "Varna":        _compute_varna(nak_a, nak_b),
            "Vashya":       _compute_vashya(moon_sign_a, moon_sign_b),
            "Tara":         _compute_tara(nak_a, nak_b),
            "Yoni":         _compute_yoni(nak_a, nak_b),
            "Graha Maitri": _compute_graha_maitri(moon_sign_a, moon_sign_b),
            "Gana":         _compute_gana(nak_a, nak_b),
            "Bhakoot":      _compute_bhakoot(moon_sign_a, moon_sign_b),
            "Nadi":         _compute_nadi(nak_a, nak_b),
        }

        total = sum(v["score"] for v in scores.values())
        doshas = [k for k, v in scores.items() if v.get("dosha")]

        if total >= 28:
            overall = "Excellent — Highly Compatible"
        elif total >= 21:
            overall = "Good — Compatible with areas of growth"
        elif total >= 18:
            overall = "Average — Requires mutual understanding and effort"
        else:
            overall = "Challenging — Significant differences to navigate with patience"

        synastry = _compute_synastry(chart_a, chart_b)

        return json.dumps({
            "names": {"a": name_a, "b": name_b},
            "moon_nakshatra": {
                "a": f"{NAKSHATRA_NAMES[nak_a]} (Moon in {moon_sign_a})",
                "b": f"{NAKSHATRA_NAMES[nak_b]} (Moon in {moon_sign_b})",
            },
            "ashtakoot": {
                "total_score": round(total, 1),
                "out_of": 36,
                "percentage": round(total / 36 * 100, 1),
                "breakdown": scores,
                "doshas_present": doshas,
                "overall": overall,
            },
            "western_synastry": {"aspects": synastry},
        })

    except Exception as e:
        return json.dumps({"error": f"Compatibility computation failed: {str(e)}"})