# Evaluation Report — AstroAgent

## Eval Architecture

**Golden set:** 30 test cases in `eval/golden_set.jsonl` written on Day 1 before any feature code.

**Grading has two layers:**
1. **Deterministic checks** (rule-based, free, fast): tool call correctness, intent classification, sun/ascendant sign accuracy, step budget, required/banned phrases, safety disclaimer presence.
2. **LLM-as-judge** (Gemini 2.0 Flash, free tier): tone warmth, astrological accuracy, helpfulness, conciseness — each scored 1–5.

**Pass threshold:** A case passes if all deterministic checks pass AND the LLM judge average ≥ 3.0/5.

---

## Scorecard History

| Date | Version | Overall | Chart Acc | Tool Acc | Warmth | Latency p50 | Cost/Run | Notes |
|------|---------|---------|-----------|----------|--------|-------------|----------|-------|
| [FILL IN] | v1.0.0 | [X]/30 ([X]%) | [X]% | [X]% | [X]/5 | [X]ms | $[X] | Initial run — baseline |
| [FILL IN] | v1.1.0 | [X]/30 ([X]%) | [X]% | [X]% | [X]/5 | [X]ms | $[X] | Fixed date validation + injection |
| [FILL IN] | v1.2.0 | [X]/30 ([X]%) | [X]% | [X]% | [X]/5 | [X]ms | $[X] | Final |

---

## Failures Discovered and Fixed

### v1.0 → v1.1

**Failure: TC008–TC010 (invalid birth dates)**
- Symptom: Server returned 500 instead of a structured validation error for future dates and year 1800.
- Root cause: `save_birth_details` endpoint didn't validate the year range.
- Fix: Added `year < 1800 or year > 2020` check in `api/routes/sessions.py`.

**Failure: TC027–TC028 (prompt injection)**
- Symptom: Injection patterns that didn't exactly match the original regex blocklist were not caught.
- Root cause: The initial regex list was too narrow.
- Fix: Extended `INJECTION_PATTERNS` in `nodes.py` with additional patterns (DAN, override, bypass, new persona).

### v1.1 → v1.2

[FILL IN with your actual v1.1 failures and fixes]

---

## Chart Math Validation

Cross-checked against Astro.com Natal Chart (Extended Chart Selection) for 3 reference charts.

| Chart | Planet | Expected | Actual | Tolerance | Pass |
|---|---|---|---|---|---|
| 1990-08-15 14:30 New Delhi | Sun (tropical) | Leo 22.8° | [FILL IN] | ≤0.5° | [✅/❌] |
| 1990-08-15 14:30 New Delhi | Moon (tropical) | Capricorn 4.2° | [FILL IN] | ≤0.5° | [✅/❌] |
| 1990-08-15 14:30 New Delhi | Ascendant | Sagittarius 7.1° | [FILL IN] | ≤1.0° | [✅/❌] |
| 1995-06-15 10:00 Chennai | Sun (tropical) | Gemini [X]° | [FILL IN] | ≤0.5° | [✅/❌] |
| 1985-07-10 08:00 Mumbai | Sun (tropical) | Cancer [X]° | [FILL IN] | ≤0.5° | [✅/❌] |

**Procedure:** Go to astro.com → Free Horoscopes → Extended Chart Selection → enter birth data → note positions under "Positions of Planets." Compare with `python tests/verify_swe.py` output.

---

## LLM Judge Spot-Check

After the v1.2 eval run, 10 judge verdicts were randomly selected and scored manually.

| Case | Dimension | Judge Score | Manual Score | Agreement (±1) |
|---|---|---|---|---|
| TC001 | tone_warmth | [X] | [X] | [✅/❌] |
| TC003 | astrological_accuracy | [X] | [X] | [✅/❌] |
| TC005 | helpfulness | [X] | [X] | [✅/❌] |
| TC011 | tone_warmth | [X] | [X] | [✅/❌] |
| TC015 | astrological_accuracy | [X] | [X] | [✅/❌] |
| TC019 | helpfulness | [X] | [X] | [✅/❌] |
| TC023 | conciseness | [X] | [X] | [✅/❌] |
| TC025 | tone_warmth | [X] | [X] | [✅/❌] |
| TC029 | helpfulness | [X] | [X] | [✅/❌] |
| TC030 | astrological_accuracy | [X] | [X] | [✅/❌] |

**Agreement rate: [X]/10 ([X]%)** — [meets/does not meet] the ≥80% target.

**Disagreement notes:** [FILL IN — explain any cases where judge and manual scores differed by more than 1 point]

---

## Cost Analysis

| Item | Tokens | Cost |
|---|---|---|
| Total API calls (7 days dev) | ~[X] | ~$[X] |
| Cost per eval run (30 cases) | ~[X] | ~$[X] |
| Cost per user conversation (avg) | ~[X] | ~$[X] |

Gemini 2.0 Flash (judge): $0.00 (free tier at 1M tokens/day, well within limits).

---

## What I Would Fix With More Time

1. **Full Shadbala strength scoring** for yoga detection — currently uses simplified dignity model.
2. **Nakshatra pada-level knowledge** — expand 27 nakshatra docs to 108 pada entries for richer RAG retrieval.
3. **Pratyantar Dasha** (sub-sub-period) — the 3rd level of Vimshottari.
4. **Secondary progressions** — Western predictive technique to complement Dasha.
5. **Muhurta sub-30-minute precision** — current 30-minute scanning could be 5-minute with parallel threads.
6. **Hindi language support** — Aradhana's Indian audience often prefers Hindi output.
7. **Partner chart sharing via URL** — currently both charts require manual entry for compatibility.