from app.config import Settings


def test_plain_postgresql_url_uses_installed_psycopg_driver() -> None:
    settings = Settings(database_url="postgresql://hr:encoded%40pass@db.example:5432/salary")

    assert settings.sqlalchemy_url.drivername == "postgresql+psycopg"
    assert settings.sqlalchemy_url.password == "encoded@pass"


def test_existing_explicit_postgresql_driver_is_preserved() -> None:
    settings = Settings(database_url="postgresql+psycopg://hr:secret@db.example:5432/salary")

    assert settings.sqlalchemy_url.drivername == "postgresql+psycopg"
