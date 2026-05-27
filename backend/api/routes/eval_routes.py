from fastapi import APIRouter

router = APIRouter(tags=["eval"])


@router.post("/eval/run")
async def run_eval():
    # Stub — the real eval runner is a CLI script, not an HTTP endpoint.
    # This endpoint is for CI/CD integration only.
    return {"message": "Run eval via: python eval/run_eval.py"}