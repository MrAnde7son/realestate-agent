"""Database configuration and session management with dependency injection."""

from __future__ import annotations

import os
from abc import abstractmethod
import logging
from contextlib import contextmanager
from typing import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Look for .env file in common locations
    # 1. Current directory
    if Path('.env').exists():
        load_dotenv('.env')
    # 2. backend-django directory (parent's sibling)
    backend_django_dir = Path(__file__).resolve().parent.parent / 'backend-django'
    env_file = backend_django_dir / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    # python-dotenv not available, skip
    pass

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

    logger = logging.getLogger(__name__)

    def __init__(self, database_url=None):
        # Try to get DATABASE_URL from environment, with intelligent default
        default_url = os.getenv("DATABASE_URL")
        if not default_url:
            # Default to db.sqlite3 in backend-django directory
            backend_django_dir = Path(__file__).resolve().parent.parent / 'backend-django'
            db_file = backend_django_dir / 'db.sqlite3'
            default_url = f"sqlite:///{db_file}"
        
        self.database_url = database_url or default_url
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
            
            self.logger.info("Database initialized successfully: %s", self.database_url)
            return True
            
        except Exception:
            self.logger.exception("Failed to initialize database")
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
            self.logger.info("All tables created successfully")
            return True
        except Exception:
            self.logger.exception("Failed to create tables")
            return False
    
    def close(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()

