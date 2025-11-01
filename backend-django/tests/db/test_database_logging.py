import logging

import pytest

from broker_backend import settings


@pytest.mark.parametrize(
    "db_settings,expected_fragment",
    [
        (
            {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': '/tmp/test.sqlite3',
            },
            "SQLite database at '/tmp/test.sqlite3'",
        ),
        (
            {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'nadlaner',
                'USER': 'broker',
                'HOST': 'postgres',
                'PORT': '5432',
                'PASSWORD': 'super-secret',
            },
            (
                "PostgreSQL database 'nadlaner' "
                "(user='broker', host='postgres', port='5432')"
            ),
        ),
    ],
)
def test_log_database_configuration_formats_expected_message(
    caplog: pytest.LogCaptureFixture,
    db_settings,
    expected_fragment,
):
    with caplog.at_level(logging.INFO):
        settings.log_database_configuration(db_settings)

    assert expected_fragment in caplog.text
    assert 'super-secret' not in caplog.text


def test_describe_database_handles_unknown_engine() -> None:
    description = settings._describe_database(
        {'ENGINE': 'django.db.backends.mysql'}
    )
    assert description == "Database engine 'django.db.backends.mysql'"
