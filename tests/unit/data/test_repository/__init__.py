from typing import Iterable

from sqlalchemy import Insert
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.data.db import create_db_url
from src.data.models import Base
from src.settings import dev_settings

engine = create_async_engine(
    create_db_url(
        dev_settings.DB_USER,
        dev_settings.DB_PASWD,
        dev_settings.DB_NAME,
        dev_settings.DB_HOST,
        dev_settings.DB_PORT,
    ),
    echo=True,
)
sessionmaker = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def db_setup_generator(*insert_stmts: Iterable[Insert]):
    async def setup_db():

        async with engine.begin() as con:
            await con.run_sync(Base.metadata.create_all)
            for stmt in insert_stmts:
                await con.execute(stmt)

        yield

        async with engine.begin() as con:
            await con.run_sync(Base.metadata.drop_all)

        await engine.dispose()

    return setup_db
