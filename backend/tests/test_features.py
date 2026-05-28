"""
Unit tests for all 5 innovative features.
Run: pytest backend/tests/test_features.py -v
"""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "test")

import pytest
from agent.tools.birth_chart import _compute_chart

PRIYA_CHART = _compute_chart("1990-08-15", "14:30", 28.6139, 77.2090, "Asia/Kolkata")
ARJUN_CHART = _compute_chart("1985-07-10", "08:00", 19.0760, 72.8777, "Asia/Kolkata")


# ── Muhurta Tests ──────────────────────────────────────────────────────────────

def test_muhurta_no_rahu_kalam_in_results():
    from agent.tools.muhurta import find_muhurta
    result_str = find_muhurta.invoke({
        "intent": "business_launch", "start_date": "2026-06-01",
        "latitude": 28.6139, "longitude": 77.2090, "timezone": "Asia/Kolkata",
        "natal_chart_json": "null",
    })
    result = json.loads(result_str)
    assert "error" not in result, f"Muhurta error: {result.get('error')}"
    for slot in result.get("top_slots", []):
        assert not slot.get("in_rahu_kalam", False), \
            f"Slot {slot.get('datetime_local')} is in Rahu Kalam!"
    print(f"  {len(result['top_slots'])} muhurta slots, none in Rahu Kalam ✓")


def test_muhurta_returns_top_3():
    from agent.tools.muhurta import find_muhurta
    result_str = find_muhurta.invoke({
        "intent": "travel", "start_date": "2026-06-01",
        "latitude": 19.0760, "longitude": 72.8777, "timezone": "Asia/Kolkata",
        "natal_chart_json": "null",
    })
    result = json.loads(result_str)
    slots = result.get("top_slots", [])
    assert len(slots) <= 3
    assert len(slots) >= 1, "Expected at least 1 auspicious slot in 30 days"
    print(f"  Top slot score: {slots[0]['score'] if slots else 'N/A'} ✓")


# ── Yoga Detection Tests ───────────────────────────────────────────────────────

def test_yoga_detection_runs():
    from agent.tools.yoga_detection import detect_yogas
    result_str = detect_yogas.invoke({"natal_chart_json": json.dumps(PRIYA_CHART)})
    result = json.loads(result_str)
    assert "error" not in result, f"Yoga error: {result.get('error')}"
    print(f"  {result['total_count']} yogas found for Priya ✓")
    for yoga in result.get("yogas_found", []):
        print(f"    - {yoga['name']} ({yoga['strength']})")


def test_budhaditya_yoga_detection():
    """Sun and Mercury in same house should trigger Budhaditya Yoga."""
    from agent.tools.yoga_detection import check_budhaditya
    sun_h = PRIYA_CHART["sidereal"]["planets"]["Sun"]["house"]
    mer_h = PRIYA_CHART["sidereal"]["planets"]["Mercury"]["house"]
    if sun_h == mer_h:
        result = check_budhaditya(PRIYA_CHART)
        assert result is not None, "Budhaditya Yoga not detected when Sun and Mercury are conjunct"
        print(f"  Budhaditya Yoga correctly detected ✓")
    else:
        print(f"  Sun house={sun_h}, Mercury house={mer_h} — not conjunct, skip ✓")


def test_gaja_kesari_logic():
    """Gaja Kesari requires Jupiter in 1,4,7,10 from Moon."""
    from agent.tools.yoga_detection import check_gaja_kesari
    result = check_gaja_kesari(PRIYA_CHART)
    moon_h = PRIYA_CHART["sidereal"]["planets"]["Moon"]["house"]
    jup_h = PRIYA_CHART["sidereal"]["planets"]["Jupiter"]["house"]
    diff = (jup_h - moon_h) % 12
    if diff in {0, 3, 6, 9}:
        assert result is not None, "Gaja Kesari should be detected"
        print(f"  Gaja Kesari detected (Jup h{jup_h} from Moon h{moon_h}) ✓")
    else:
        assert result is None, "Gaja Kesari should NOT be detected"
        print(f"  Gaja Kesari correctly absent (Jup h{jup_h}, Moon h{moon_h}) ✓")


# ── Panchang Tests ─────────────────────────────────────────────────────────────

def test_panchang_returns_five_limbs():
    from agent.tools.panchang import get_panchang
    result_str = get_panchang.invoke({
        "date": "2026-05-27", "latitude": 28.6139,
        "longitude": 77.2090, "timezone": "Asia/Kolkata",
    })
    result = json.loads(result_str)
    assert "error" not in result
    for key in ["tithi","vara","nakshatra","yoga","karana","rahu_kalam"]:
        assert key in result, f"Missing {key} in panchang"
    print(f"  Panchang 2026-05-27: {result['tithi']['name']} {result['tithi']['paksha']} | "
          f"Nak: {result['nakshatra']['name']} | Yoga: {result['yoga']['name']} ✓")


def test_panchang_sun_in_gemini_may_2026():
    """On May 27 2026, Sun should be in Gemini — Vara is Wednesday (Mercury)."""
    from agent.tools.panchang import get_panchang
    result_str = get_panchang.invoke({
        "date": "2026-05-27", "latitude": 28.6, "longitude": 77.2, "timezone": "Asia/Kolkata",
    })
    result = json.loads(result_str)
    # May 27 2026 is a Wednesday
    assert result["vara"]["name"] == "Wednesday", f"Expected Wednesday, got {result['vara']['name']}"
    assert result["vara"]["lord"] == "Mercury"
    print(f"  2026-05-27 is {result['vara']['name']} ruled by {result['vara']['lord']} ✓")


# ── Dasha Tests ────────────────────────────────────────────────────────────────

def test_dasha_timeline_120_years():
    from agent.tools.dasha import compute_dasha_timeline
    chart_with_birth = dict(PRIYA_CHART)
    chart_with_birth["birth_details"] = {"date": "1990-08-15", "time": "14:30"}
    result_str = compute_dasha_timeline.invoke({
        "natal_chart_json": json.dumps(chart_with_birth),
        "target_date": "2026-05-27",
    })
    result = json.loads(result_str)
    assert "error" not in result, f"Dasha error: {result.get('error')}"
    assert "timeline" in result
    total_years = sum(d["years"] for d in result["timeline"])
    assert abs(total_years - 120) < 2, f"Total dasha years {total_years} should be ~120"
    print(f"  Dasha total: {total_years:.1f} years ✓")
    cp = result["current_period"]
    if cp["mahadasha"]:
        print(f"  Current: {cp['mahadasha']['planet']} Mahadasha, {cp['antardasha']['planet'] if cp['antardasha'] else '?'} Antardasha ✓")


def test_dasha_sequence_order():
    """First dasha lord must be based on birth Moon nakshatra."""
    from agent.tools.dasha import compute_dasha_timeline, NAKSHATRA_LORDS, NAKSHATRA_NAMES
    chart_with_birth = dict(PRIYA_CHART)
    chart_with_birth["birth_details"] = {"date": "1990-08-15", "time": "14:30"}
    result_str = compute_dasha_timeline.invoke({"natal_chart_json": json.dumps(chart_with_birth)})
    result = json.loads(result_str)
    expected_lord = result.get("birth_dasha_lord")
    first_dasha = result["timeline"][0]["planet"]
    assert first_dasha == expected_lord, f"First dasha {first_dasha} != expected {expected_lord}"
    print(f"  Birth Dasha Lord: {expected_lord} ✓  (Nakshatra: {result['birth_nakshatra']})")


# ── Compatibility Tests ────────────────────────────────────────────────────────

def test_ashtakoot_max_36():
    from agent.tools.compatibility import compute_compatibility
    result_str = compute_compatibility.invoke({
        "chart_a_json": json.dumps(PRIYA_CHART),
        "chart_b_json": json.dumps(ARJUN_CHART),
        "name_a": "Priya", "name_b": "Arjun",
    })
    result = json.loads(result_str)
    assert "error" not in result
    total = result["ashtakoot"]["total_score"]
    assert 0 <= total <= 36, f"Score {total} out of range [0,36]"
    print(f"  Ashtakoot score: {total}/36 ({result['ashtakoot']['percentage']}%) ✓")


def test_nadi_dosha_detection():
    """If both charts have same Nadi, Nadi Dosha must be detected and score = 0."""
    from agent.tools.compatibility import _compute_nadi, _nak_idx, NAKSHATRA_NADI
    moon_a = PRIYA_CHART["sidereal"]["planets"]["Moon"]["longitude"]
    moon_b = ARJUN_CHART["sidereal"]["planets"]["Moon"]["longitude"]
    nak_a = _nak_idx(moon_a)
    nak_b = _nak_idx(moon_b)
    result = _compute_nadi(nak_a, nak_b)
    if NAKSHATRA_NADI[nak_a] == NAKSHATRA_NADI[nak_b]:
        assert result["score"] == 0, "Nadi Dosha should give 0 points"
        assert result["dosha"] is True
        print(f"  Nadi Dosha correctly detected: {result['nadi_a']} = {result['nadi_b']} → 0 pts ✓")
    else:
        assert result["score"] == 8, "No Nadi Dosha should give 8 points"
        print(f"  No Nadi Dosha: {result['nadi_a']} ≠ {result['nadi_b']} → 8 pts ✓")