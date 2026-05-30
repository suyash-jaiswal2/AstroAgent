"""
chat.py — SSE streaming endpoint using LangGraph astream_events
for real token-by-token streaming.
"""
import json
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
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

    print("DEBUG: session birth_details_json raw:", session.birth_details_json)
    print("DEBUG: loaded session_data['birth_details']:", session_data["birth_details"])

    initial_state = _build_initial_state(request, session_data)
    latency_start = initial_state["_latency_start"]

    print("DEBUG: initial_state['birth_details']:", initial_state.get("birth_details"))

    # Persist user message
    await crud.add_message(db, request.session_id, "user", request.message)

    async def event_generator() -> AsyncGenerator[dict, None]:
        all_tokens: list[str] = []
        tool_calls_made: list[str] = []
        final_intent = "free_form"
        new_natal_chart: dict | None = session_data.get("natal_chart")
        final_step_count = 0

        try:
            async for event in GRAPH.astream_events(
                input=initial_state,
                version="v2",
            ):
                kind = event.get("event", "")

                # ── Token streaming ────────────────────────────────────────────
                if kind == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    if chunk and hasattr(chunk, "content"):
                        text = chunk.content
                        if isinstance(text, str) and text:
                            all_tokens.append(text)
                            yield {
                                "event": "token",
                                "data": json.dumps({"text": text}),
                            }
                        elif isinstance(text, list):
                            for part in text:
                                if isinstance(part, dict) and part.get("type") == "text":
                                    t = part.get("text", "")
                                    if t:
                                        all_tokens.append(t)
                                        yield {
                                            "event": "token",
                                            "data": json.dumps({"text": t}),
                                        }

                # ── Tool start ────────────────────────────────────────────────
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown_tool")
                    if tool_name not in tool_calls_made:
                        tool_calls_made.append(tool_name)
                    yield {
                        "event": "tool_start",
                        "data": json.dumps({"tool": tool_name, "step": len(tool_calls_made)}),
                    }

                # ── Tool end ──────────────────────────────────────────────────
                elif kind == "on_tool_end":
                    tool_name = event.get("name", "")
                    tool_output = event["data"].get("output", "")

                    # Auto-save natal chart when compute_birth_chart completes
                    if tool_name == "compute_birth_chart" and isinstance(tool_output, str):
                        try:
                            chart_data = json.loads(tool_output)
                            if "tropical" in chart_data and "error" not in chart_data:
                                new_natal_chart = chart_data
                        except Exception:
                            pass

                    yield {
                        "event": "tool_end",
                        "data": json.dumps({"tool": tool_name, "status": "done"}),
                    }

                # ── Final chain end ───────────────────────────────────────────
                elif kind == "on_chain_end" and event.get("name") == "LangGraph":
                    output = event.get("data", {}).get("output", {})
                    final_intent = output.get("intent", "free_form")
                    final_step_count = output.get("step_count", 0)
                    # Pick up natal chart from state if reasoning node cached it
                    if not new_natal_chart and output.get("natal_chart"):
                        new_natal_chart = output["natal_chart"]
                    # Capture non-streamed final AIMessage content
                    # (e.g. from format_error_node which bypasses LLM streaming)
                    final_messages = output.get("messages", [])
                    if final_messages and not all_tokens:
                        last_msg = final_messages[-1]
                        if hasattr(last_msg, "content") and isinstance(last_msg.content, str) and last_msg.content:
                            all_tokens.append(last_msg.content)
                            yield {
                                "event": "token",
                                "data": json.dumps({"text": last_msg.content}),
                            }

        except Exception as e:
            import traceback
            print("ERROR in chat_stream event generator:")
            traceback.print_exc()
            yield {"event": "error", "data": json.dumps({"message": str(e)})}

        # ── Post-stream persistence ────────────────────────────────────────────
        full_response = "".join(all_tokens)

        if full_response.strip():
            await crud.add_message(
                db, request.session_id, "assistant", full_response,
                tool_calls=tool_calls_made if tool_calls_made else None,
            )

        # Save natal chart to SQLite (cached forever)
        if new_natal_chart and not session_data.get("natal_chart"):
            await crud.update_session_natal_chart(db, request.session_id, new_natal_chart)

        yield {
            "event": "done",
            "data": json.dumps({
                "total_tokens": len("".join(all_tokens).split()),
                "tool_calls": tool_calls_made,
                "latency_ms": round((time.time() - latency_start) * 1000),
                "intent": final_intent,
                "step_count": final_step_count,
                "natal_chart": new_natal_chart,
            }),
        }

    return EventSourceResponse(event_generator())