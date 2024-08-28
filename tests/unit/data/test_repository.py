import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.data.db import create_db_url
from src.data.models import Base
from src.data.repository import ProducerRepository
from src.settings import dev_settings
from tests.utils import populate_db

pytestmark = pytest.mark.asyncio

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


@pytest_asyncio.fixture(loop_scope="module", autouse=True)
async def setup_db():

    async with engine.begin() as con:
        await con.run_sync(Base.metadata.create_all)
        await populate_db(con)

    yield

    async with engine.begin() as con:
        await con.run_sync(Base.metadata.drop_all)

    await engine.dispose()


async def test_foo():
    async with sessionmaker() as session:
        repo = ProducerRepository(session)
        r = await repo.fetch_one_by_pk(1)

    print(r.meds)
    # await session.execute(text("select 1"))
    # await drop_tables()
    # await create_tables()


# async def test_bar():
#     async with sessionmaker() as session:
#         await session.execute(text("select 2"))
