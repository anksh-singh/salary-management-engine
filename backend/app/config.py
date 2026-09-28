from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://localhost/salary_management"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def sqlalchemy_url(self) -> URL:
        return make_url(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
