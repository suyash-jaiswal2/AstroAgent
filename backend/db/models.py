from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from .database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    birth_details_json = Column(Text, nullable=True)   # JSON blob
    natal_chart_json = Column(Text, nullable=True)     # JSON blob — cached forever

    messages = relationship("Message", back_populates="session",
                            cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"))
    role = Column(String)          # "user" | "assistant" | "tool"
    content = Column(Text)
    tool_calls_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="messages")


class CachedGeocode(Base):
    __tablename__ = "cached_geocodes"

    place_name = Column(String, primary_key=True)
    result_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)