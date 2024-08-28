import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from litestar import Litestar
from litestar.datastructures import State
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.settings import settings

from .db import create_db_url

logger = logging.getLogger(__name__)
sessionmaker = async_sessionmaker(expire_on_commit=False, autoflush=False)


@asynccontextmanager
async def provide_engine(app: Litestar) -> AsyncGenerator[None, None]:
    engine = getattr(app, "db_engine", None)
    if not engine:
        engine = create_async_engine(create_db_url(), echo=settings.DEBUG)
        app.state.db_engine = engine

    try:
        yield
    finally:
        await engine.dispose()


async def provide_db_session(state: State) -> AsyncGenerator[AsyncSession, None]:
    async with sessionmaker(bind=state.db_engine) as session:
        try:
            async with session.begin():
                yield session
        except Exception as err:
            logger.error(f"Error occured during db_session execution: {err}")
            raise