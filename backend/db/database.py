import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
default_db_path = BASE_DIR / "astroagent.db"
default_db_url = f"sqlite+aiosqlite:///{default_db_path.as_posix()}"

DATABASE_URL = os.getenv("DATABASE_URL", default_db_url)

print(f"DATABASE_URL is set to: {DATABASE_URL}")

# Parse database path if using SQLite and automatically create parent directories
if DATABASE_URL.startswith("sqlite"):
    path_str = DATABASE_URL.split(":///")[1] if ":///" in DATABASE_URL else ""
    if path_str:
        db_path = Path(path_str)
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"INFO: Database directory '{db_path.parent}' verified and created successfully.")
        except Exception as e:
            print(f"WARNING: Could not create database directory '{db_path.parent}': {e}")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def init_db():
    """Create all tables on startup."""
    # Import models here to ensure they are registered with Base
    from . import models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for FastAPI routes."""
    async with AsyncSessionLocal() as session:
        yield session