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
        step_count = 0

        try:
            async for chunk in GRAPH.astream(
                input=initial_state,
                stream_mode="values",  # streams full state after each node
            ):
                # Extract the latest message from state
                messages = chunk.get("messages", [])
                if not messages:
                    continue

                last_msg = messages[-1]

                # Check for intent update
                if chunk.get("intent"):
                    final_intent = chunk["intent"]
                if chunk.get("step_count"):
                    step_count = chunk["step_count"]

                # Yield tool start events
                from langchain_core.messages import AIMessage as _AIMessage, ToolMessage as _ToolMessage
                if isinstance(last_msg, _AIMessage) and last_msg.tool_calls:
                    for tc in last_msg.tool_calls:
                        tool_name = tc.get("name", "unknown_tool")
                        if tool_name not in tool_calls_made:
                            tool_calls_made.append(tool_name)
                            yield {
                                "event": "tool_start",
                                "data": json.dumps({
                                    "tool": tool_name,
                                    "step": step_count,
                                }),
                            }

                # Yield token events (final AI response, not tool calls)
                if isinstance(last_msg, _AIMessage) and not last_msg.tool_calls:
                    content = last_msg.content if isinstance(last_msg.content, str) else ""
                    if content:
                        # Yield incrementally if this is new content
                        existing = "".join(full_response_tokens)
                        new_content = content[len(existing):]
                        if new_content:
                            full_response_tokens.append(new_content)
                            yield {
                                "event": "token",
                                "data": json.dumps({"text": new_content}),
                            }

                # Tool end events
                if isinstance(last_msg, _ToolMessage):
                    yield {
                        "event": "tool_end",
                        "data": json.dumps({
                            "tool": last_msg.name,
                            "status": "done",
                        }),
                    }

        except Exception as e:
            yield {"event": "error", "data": json.dumps({"message": str(e)})}

        full_response = "".join(full_response_tokens)

        if full_response:
            await crud.add_message(
                db, request.session_id, "assistant", full_response,
                tool_calls=tool_calls_made if tool_calls_made else None,
            )

        yield {
            "event": "done",
            "data": json.dumps({
                "total_tokens": 0,
                "tool_calls": tool_calls_made,
                "latency_ms": round((time.time() - initial_state["_latency_start"]) * 1000),
                "step_count": step_count,
                "intent": final_intent,
            }),
        }

    return EventSourceResponse(event_generator())