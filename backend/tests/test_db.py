from app.core.db import engine


def test_suite_uses_test_database() -> None:
    assert engine.url.database is not None
    assert engine.url.database.endswith("_test")
    assert engine.url.database != "app"
