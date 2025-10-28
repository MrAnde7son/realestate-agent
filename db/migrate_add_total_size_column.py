#!/usr/bin/env python3
"""
Migration script to add the total_size column to the listings table.

This keeps the database schema aligned with the SQLAlchemy model so that
total lot area data collected from scrapers is persisted.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError


def migrate() -> bool:
    """Add the listings.total_size column when it is missing."""

    database_url = os.getenv("DATABASE_URL", "sqlite:///./backend-django/db.sqlite3")
    print(f"Starting migration for database: {database_url}")

    try:
        if database_url.startswith("sqlite"):
            engine = create_engine(database_url, connect_args={"check_same_thread": False})
            sqlite = True
        else:
            engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=300)
            sqlite = False
    except SQLAlchemyError as exc:
        print(f"Failed to create engine: {exc}")
        return False

    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
    except SQLAlchemyError as exc:
        print(f"Failed to inspect database: {exc}")
        return False

    if "listings" not in tables:
        print("Listings table not found; no changes applied.")
        return False

    try:
        existing_columns = {column["name"] for column in inspector.get_columns("listings")}
    except SQLAlchemyError as exc:
        print(f"Failed to read listings schema: {exc}")
        return False

    if "total_size" in existing_columns:
        print("total_size column already exists; nothing to do.")
        return True

    statement = text("ALTER TABLE listings ADD COLUMN total_size FLOAT")

    # SQLite supports ADD COLUMN with NULL defaults with no additional handling.
    try:
        with engine.begin() as conn:
            conn.execute(statement)
            print("Executed: ALTER TABLE listings ADD COLUMN total_size FLOAT")
    except SQLAlchemyError as exc:
        print(f"Failed to apply schema changes: {exc}")
        return False

    print("Migration completed successfully.")
    return True


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
