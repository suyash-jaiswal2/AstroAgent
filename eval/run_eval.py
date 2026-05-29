"""
AstroAgent Evaluation Runner
Usage:
    python eval/run_eval.py
    python eval/run_eval.py --category chart_request_valid
    python eval/run_eval.py --dry-run
"""
import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from graders.deterministic import run_deterministic_checks
from graders.llm_judge import run_llm_judge

BASE_URL = "http://localhost:8000"
VERSION = "1.0.0"


def load_cases(category: str | None = None) -> list[dict]:
    path = Path(__file__).parent / "golden_set.jsonl"
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if category:
        cases = [c for c in cases if c.get("category") == category]
    return cases


async def run_single_case(case: dict, client: httpx.AsyncClient) -> dict:
    start = time.time()
    tokens: list[str] = []
    tool_calls: list[str] = []
    final_meta: dict = {}
    error_msg: str | None = None

    try:
        # 1. Create session
        resp = await client.post("/api/sessions")
        resp.raise_for_status()
        session_id = resp.json()["session_id"]

        # 2. Set birth details if present
        bd = case["input"].get("birth_details")
        if bd:
            await client.post(f"/api/sessions/{session_id}/birth", json=bd)

        # 3. Stream chat response
        async with client.stream(
            "POST", "/api/chat/stream",
            json={"message": case["input"]["message"], "session_id": session_id},
            timeout=90.0,
        ) as response:
            buffer = ""
            async for chunk in response.aiter_bytes():
                buffer += chunk.decode("utf-8", errors="replace").replace("\r\n", "\n")
                while "\n\n" in buffer:
                    raw_event, buffer = buffer.split("\n\n", 1)
                    lines = raw_event.strip().splitlines()
                    event_type = ""
                    data_str = ""
                    for line in lines:
                        if line.startswith("event:"):
                            event_type = line.replace("event:", "").strip()
                        elif line.startswith("data:"):
                            data_str = line.replace("data:", "").strip()
                    if not event_type or not data_str:
                        continue
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    if event_type == "token":
                        tokens.append(data.get("text", ""))
                    elif event_type == "tool_start":
                        tool_calls.append(data.get("tool", ""))
                    elif event_type == "done":
                        final_meta = data
                    elif event_type == "error":
                        error_msg = data.get("message", "Unknown error")

    except Exception as e:
        error_msg = str(e)

    latency_ms = round((time.time() - start) * 1000)
    full_response = "".join(tokens)

    det_results = run_deterministic_checks(case, full_response, tool_calls, final_meta)
    judge_results = await run_llm_judge(case, full_response)

    passed = det_results["all_passed"] and judge_results["avg_score"] >= 3.0

    return {
        "id": case["id"],
        "category": case["category"],
        "latency_ms": latency_ms,
        "tool_calls": tool_calls,
        "full_response": full_response[:500] + "..." if len(full_response) > 500 else full_response,
        "deterministic": det_results,
        "llm_judge": judge_results,
        "tokens": final_meta.get("total_tokens", 0),
        "step_count": final_meta.get("step_count", 0),
        "error": error_msg,
        "passed": passed,
    }


def print_scorecard(results: list[dict]) -> None:
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    latencies = [r["latency_ms"] for r in results if r["latency_ms"] > 0]
    p50 = sorted(latencies)[len(latencies) // 2] if latencies else 0
    p95 = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0

    by_cat: dict = {}
    for r in results:
        cat = r["category"]
        by_cat.setdefault(cat, {"passed": 0, "total": 0})
        by_cat[cat]["total"] += 1
        if r["passed"]:
            by_cat[cat]["passed"] += 1

    print(f"\n{'='*68}")
    print(f"  ASTROAGENT EVALUATION SCORECARD  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  v{VERSION}")
    print(f"{'='*68}")
    print(f"  OVERALL: {passed}/{total} passed ({passed/total*100:.1f}%)")
    print(f"{'-'*68}")
    for cat, data in by_cat.items():
        bar = "#" * int(data["passed"] / data["total"] * 20)
        bar += "." * (20 - len(bar))
        print(f"  {cat[:32]:<32} {data['passed']:>2}/{data['total']:<2}  {bar}")
    print(f"{'-'*68}")
    print(f"  Latency p50: {p50}ms   p95: {p95}ms")
    print(f"  Failure rate: {(total-passed)/total*100:.1f}%")
    print(f"{'='*68}\n")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default=None)
    parser.add_argument("--case", default=None, help="Run a specific case ID (e.g. TC001)")
    parser.add_argument("--output", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cases = load_cases(args.category)
    if args.case:
        cases = [c for c in cases if c.get("id") == args.case]
    print(f"Loaded {len(cases)} test cases.")

    if args.dry_run:
        print("Dry run - validating golden set format only.")
        for c in cases:
            assert "id" in c and "input" in c and "expected" in c, f"Malformed case: {c.get('id')}"
        print("All cases valid. [OK]")
        return

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=90.0) as client:
        # Health check
        try:
            health = await client.get("/api/health")
            health.raise_for_status()
        except Exception:
            print("ERROR: Backend not running. Start it with: uvicorn api.main:app --reload --port 8000")
            sys.exit(1)

        print(f"Starting execution of {len(cases)} cases with concurrency limit = 3...")
        
        sem = asyncio.Semaphore(3)
        completed_count = 0

        async def run_with_sem(case):
            nonlocal completed_count
            async with sem:
                result = await run_single_case(case, client)
                completed_count += 1
                status = "PASS" if result["passed"] else "FAIL"
                print(f"[{completed_count}/{len(cases)}] Case {case['id']} - {status} ({result['latency_ms']}ms)")
                return result

        tasks = [run_with_sem(c) for c in cases]
        results = await asyncio.gather(*tasks)

    print_scorecard(results)

    output_path = args.output or f"eval/results/run_{datetime.now().strftime('%Y-%m-%d_%H%M')}.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())