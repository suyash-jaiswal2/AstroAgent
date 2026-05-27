"""
AstroAgent Tool Registry
All tools imported here. ALL_TOOLS is consumed by:
  - agent/nodes.py (reasoning_node binds tools to the LLM)
  - agent/graph.py (ToolNode executes tools)
"""

from .geocode import geocode_place
from .birth_chart import compute_birth_chart
from .daily_transits import get_daily_transits
from .knowledge_lookup import knowledge_lookup

# Innovative feature tools — uncommented as implemented in Steps 41–60
# from .muhurta import find_muhurta
# from .compatibility import compute_compatibility
# from .yoga_detection import detect_yogas
# from .panchang import get_panchang
# from .dasha import compute_dasha_timeline

ALL_TOOLS = [
    geocode_place,
    compute_birth_chart,
    get_daily_transits,
    knowledge_lookup,
    # find_muhurta,
    # compute_compatibility,
    # detect_yogas,
    # get_panchang,
    # compute_dasha_timeline,
]

__all__ = ["ALL_TOOLS"]