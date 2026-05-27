from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .state import AstroAgentState
from .nodes import (
    precheck_node,
    intent_router_node,
    reasoning_node,
    response_formatter_node,
    format_error_node,
    route_after_precheck,
    route_after_reasoning,
)
from .tools import ALL_TOOLS


def build_graph():
    graph = StateGraph(AstroAgentState)

    # ── Add nodes ──────────────────────────────────────────────────────────────
    graph.add_node("precheck", precheck_node)
    graph.add_node("intent_router", intent_router_node)
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("tool_node", ToolNode(ALL_TOOLS))
    graph.add_node("response_formatter", response_formatter_node)
    graph.add_node("format_error", format_error_node)

    # ── Entry point ────────────────────────────────────────────────────────────
    graph.set_entry_point("precheck")

    # ── Edges ──────────────────────────────────────────────────────────────────
    graph.add_conditional_edges(
        "precheck",
        route_after_precheck,
        {"intent_router": "intent_router", "format_error": "format_error"},
    )
    graph.add_edge("intent_router", "reasoning")
    graph.add_conditional_edges(
        "reasoning",
        route_after_reasoning,
        {"tool_node": "tool_node", "response_formatter": "response_formatter"},
    )
    graph.add_edge("tool_node", "reasoning")
    graph.add_edge("response_formatter", END)
    graph.add_edge("format_error", END)

    return graph.compile()


# Singleton — imported by routes
GRAPH = build_graph()