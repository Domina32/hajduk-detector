from app.core.db import engine


def test_suite_uses_test_database() -> None:
    assert engine.url.database == "app_test"
