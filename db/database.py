"""Database configuration and session management with dependency injection."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()


class Database(ABC):
    """Abstract database interface for dependency injection."""

    @abstractmethod
    def init_db(self) -> None:
        """Create database tables if they do not exist."""

    @abstractmethod
    @contextmanager
    def get_session(self) -> Iterator[Session]:
        """Yield a SQLAlchemy session."""


class SQLAlchemyDatabase(Database):
    """SQLAlchemy-backed database implementation."""

    def __init__(self, url: Optional[str] = None) -> None:
        self.url = url or os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:postgres@localhost:5432/realestate",
        )
        self.engine = create_engine(self.url, future=True)
        self.SessionLocal = sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False
        )

    def init_db(self) -> None:
        # Import models within the function to avoid circular imports during
        # initialization.
        import db.models  # noqa: F401

        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self) -> Iterator[Session]:
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

