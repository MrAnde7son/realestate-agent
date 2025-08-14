#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for database initialization and the Listing model."""

from datetime import datetime
from sqlalchemy import inspect


def _setup(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    from db import SQLAlchemyDatabase, models

    db = SQLAlchemyDatabase()
    db.init_db()
    return db, models


def test_init_db_creates_tables(monkeypatch):
    db, models = _setup(monkeypatch)
    inspector = inspect(db.engine)
    assert "listings" in inspector.get_table_names()


def test_listing_model_persists_multiple_sources(monkeypatch):
    db, models = _setup(monkeypatch)
    with db.get_session() as session:
        session.add_all([
            models.Listing(source="yad2", external_id="1", title="Yad2", scraped_at=datetime.utcnow()),
            models.Listing(source="madlan", external_id="1", title="Madlan", scraped_at=datetime.utcnow()),
            models.Listing(source="onmap", external_id="2", title="OnMap", scraped_at=datetime.utcnow()),
        ])
        session.commit()
        counts = {
            source: session.query(models.Listing).filter_by(source=source).count()
            for source in ["yad2", "madlan", "onmap"]
        }
        assert counts["yad2"] == 1
        assert counts["madlan"] == 1
        assert counts["onmap"] == 1

