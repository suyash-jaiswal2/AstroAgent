import json

try:
    with open('eval/results/run_2026-05-30_0212.json') as f:
        d = json.load(f)
    for c in d:
        if not c['passed']:
            print(f"{c['id']} - Error: {c.get('error')}")
            print(f"Tools: {c['tool_calls']}")
            print(f"Checks: {c['deterministic']}")
            print(f"Judge: {c['llm_judge']['avg_score']} - Scores: {c['llm_judge'].get('scores', {})}")
            print("---")
except Exception as e:
    print(f"Error: {e}")
