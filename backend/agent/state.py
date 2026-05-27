from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from dataclasses import dataclass, field


@dataclass
class BirthDetails:
    name: str
    date: str             # ISO format: "1990-08-15"
    time: str | None      # "14:30" or None if unknown
    place: str            # Raw user input: "Mumbai, India"
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None    # "Asia/Kolkata"
    time_unknown: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name, "date": self.date, "time": self.time,
            "place": self.place, "latitude": self.latitude,
            "longitude": self.longitude, "timezone": self.timezone,
            "time_unknown": self.time_unknown,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BirthDetails":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def summary(self) -> str:
        t = self.time if self.time else "time unknown"
        return f"{self.name}, born {self.date} at {t}, {self.place}"


@dataclass
class NatalChart:
    planets: dict          # {"Sun": {"sign": "Leo", "degree": 14.3, "house": 9, "retrograde": False}}
    houses: dict           # {"1": {"sign": "Sagittarius", "cusp_degree": 0.0}}
    ascendant: dict        # {"sign": "Sagittarius", "degree": 5.12}
    tropical: dict         # Full tropical (Western) chart
    sidereal: dict         # Full sidereal (Vedic) chart — Lahiri ayanamsa
    birth_details: BirthDetails
    computed_at: str       # ISO timestamp

    def to_dict(self) -> dict:
        d = {
            "planets": self.planets, "houses": self.houses,
            "ascendant": self.ascendant, "tropical": self.tropical,
            "sidereal": self.sidereal, "computed_at": self.computed_at,
            "birth_details": self.birth_details.to_dict(),
        }
        return d

    def summary(self) -> str:
        sun = self.tropical.get("planets", {}).get("Sun", {})
        moon = self.tropical.get("planets", {}).get("Moon", {})
        asc = self.tropical.get("ascendant", {})
        return (f"Sun in {sun.get('sign','?')}, Moon in {moon.get('sign','?')}, "
                f"Ascendant {asc.get('sign','?')}")


class AstroAgentState(TypedDict):
    # Core conversation
    messages: Annotated[list[AnyMessage], add_messages]
    session_id: str

    # User profile
    birth_details: BirthDetails | None
    natal_chart: NatalChart | None     # Cached after first compute

    # Routing
    intent: Literal[
        "chart_request", "daily_horoscope", "muhurta_request",
        "compatibility_request", "yoga_query", "panchang_request",
        "dasha_query", "free_form", "off_topic", "safety_block"
    ]

    # Loop control
    step_count: int
    tool_calls_made: list[str]
    max_steps: int           # Default 8

    # Eval metadata (stripped before sending to client)
    _latency_start: float
    _token_log: dict
    _eval_mode: bool