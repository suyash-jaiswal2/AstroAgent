import json
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agent.graph import GRAPH
from agent.state import AstroAgentState, BirthDetails, NatalChart
from db.database import get_db
from db import crud

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str


def _build_initial_state(request: ChatRequest, session_data: dict) -> AstroAgentState:
    """Build the LangGraph state from request + persisted session data."""
    birth_details = None
    natal_chart = None

    if session_data.get("birth_details"):
        birth_details = BirthDetails.from_dict(session_data["birth_details"])

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
    session = await crud.get_session(db, request.session_id)
    if not session:
        session = await crud.create_session(db)

    session_data = {
        "birth_details": json.loads(session.birth_details_json) if session.birth_details_json else None,
        "natal_chart": json.loads(session.natal_chart_json) if session.natal_chart_json else None,
    }

    initial_state = _build_initial_state(request, session_data)

    # Persist user message
    await crud.add_message(db, request.session_id, "user", request.message)

    async def event_generator() -> AsyncGenerator[dict, None]:
        full_response_tokens: list[str] = []
        tool_calls_made: list[str] = []
        final_intent = "free_form"

        try:
            async for event_chunk in GRAPH.astream(
                input=initial_state,
                stream_mode="messages",
            ):
                # event_chunk is a tuple: (node_name, message_chunk)
                if not isinstance(event_chunk, tuple) or len(event_chunk) < 2:
                    continue

                node_name, message = event_chunk

                # Streaming tokens from reasoning node
                if node_name in ("reasoning", "response_formatter") and isinstance(message, AIMessage):
                    if isinstance(message.content, str) and message.content:
                        full_response_tokens.append(message.content)
                        yield {
                            "event": "token",
                            "data": json.dumps({"text": message.content}),
                        }

                # Tool start events
                elif node_name == "tool_node":
                    yield {
                        "event": "tool_start",
                        "data": json.dumps({"tool": str(node_name), "step": 0}),
                    }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}),
            }

        full_response = "".join(full_response_tokens)

        # Persist assistant response
        if full_response:
            await crud.add_message(db, request.session_id, "assistant", full_response,
                                   tool_calls=tool_calls_made if tool_calls_made else None)

        yield {
            "event": "done",
            "data": json.dumps({
                "total_tokens": 0,
                "tool_calls": tool_calls_made,
                "latency_ms": round((time.time() - initial_state["_latency_start"]) * 1000),
                "step_count": 0,
                "intent": final_intent,
            }),
        }

    return EventSourceResponse(event_generator())