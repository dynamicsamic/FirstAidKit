from pydantic_settings import BaseSettings
from zoneinfo import ZoneInfo


class DevSettings(BaseSettings):
    TZ: ZoneInfo = ZoneInfo("Europe/Moscow")
    DEBUG: bool = True

    DB_DIALECT: str = "postgresql+asyncpg"
    DB_USER: str = "test_user"
    DB_PASWD: str = "test_user"
    DB_NAME: str = "test_aidkit"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

class ProdSettings(BaseSettings):
    TZ: ZoneInfo = ZoneInfo("Europe/Moscow")
    DEBUG: bool = True
    ITEMS_PER_PAGE: int = 20
    PAGINATION_LIMIT: int = 100


    DB_DIALECT: str = "postgresql+asyncpg"
    DB_USER: str = "test_user"
    DB_PASWD: str = "test_user"
    DB_NAME: str = "test_aidkit"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

dev_settings= DevSettings()
settings = ProdSettings()
