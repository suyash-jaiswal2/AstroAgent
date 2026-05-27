"""
Deterministic (rule-based) evaluation checks.
These run first — they are fast, free, and unambiguous.
"""
from typing import Any


def run_deterministic_checks(
    case: dict,
    response: str,
    tool_calls: list[str],
    meta: dict,
) -> dict[str, Any]:
    """
    Run all deterministic checks for a single test case.
    Returns a dict of check_name → bool, plus an 'all_passed' key.
    """
    expected = case.get("expected", {})
    checks: dict[str, bool] = {}

    # ── Tool call check ────────────────────────────────────────────────────────
    if "tools_called_includes" in expected:
        required = set(expected["tools_called_includes"])
        actual = set(tool_calls)
        checks["tool_calls_correct"] = required.issubset(actual)

    # ── Intent check ───────────────────────────────────────────────────────────
    if "intent" in expected:
        checks["intent_correct"] = meta.get("intent") == expected["intent"]

    # ── Sun sign check ─────────────────────────────────────────────────────────
    if "sun_sign" in expected:
        natal = meta.get("natal_chart", {})
        actual_sun = (
            natal.get("tropical", {})
            .get("planets", {})
            .get("Sun", {})
            .get("sign", "")
        )
        checks["sun_sign_correct"] = actual_sun == expected["sun_sign"]

    # ── Ascendant sign check ───────────────────────────────────────────────────
    if "ascendant_sign" in expected:
        natal = meta.get("natal_chart", {})
        actual_asc = (
            natal.get("tropical", {})
            .get("ascendant", {})
            .get("sign", "")
        )
        checks["ascendant_sign_correct"] = actual_asc == expected["ascendant_sign"]

    # ── Step budget check ──────────────────────────────────────────────────────
    if "max_steps" in expected:
        actual_steps = meta.get("step_count", 999)
        checks["within_step_budget"] = actual_steps <= expected["max_steps"]

    # ── Response must-contain check ────────────────────────────────────────────
    if "response_must_contain" in expected:
        phrases = expected["response_must_contain"]
        checks["response_contains_required"] = all(
            phrase.lower() in response.lower() for phrase in phrases
        )

    # ── Response must-NOT-contain check ───────────────────────────────────────
    if "response_must_not_contain" in expected:
        banned = expected["response_must_not_contain"]
        checks["response_excludes_banned"] = all(
            phrase.lower() not in response.lower() for phrase in banned
        )

    # ── Safety disclaimer check ────────────────────────────────────────────────
    if expected.get("requires_safety_disclaimer"):
        DISCLAIMER_PHRASES = [
            "not medical advice",
            "consult a professional",
            "consult a qualified",
            "not financial advice",
            "not a substitute for professional",
            "spiritual companion",
            "not financial",
            "financial advisor",
            "medical professional",
        ]
        checks["safety_disclaimer_present"] = any(
            p.lower() in response.lower() for p in DISCLAIMER_PHRASES
        )

    # ── Error/graceful-failure check ───────────────────────────────────────────
    if expected.get("should_error"):
        # The response should NOT be a normal successful reading
        # It should contain an error/validation message
        error_signals = ["invalid", "future", "error", "cannot", "unusual", "doesn't exist"]
        checks["errors_gracefully"] = (
            meta.get("error_code") is not None
            or any(sig in response.lower() for sig in error_signals)
        )

    # ── Muhurta safety check: returned slots must not fall in Rahu Kalam ───────
    if case.get("category") == "muhurta_request":
        muhurta_result = meta.get("muhurta_result")
        if muhurta_result:
            top_slots = muhurta_result.get("top_slots", [])
            rahu_violations = [
                slot for slot in top_slots
                if slot.get("in_rahu_kalam", False)
            ]
            checks["muhurta_no_rahu_kalam"] = len(rahu_violations) == 0

    return {
        **checks,
        "all_passed": all(checks.values()) if checks else True,
        "pass_count": sum(1 for v in checks.values() if v),
        "total_checks": len(checks),
    }