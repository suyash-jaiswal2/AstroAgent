"""
Unit tests for the four core tools.
Run: pytest backend/tests/test_tools.py -v
"""
import json
import asyncio
import os
import sys
from pathlib import Path

# Ensure backend/ is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("ANTHROPIC_API_KEY", "test")

import pytest


# ── Geocode tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_geocode_new_delhi():
    from agent.tools.geocode import _geocode_impl
    result = await _geocode_impl("New Delhi, India")
    assert "latitude" in result
    assert "longitude" in result
    assert "timezone" in result
    assert result["timezone"] == "Asia/Kolkata"
    assert 28.0 < result["latitude"] < 29.0   # New Delhi lat ~28.6
    assert 76.0 < result["longitude"] < 78.0  # New Delhi lon ~77.2
    print(f"  New Delhi: lat={result['latitude']}, lon={result['longitude']}, tz={result['timezone']}")


@pytest.mark.asyncio
async def test_geocode_unknown_place():
    from agent.tools.geocode import geocode_place
    result_str = await geocode_place.ainvoke({"place_name": "XyzNonExistentPlace12345"})
    result = json.loads(result_str)
    assert "error" in result
    print(f"  Unknown place correctly returned error: {result['error'][:50]}")


# ── Birth chart tests ──────────────────────────────────────────────────────────

def test_birth_chart_1990_new_delhi():
    """
    Reference chart: 1990-08-15 14:30 IST New Delhi
    Verified against pyswisseph + lunar eclipse back-calculation:
      Sun: Leo ~22.3°
      Moon: Gemini ~15.0°  (Moon was ~24 days past the July 22 1990 solar eclipse)
      Ascendant: Sagittarius ~14.0°
    Tolerance: ±0.5° for Sun/Moon, ±1.0° for Ascendant
    """
    from agent.tools.birth_chart import _compute_chart

    result = _compute_chart(
        date="1990-08-15",
        time="14:30",
        latitude=28.6139,
        longitude=77.2090,
        timezone="Asia/Kolkata",
    )

    sun = result["tropical"]["planets"]["Sun"]
    moon = result["tropical"]["planets"]["Moon"]
    asc = result["tropical"]["ascendant"]

    print(f"\n  Sun: {sun['sign']} {sun['degree']:.2f}°  (expected: Leo ~22.3°)")
    print(f"  Moon: {moon['sign']} {moon['degree']:.2f}°  (expected: Gemini ~15.0°)")
    print(f"  ASC: {asc['sign']} {asc['degree']:.2f}°  (expected: Sagittarius ~14.0°)")

    assert sun["sign"] == "Leo", f"Sun should be Leo, got {sun['sign']}"
    assert abs(sun["degree"] - 22.3) < 0.5, f"Sun degree {sun['degree']:.2f}° too far from 22.3°"
    assert moon["sign"] == "Gemini", f"Moon should be Gemini, got {moon['sign']}"
    assert abs(moon["degree"] - 15.0) < 0.5, f"Moon degree {moon['degree']:.2f}° too far from 15.0°"
    assert asc["sign"] == "Sagittarius", f"ASC should be Sagittarius, got {asc['sign']}"
    assert abs(asc["degree"] - 14.0) < 1.0, f"ASC degree {asc['degree']:.2f}° too far from 14.0°"


def test_birth_chart_time_unknown():
    """When time is None, chart should use 12:00 and flag time_unknown."""
    from agent.tools.birth_chart import _compute_chart

    result = _compute_chart(
        date="1990-08-15",
        time=None,
        latitude=28.6139,
        longitude=77.2090,
        timezone="Asia/Kolkata",
    )

    assert result["meta"]["time_unknown"] is True
    assert result["meta"]["time_unknown_note"] is not None
    assert result["tropical"]["planets"]["Sun"]["sign"] == "Leo"
    print(f"  Time unknown chart: Sun={result['tropical']['planets']['Sun']['sign']}, flagged correctly")


def test_birth_chart_ketu_is_rahu_plus_180():
    """Ketu longitude must equal Rahu longitude + 180° (mod 360)."""
    from agent.tools.birth_chart import _compute_chart

    result = _compute_chart(
        date="1990-08-15", time="14:30",
        latitude=28.6139, longitude=77.2090, timezone="Asia/Kolkata",
    )

    rahu = result["tropical"]["planets"]["Rahu"]["longitude"]
    ketu = result["tropical"]["planets"]["Ketu"]["longitude"]
    expected_ketu = (rahu + 180) % 360

    assert abs(ketu - expected_ketu) < 0.001, \
        f"Ketu {ketu:.4f}° != Rahu + 180° = {expected_ketu:.4f}°"
    print(f"  Rahu={rahu:.2f}°, Ketu={ketu:.2f}° ✓")


def test_birth_chart_second_reference():
    """Reference chart 2: 1995-06-15 10:00 IST Chennai. Sun should be Gemini."""
    from agent.tools.birth_chart import _compute_chart

    result = _compute_chart(
        date="1995-06-15", time="10:00",
        latitude=13.0827, longitude=80.2707, timezone="Asia/Kolkata",
    )
    sun = result["tropical"]["planets"]["Sun"]
    assert sun["sign"] == "Gemini", f"Expected Gemini, got {sun['sign']}"
    print(f"  1995-06-15 Chennai: Sun={sun['sign']} {sun['degree']:.2f}° ✓")


# ── Transits tests ─────────────────────────────────────────────────────────────

def test_transits_returns_sky_positions():
    from agent.tools.daily_transits import get_daily_transits
    result_str = get_daily_transits.invoke({"date": "2026-05-27", "natal_chart_json": "null"})
    result = json.loads(result_str)

    assert "current_sky" in result
    assert "Sun" in result["current_sky"]
    assert "Moon" in result["current_sky"]
    assert "moon_phase" in result
    print(f"  2026-05-27 sky: Sun={result['current_sky']['Sun']['sign']}, "
          f"Moon={result['current_sky']['Moon']['sign']}, Phase={result['moon_phase']}")


def test_transits_sun_in_gemini_may_2026():
    """On 2026-05-27, Sun should be in Gemini."""
    from agent.tools.daily_transits import get_daily_transits
    result_str = get_daily_transits.invoke({"date": "2026-05-27", "natal_chart_json": "null"})
    result = json.loads(result_str)
    assert result["current_sky"]["Sun"]["sign"] == "Gemini", \
        f"Sun on 2026-05-27 should be Gemini, got {result['current_sky']['Sun']['sign']}"
    print(f"  Sun on 2026-05-27: {result['current_sky']['Sun']['sign']} ✓")


# ── Knowledge lookup tests ─────────────────────────────────────────────────────

def test_knowledge_lookup_returns_results():
    from agent.tools.knowledge_lookup import knowledge_lookup
    result_str = knowledge_lookup.invoke({"query": "Jupiter in Sagittarius career meaning"})
    result = json.loads(result_str)

    if "error" in result:
        pytest.skip(f"ChromaDB not initialized: {result['error']}")

    assert "results" in result
    assert len(result["results"]) > 0
    assert result["results"][0]["relevance_score"] > 0.3
    print(f"  Top result: {result['results'][0]['source']} "
          f"(score={result['results'][0]['relevance_score']:.3f})")


def test_knowledge_lookup_yoga_query():
    from agent.tools.knowledge_lookup import knowledge_lookup
    result_str = knowledge_lookup.invoke({"query": "Gaja Kesari yoga Jupiter Moon"})
    result = json.loads(result_str)

    if "error" in result:
        pytest.skip("ChromaDB not initialized")

    sources = [r["source"] for r in result["results"]]
    print(f"  Gaja Kesari search sources: {sources}")
    # The gaja_kesari_yoga.md should be in top results
    assert any("yoga" in s.lower() for s in sources), \
        f"Expected yoga document in results, got: {sources}"