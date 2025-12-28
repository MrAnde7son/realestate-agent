#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script to change the floor field from INTEGER to VARCHAR(50) in the listings table.
This fixes the issue where Hebrew floor descriptions were causing database errors.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


def migrate_floor_field():
    """Migrate the floor field from INTEGER to VARCHAR(50)."""

    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "sqlite:///./backend-django/db.sqlite3")

    print(f"Starting migration for database: {database_url}")

    try:
        # Create engine
        if database_url.startswith("sqlite"):
            engine = create_engine(
                database_url, connect_args={"check_same_thread": False}
            )
        else:
            engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=300)

        with engine.connect() as conn:
            # Check if we're using PostgreSQL or SQLite
            if database_url.startswith("postgresql"):
                # PostgreSQL migration
                print("Detected PostgreSQL database")

                # Check if the column exists and its current type
                result = conn.execute(
                    text("""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'listings' AND column_name = 'floor'
                """)
                )

                row = result.fetchone()
                if row:
                    current_type = row[0]
                    print(f"Current floor column type: {current_type}")

                    if current_type == "integer":
                        print("Converting floor column from INTEGER to VARCHAR(50)...")

                        # For PostgreSQL, we need to alter the column type
                        conn.execute(
                            text(
                                "ALTER TABLE listings ALTER COLUMN floor TYPE VARCHAR(50)"
                            )
                        )
                        conn.commit()
                        print("Floor column successfully converted to VARCHAR(50)")
                    else:
                        print(
                            f"Floor column is already {current_type}, no migration needed"
                        )
                else:
                    print("Floor column not found in listings table")
                    return False

            else:
                # SQLite migration
                print("Detected SQLite database")

                # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
                print("SQLite requires table recreation for column type changes...")

                # Check if the table exists
                result = conn.execute(
                    text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='listings'
                """)
                )

                if not result.fetchone():
                    print("Listings table not found")
                    return False

                # Get the current table schema
                result = conn.execute(text("PRAGMA table_info(listings)"))
                columns = result.fetchall()

                # Find the floor column
                floor_column = None
                for col in columns:
                    if col[1] == "floor":
                        floor_column = col
                        break

                if not floor_column:
                    print("Floor column not found in listings table")
                    return False

                print(f"Current floor column type: {floor_column[2]}")

                if floor_column[2].upper() == "INTEGER":
                    print("Recreating listings table with VARCHAR(50) floor column...")

                    # Create new table with correct schema
                    conn.execute(
                        text("""
                        CREATE TABLE listings_new (
                            id INTEGER PRIMARY KEY,
                            title VARCHAR(255),
                            price FLOAT,
                            address VARCHAR(255),
                            rooms FLOAT,
                            floor VARCHAR(50),
                            size FLOAT,
                            property_type VARCHAR(100),
                            description TEXT,
                            url VARCHAR(500),
                            listing_id VARCHAR(100),
                            latitude FLOAT,
                            longitude FLOAT,
                            scraped_at DATETIME
                        )
                    """)
                    )

                    # Copy data from old table to new table
                    conn.execute(
                        text("""
                        INSERT INTO listings_new 
                        SELECT id, title, price, address, rooms, 
                               CASE 
                                   WHEN floor IS NULL THEN NULL
                                   WHEN CAST(floor AS TEXT) = floor THEN floor
                                   ELSE CAST(floor AS TEXT)
                               END as floor,
                               size, property_type, description, url, listing_id, 
                               latitude, longitude, scraped_at
                        FROM listings
                    """)
                    )

                    # Drop old table and rename new table
                    conn.execute(text("DROP TABLE listings"))
                    conn.execute(text("ALTER TABLE listings_new RENAME TO listings"))

                    # Recreate indexes
                    conn.execute(
                        text(
                            "CREATE UNIQUE INDEX ix_listings_listing_id ON listings (listing_id)"
                        )
                    )

                    conn.commit()
                    print(
                        "Listings table successfully recreated with VARCHAR(50) floor column"
                    )
                else:
                    print(
                        f"Floor column is already {floor_column[2]}, no migration needed"
                    )

        print("Migration completed successfully!")
        return True

    except SQLAlchemyError as e:
        print(f"Database error during migration: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during migration: {e}")
        return False


if __name__ == "__main__":
    success = migrate_floor_field()
    sys.exit(0 if success else 1)
