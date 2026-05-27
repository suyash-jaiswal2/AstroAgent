"""
LLM-as-judge using Google Gemini Flash (free tier: 1M tokens/day).
Scores responses on 4 dimensions: tone_warmth, astrological_accuracy,
helpfulness, conciseness.
"""
import json
import os
import re
import asyncio

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
_gemini = genai.GenerativeModel("gemini-2.0-flash")

JUDGE_RUBRIC = """You are evaluating an AI astrology assistant response. Score ONLY the dimension given below on a 1–5 scale.

Scoring dimensions:
- tone_warmth: Is the response warm, compassionate, and spiritually resonant? (1=robotic/cold, 5=deeply warm and wise)
- astrological_accuracy: Are astrological claims correct and consistent with chart data? (1=errors/hallucinations, 5=precise and well-grounded)
- helpfulness: Does it actually answer what the user asked? (1=deflects/ignores, 5=fully answers with actionable insight)
- conciseness: Appropriate length — not too verbose, not too brief? (1=very off, 5=perfectly sized)

Reference answer (if provided): {reference_answer}
User question: {question}
Assistant response: {response}

Dimension to score: {dimension}

Output EXACTLY this JSON and nothing else:
{{"dimension": "{dimension}", "score": <integer 1-5>, "reason": "<one sentence under 20 words>"}}"""


async def run_llm_judge(case: dict, response: str) -> dict:
    """Score a response on all specified llm_judge dimensions using Gemini Flash."""
    dimensions: list[str] = case.get("grading", {}).get("llm_judge", [])
    if not dimensions:
        return {"scores": {}, "avg_score": 0.0}

    scores: dict = {}

    for dim in dimensions:
        prompt = JUDGE_RUBRIC.format(
            reference_answer=case.get("reference_answer", "Not provided"),
            question=case["input"]["message"],
            response=response[:3000],  # Truncate to avoid token limits
            dimension=dim,
        )
        try:
            result = _gemini.generate_content(prompt)
            raw = result.text.strip()
            # Strip markdown fences
            raw = re.sub(r"```json|```", "", raw).strip()
            parsed = json.loads(raw)
            scores[dim] = {
                "score": int(parsed.get("score", 3)),
                "reason": parsed.get("reason", ""),
            }
        except Exception as e:
            scores[dim] = {"score": 3, "reason": f"Judge error: {str(e)[:50]}"}
        # Brief pause to respect Gemini rate limits
        await asyncio.sleep(0.5)

    avg = sum(s["score"] for s in scores.values()) / len(scores) if scores else 0.0
    return {"scores": scores, "avg_score": round(avg, 2)}