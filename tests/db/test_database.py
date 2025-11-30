import pytest

from db.database import SQLAlchemyDatabase
from db.models import Listing


@pytest.fixture()
def db():
    database = SQLAlchemyDatabase("sqlite:///:memory:")
    database.init_db()
    database.create_tables()
    return database


def test_session_factory_expires_on_commit(db):
    assert db.SessionLocal.kw.get("expire_on_commit") is True


def test_session_scope_commits_and_cleans(db):
    with db.session_scope() as session:
        session.add(Listing(title="persist", listing_id="abc123"))

    with db.session_scope() as session:
        assert session.query(Listing).count() == 1


def test_session_scope_rolls_back_on_error(db):
    with pytest.raises(RuntimeError):
        with db.session_scope() as session:
            session.add(Listing(title="fail", listing_id="dup123"))
            raise RuntimeError("boom")

    with db.session_scope() as session:
        assert session.query(Listing).count() == 0
