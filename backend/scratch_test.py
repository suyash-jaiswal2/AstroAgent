import asyncio
import json
from agent.graph import GRAPH
from agent.state import BirthDetails
from langchain_core.messages import HumanMessage

async def main():
    bd = BirthDetails(
        name="Priya",
        date="1990-08-15",
        time="14:30",
        place="New Delhi, India"
    )
    
    state = {
        "messages": [HumanMessage(content="What does my chart say about my career?")],
        "session_id": "test_session_123",
        "birth_details": bd,
        "natal_chart": None,
        "intent": "chart_request",
        "step_count": 0,
        "tool_calls_made": [],
        "max_steps": 8,
        "_latency_start": 0,
        "_token_log": {},
        "_eval_mode": True
    }
    
    # We will modify nodes.py to print the system prompt or we can print it from the runner
    print("--- STARTING GRAPH EXECUTION ---")
    async for event in GRAPH.astream_events(state, version="v2"):
        kind = event.get("event")
        name = event.get("name")
        if kind == "on_chat_model_stream":
            chunk = event["data"].get("chunk")
            if chunk and hasattr(chunk, "content"):
                print(chunk.content, end="", flush=True)
        elif kind == "on_tool_start":
            print(f"\n[TOOL START: {name}]")
        elif kind == "on_tool_end":
            print(f"\n[TOOL END: {name}]")
        elif kind == "on_chain_end" and name == "LangGraph":
            print("\n--- GRAPH DONE ---")
            output = event["data"].get("output", {})
            print("Final Step Count:", output.get("step_count"))
            print("Final Intent:", output.get("intent"))
            print("Final Natal Chart:", "Present" if output.get("natal_chart") else "None")
            print("\nMessages in final state:")
            for i, msg in enumerate(output.get("messages", [])):
                role = msg.__class__.__name__
                content = msg.content
                tool_calls = getattr(msg, "tool_calls", None)
                print(f"\n[{i}] {role}: {content[:200]}")
                if tool_calls:
                    print(f"    Tool Calls: {tool_calls}")

if __name__ == "__main__":
    asyncio.run(main())
