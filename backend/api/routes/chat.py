"""
chat.py — REST JSON chat endpoint using LangGraph synchronous invoke.
Returns complete assistant response after execution.
"""
import json
import time

from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from agent.graph import GRAPH
from agent.state import AstroAgentState, BirthDetails
from db.database import get_db
from db import crud

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str


def _build_initial_state(request: ChatRequest, session_data: dict) -> AstroAgentState:
    birth_details = None
    natal_chart = None

    if session_data.get("birth_details"):
        try:
            bd = session_data["birth_details"]
            birth_details = BirthDetails(
                name=bd.get("name",""), date=bd.get("date",""),
                time=bd.get("time"), place=bd.get("place",""),
                latitude=bd.get("latitude"), longitude=bd.get("longitude"),
                timezone=bd.get("timezone"), time_unknown=bd.get("time_unknown", False),
            )
        except Exception:
            pass

    if session_data.get("natal_chart"):
        natal_chart = session_data["natal_chart"]

    return {
        "messages": [HumanMessage(content=request.message)],
        "session_id": request.session_id,
        "birth_details": birth_details,
        "natal_chart": natal_chart,
        "intent": "free_form",
        "step_count": 0,
        "tool_calls_made": [],
        "max_steps": 8,
        "_latency_start": time.time(),
        "_token_log": {},
        "_eval_mode": False,
    }


@router.get("/chat/stream")
async def chat_stream_get(
    message: str,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    request = ChatRequest(message=message, session_id=session_id)
    return await chat_stream(request, db)


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    # Ensure session exists
    session = await crud.get_session(db, request.session_id)
    if not session:
        from db.models import Session as DbSession
        session = DbSession(id=request.session_id)
        db.add(session)
        await db.commit()
        await db.refresh(session)

    session_data = {
        "birth_details": json.loads(session.birth_details_json) if session.birth_details_json else None,
        "natal_chart": json.loads(session.natal_chart_json) if session.natal_chart_json else None,
    }

    initial_state = _build_initial_state(request, session_data)
    latency_start = initial_state["_latency_start"]

    # Persist user message in SQLite
    await crud.add_message(db, request.session_id, "user", request.message)

    print(f"[CHAT REST] Starting GRAPH.ainvoke for session {request.session_id}...")
    
    # Run the state machine to completion!
    final_state = await GRAPH.ainvoke(initial_state)

    # Find the assistant's final response content
    assistant_message = ""
    messages = final_state.get("messages", [])
    for msg in reversed(messages):
        # Match AIMessage or role == assistant
        if msg.__class__.__name__ == "AIMessage" or getattr(msg, "role", None) == "assistant":
            assistant_message = msg.content
            break

    tool_calls_made = final_state.get("tool_calls_made", [])
    print(f"[CHAT REST] Invocation complete. Steps: {final_state.get('step_count')}, Tool calls: {tool_calls_made}")

    # Persist assistant message in SQLite
    if assistant_message.strip():
        await crud.add_message(
            db, request.session_id, "assistant", assistant_message,
            tool_calls=tool_calls_made if tool_calls_made else None,
        )

    # Update session natal chart if computed
    new_natal_chart = final_state.get("natal_chart")
    if new_natal_chart and not session_data.get("natal_chart"):
        await crud.update_session_natal_chart(db, request.session_id, new_natal_chart)

    return {
        "content": assistant_message,
        "tool_calls": tool_calls_made,
        "intent": final_state.get("intent", "free_form"),
        "step_count": final_state.get("step_count", 0),
        "natal_chart": new_natal_chart,
        "latency_ms": round((time.time() - latency_start) * 1000),
    }