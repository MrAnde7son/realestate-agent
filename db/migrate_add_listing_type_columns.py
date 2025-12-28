#!/usr/bin/env python3
"""
Migration script to add listing_type and ad_type columns to the listings table.

Run this once per environment after deploying the code that expects these fields.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError


def migrate():
    """Add missing listing_type and ad_type columns to the listings table."""

    database_url = os.getenv("DATABASE_URL", "sqlite:///./backend-django/db.sqlite3")
    print(f"Starting migration for database: {database_url}")

    try:
        if database_url.startswith("sqlite"):
            engine = create_engine(
                database_url, connect_args={"check_same_thread": False}
            )
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
        existing_columns = {
            column["name"] for column in inspector.get_columns("listings")
        }
    except SQLAlchemyError as exc:
        print(f"Failed to read listings schema: {exc}")
        return False

    pending_statements = []
    if "listing_type" not in existing_columns:
        pending_statements.append(
            "ALTER TABLE listings ADD COLUMN listing_type VARCHAR(50)"
        )
    if "ad_type" not in existing_columns:
        pending_statements.append("ALTER TABLE listings ADD COLUMN ad_type VARCHAR(50)")

    if not pending_statements:
        print("Both listing_type and ad_type columns already exist; nothing to do.")
        return True

    if sqlite:
        # SQLite allows ADD COLUMN with no DEFAULT clause; no extra handling needed here.
        pass

    try:
        with engine.begin() as conn:
            for statement in pending_statements:
                conn.execute(text(statement))
                print(f"Executed: {statement}")
    except SQLAlchemyError as exc:
        print(f"Failed to apply schema changes: {exc}")
        return False

    print("Migration completed successfully.")
    return True


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
