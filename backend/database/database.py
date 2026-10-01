"""
SafeUPI database configuration and session management.

Default configuration uses SQLite for local development so the project can
run without requiring a PostgreSQL server. Set DATABASE_URL to PostgreSQL
when deploying or integrating with a real database.

Examples:
    SQLite:
        DATABASE_URL=sqlite:///./safeupi.db

    PostgreSQL:
        DATABASE_URL=postgresql+psycopg2://user:password@localhost/safeupi
"""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DEFAULT_DATABASE_URL = "sqlite:///./safeupi.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


# SQLite needs this option because FastAPI may use multiple worker/request
# threads during local development.
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides one database session per request.

    The session is always closed after the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Create all tables defined on Base.metadata.

    Importing models before calling this function ensures SQLAlchemy knows
    about the ORM tables.
    """
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def reset_sqlite_database() -> None:
    """
    Delete the local SQLite database file.

    Intended for development/testing only. It does nothing for non-SQLite
    databases.
    """
    if not DATABASE_URL.startswith("sqlite:///"):
        raise RuntimeError(
            "reset_sqlite_database() is only available for SQLite."
        )

    db_path = DATABASE_URL.removeprefix("sqlite:///")
    path = Path(db_path)

    if path.exists():
        path.unlink()
