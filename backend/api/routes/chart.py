import json
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db import crud

router = APIRouter(tags=["chart"])


class MuhurtaRequest(BaseModel):
    session_id: str
    intent: str
    start_date: str


class CompatibilityRequest(BaseModel):
    session_id: str
    partner_name: str
    partner_date: str
    partner_time: str | None = None
    partner_place: str


@router.get("/panchang")
async def get_panchang_endpoint(
    date: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...),
    tz: str = Query(...),
):
    try:
        from agent.tools.panchang import get_panchang
        result_str = get_panchang.invoke({"date": date, "latitude": lat, "longitude": lon, "timezone": tz})
        return json.loads(result_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/muhurta")
async def find_muhurta_endpoint(body: MuhurtaRequest, db: AsyncSession = Depends(get_db)):
    session = await crud.get_session(db, body.session_id)
    if not session or not session.natal_chart_json:
        raise HTTPException(status_code=400, detail="Natal chart not computed yet")

    natal_chart = json.loads(session.natal_chart_json)
    birth_details = json.loads(session.birth_details_json) if session.birth_details_json else {}

    try:
        from agent.tools.muhurta import find_muhurta
        result_str = find_muhurta.invoke({
            "intent": body.intent,
            "start_date": body.start_date,
            "latitude": birth_details.get("latitude", 28.6),
            "longitude": birth_details.get("longitude", 77.2),
            "timezone": birth_details.get("timezone", "Asia/Kolkata"),
            "natal_chart_json": json.dumps(natal_chart),
        })
        return json.loads(result_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/dashas")
async def get_dashas(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await crud.get_session(db, session_id)
    if not session or not session.natal_chart_json:
        raise HTTPException(status_code=404, detail="Natal chart not found")
    try:
        from agent.tools.dasha import compute_dasha_timeline
        result_str = compute_dasha_timeline.invoke({"natal_chart_json": session.natal_chart_json})
        return json.loads(result_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/yogas")
async def get_yogas(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await crud.get_session(db, session_id)
    if not session or not session.natal_chart_json:
        raise HTTPException(status_code=404, detail="Natal chart not found")
    try:
        from agent.tools.yoga_detection import detect_yogas
        result_str = detect_yogas.invoke({"natal_chart_json": session.natal_chart_json})
        return json.loads(result_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))