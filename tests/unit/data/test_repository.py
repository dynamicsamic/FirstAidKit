import pytest
import pytest_asyncio
from sqlalchemy import insert
from sqlalchemy.engine import ScalarResult
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.data.db import create_db_url
from src.data.models import Base, BaseModel
from src.data.repository import Repository
from src.settings import dev_settings
from src.utils import now
from tests.conftest import DEFAULT_LIMIT

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

TEST_SAMPLE = 30


class GenericModel(BaseModel):
    __tablename__ = "fakes"


class GenericRepo(Repository):
    model = GenericModel


Repo = GenericRepo


@pytest_asyncio.fixture(loop_scope="module", autouse=True)
async def setup_db():

    async with engine.begin() as con:
        await con.run_sync(Base.metadata.create_all)
        await con.execute(insert(GenericModel).values([{} for _ in range(TEST_SAMPLE)]))

    yield

    async with engine.begin() as con:
        await con.run_sync(Base.metadata.drop_all)

    await engine.dispose()


class TestGenericRepository:

    async def test_fetch_many_without_args(self):
        async with sessionmaker() as session:
            r = await Repo(session).fetch_many()

        assert isinstance(r, ScalarResult)
        items = r.all()
        assert len(items) == DEFAULT_LIMIT
        assert all(isinstance(obj, GenericModel) for obj in r.all())

    async def test_fetch_many_with_custom_limit(self):
        limit = 7
        async with sessionmaker() as session:
            r = await Repo(session).fetch_many(limit=limit)

        assert len(r.all) == limit

    async def test_fetch_many_with_custom_offset(self):
        offset = 7
        async with sessionmaker() as session:
            r = await Repo(session).fetch_many(offset=offset)

        assert all(item.pk > offset for item in r.all())

    async def test_fetch_many_with_order_by(self):
        async with sessionmaker() as session:
            r = await Repo(session).fetch_many(order_by=[GenericModel.pk.desc()])

        items = r.all()
        assert all(items[i].pk > items[i + 1].pk for i in range(len(items) - 1))

    async def test_fetch_many_with_single_filter(self):
        pks = [1, 2, 3]
        async with sessionmaker() as session:
            r = await Repo(session).fetch_many(GenericModel.pk.in_(pks))

        assert len(r.all()) == len(pks)

    async def test_fetch_many_with_inclusive_filters(self):
        pks = [1, 2, 3]
        filters = [GenericModel.pk.in_(pks), GenericModel.created_at < now()]
        async with sessionmaker() as session:
            r = await Repo(session).fetch_many(*filters)

        assert len(r.all()) == len(pks)

    async def test_fetch_many_with_mutually_exclusive_filters(self):
        async with sessionmaker() as session:
            r = await Repo(session).fetch_many(
                GenericModel.pk == 1, GenericModel.pk == 2
            )

        assert len(r.all()) == 0

    async def test_estimate(self):
        async with sessionmaker() as session:
            r = await Repo(session).estimate()

        print(r)
