import json
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from .models import Session, Message, CachedGeocode


# ── Sessions ──────────────────────────────────────────────────────────────────

async def create_session(db: AsyncSession) -> Session:
    session = Session(id=str(uuid4()))
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: str) -> Session | None:
    result = await db.execute(select(Session).where(Session.id == session_id))
    return result.scalar_one_or_none()


async def delete_session(db: AsyncSession, session_id: str) -> bool:
    result = await db.execute(delete(Session).where(Session.id == session_id))
    await db.commit()
    return result.rowcount > 0


async def update_session_birth_details(db: AsyncSession, session_id: str,
                                        birth_details: dict) -> Session | None:
    session = await get_session(db, session_id)
    if not session:
        return None
    session.birth_details_json = json.dumps(birth_details)
    session.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)
    return session


async def update_session_natal_chart(db: AsyncSession, session_id: str,
                                      natal_chart: dict) -> Session | None:
    session = await get_session(db, session_id)
    if not session:
        return None
    session.natal_chart_json = json.dumps(natal_chart)
    session.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)
    return session


# ── Messages ──────────────────────────────────────────────────────────────────

async def add_message(db: AsyncSession, session_id: str, role: str,
                       content: str, tool_calls: list | None = None) -> Message:
    msg = Message(
        session_id=session_id,
        role=role,
        content=content,
        tool_calls_json=json.dumps(tool_calls) if tool_calls else None,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_messages(db: AsyncSession, session_id: str) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    return list(result.scalars().all())


# ── Geocode cache ─────────────────────────────────────────────────────────────

async def get_cached_geocode(db: AsyncSession, place_name: str) -> dict | None:
    result = await db.execute(
        select(CachedGeocode).where(CachedGeocode.place_name == place_name.lower().strip())
    )
    row = result.scalar_one_or_none()
    return json.loads(row.result_json) if row else None


async def save_geocode_cache(db: AsyncSession, place_name: str, result: dict) -> None:
    existing = await get_cached_geocode(db, place_name)
    if existing:
        return
    entry = CachedGeocode(
        place_name=place_name.lower().strip(),
        result_json=json.dumps(result),
    )
    db.add(entry)
    await db.commit()