"""Database configuration and session management with dependency injection."""

from __future__ import annotations

import os
from abc import abstractmethod
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

Base = declarative_base()


class Database:
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

    def __init__(self, database_url=None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "sqlite:///./realestate.db",
        )
        self.engine = None
        self.SessionLocal = None
        
    def init_db(self):
        """Initialize database connection and create tables."""
        try:
            # Create engine with appropriate configuration
            if self.database_url.startswith('sqlite'):
                # SQLite configuration
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool
                )
            else:
                # PostgreSQL configuration
                self.engine = create_engine(
                    self.database_url,
                    pool_pre_ping=True,
                    pool_recycle=300
                )
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            print(f"Database initialized successfully: {self.database_url}")
            return True
            
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            return False
    
    def get_session(self):
        """Get a database session."""
        if not self.SessionLocal:
            self.init_db()
        return self.SessionLocal()
    
    def create_tables(self):
        """Create all tables defined in models."""
        try:
            from .models import Base
            Base.metadata.create_all(bind=self.engine)
            print("All tables created successfully")
            return True
        except Exception as e:
            print(f"Failed to create tables: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()

