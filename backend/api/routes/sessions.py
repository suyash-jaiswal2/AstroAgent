import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db import crud

router = APIRouter(tags=["sessions"])


class BirthDetailsRequest(BaseModel):
    name: str
    date: str
    time: str | None = None
    place: str
    time_unknown: bool = False


@router.post("/sessions")
async def create_session(db: AsyncSession = Depends(get_db)):
    session = await crud.create_session(db)
    return {"session_id": session.id, "created_at": session.created_at.isoformat()}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await crud.get_messages(db, session_id)
    birth_details = json.loads(session.birth_details_json) if session.birth_details_json else None
    natal_chart = json.loads(session.natal_chart_json) if session.natal_chart_json else None

    return {
        "session_id": session.id,
        "created_at": session.created_at.isoformat(),
        "birth_details": birth_details,
        "natal_chart": natal_chart,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
                "tool_calls": json.loads(m.tool_calls_json) if m.tool_calls_json else None,
            }
            for m in messages
        ],
    }


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await crud.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/sessions/{session_id}/birth")
async def save_birth_details(
    session_id: str,
    body: BirthDetailsRequest,
    db: AsyncSession = Depends(get_db),
):
    from datetime import date as date_type, datetime

    # Validate: no future dates
    try:
        birth_date = datetime.strptime(body.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid date format or impossible date: {body.date}")

    if birth_date > date_type.today():
        raise HTTPException(status_code=422, detail="Birth date cannot be in the future.")
    if birth_date.year < 1800 or birth_date.year > 2020:
        raise HTTPException(
            status_code=422,
            detail=f"Birth year {birth_date.year} is outside the expected range (1800–2020)."
        )

    birth_dict = body.model_dump()
    session = await crud.update_session_birth_details(db, session_id, birth_dict)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"session_id": session_id, "birth_details": birth_dict}


@router.get("/sessions/{session_id}/chart")
async def get_chart(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.natal_chart_json:
        return {"session_id": session_id, "natal_chart": json.loads(session.natal_chart_json)}

    # Chart not yet computed — will be computed by the agent on first chart request
    return {"session_id": session_id, "natal_chart": None,
            "message": "Ask the agent about your chart to trigger computation."}