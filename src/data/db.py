import logging

from sqlalchemy.ext.asyncio import create_async_engine

from src.settings import settings

from .models import Base

logger = logging.getLogger(__name__)


def create_db_url(
    db_user: str = settings.DB_USER,
    db_paswd: str = settings.DB_PASWD,
    db_name: str = settings.DB_NAME,
    db_host: str = settings.DB_HOST,
    db_port: int = settings.DB_PORT,
    db_dialect: str = None,
) -> str:
    if not db_dialect:
        db_dialect = settings.DB_DIALECT
    return f"{db_dialect}://{db_user}:{db_paswd}@{db_host}:{db_port}/{db_name}"


engine = create_async_engine(create_db_url(), echo=settings.DEBUG)


async def create_tables():
    async with engine.begin() as con:
        await con.run_sync(Base.metadata.create_all)


async def drop_tables():
    async with engine.begin() as con:
        await con.run_sync(Base.metadata.drop_all)


# async def drop_tables():
# async with
