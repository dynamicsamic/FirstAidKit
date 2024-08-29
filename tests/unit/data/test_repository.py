import pytest
import pytest_asyncio
from sqlalchemy import insert, text
from sqlalchemy.engine import ScalarResult
from sqlalchemy.exc import CompileError, DBAPIError, IntegrityError, ProgrammingError
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

        assert len(r.all()) == limit

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

    @pytest.mark.xfail(raises=ProgrammingError, strict=True)
    async def test_fetch_many_with_invalid_limit_type(self):
        async with sessionmaker() as session:
            await Repo(session).fetch_many(limit="a12")

    @pytest.mark.xfail(raises=ProgrammingError, strict=True)
    async def test_fetch_many_with_invalid_offset_type(self):
        async with sessionmaker() as session:
            await Repo(session).fetch_many(offset="a12")

    @pytest.mark.xfail(raises=ProgrammingError, strict=True)
    async def test_fetch_many_with_invalid_order_by_type(self):
        async with sessionmaker() as session:
            await Repo(session).fetch_many(order_by=[text("invalid_col")])

    @pytest.mark.xfail(raises=ProgrammingError, strict=True)
    async def test_fetch_many_with_invalid_filter_type(self):
        async with sessionmaker() as session:
            await Repo(session).fetch_many(GenericModel.pk == "a")

    async def test_fetch_one_by_any_without_args(self):
        async with sessionmaker() as session:
            r = await Repo(session).fetch_one_by_any()

        assert isinstance(r, GenericModel)

    async def test_fetch_one_by_any_with_order_by(self):
        async with sessionmaker() as session:
            r = await Repo(session).fetch_one_by_any(order_by=[GenericModel.pk])

        assert r.pk == 1

    async def test_fetch_one_by_any_with_single_filter(self):
        async with sessionmaker() as session:
            r = await Repo(session).fetch_one_by_any(GenericModel.created_at < now())

        assert isinstance(r, GenericModel)

    async def test_fetch_one_by_any_with_mutually_exclusive_filters(self):
        async with sessionmaker() as session:
            r = await Repo(session).fetch_one_by_any(
                GenericModel.pk == 1, GenericModel.pk == 2
            )

        assert r is None

    async def test_fetch_one_by_pk_with_existing_pk(self):
        pk = 1
        async with sessionmaker() as session:
            r = await Repo(session).fetch_one_by_pk(pk=pk)

        assert isinstance(r, GenericModel)
        assert r.pk == pk

    async def test_fetch_one_by_pk_with_pk_does_not_exist(self):
        async with sessionmaker() as session:
            r = await Repo(session).fetch_one_by_pk(pk=-999)

        assert r is None

    async def test_insert_one_with_valid_payload(self):
        date = now()
        payload = {"pk": 1001, "created_at": date, "updated_at": date}

        async with sessionmaker() as session:
            r = await Repo(session).insert_one(**payload)

        assert isinstance(r, GenericModel)
        assert r.pk == payload["pk"]
        assert r.created_at == date
        assert r.updated_at == date

    @pytest.mark.xfail(raises=DBAPIError, strict=True)
    async def test_insert_one_with_invalid_payload(self):
        payload = {"pk": 1001, "created_at": now(), "updated_at": "hello"}
        async with sessionmaker() as session:
            await Repo(session).insert_one(**payload)

    @pytest.mark.xfail(raises=IntegrityError, strict=True)
    async def test_insert_one_with_duplicate_payload(self):
        async with sessionmaker() as session:
            repo = Repo(session)
            instance = await repo.fetch_one_by_any()
            payload = {"pk": instance.pk}
            await repo.insert_one(**payload)

    @pytest.mark.xfail(raises=CompileError, strict=True)
    async def test_insert_one_with_extra_attr_in_payload(self):
        payload = {"pk": 1001, "created_at": now(), "extra": "extra"}
        async with sessionmaker() as session:
            await Repo(session).insert_one(**payload)

    async def test_update_with_unique_filters(self):
        pk = 1
        filters = [GenericModel.pk == pk]
        payload = {"created_at": now()}
        async with sessionmaker() as session:
            r = await Repo(session).update(*filters, **payload)

        assert isinstance(r, ScalarResult)
        updated = r.all()
        assert len(updated) == 1
        updated = updated[0]
        assert isinstance(updated, GenericModel)
        assert updated.pk == pk
        assert updated.created_at == payload["created_at"]

        async with sessionmaker() as session:
            r = await Repo(session).fetch_one_by_pk(pk)
        assert r.pk == updated.pk
        assert r.created_at == updated.created_at

    async def test_update_with_generic_filters(self):
        pks = [1, 2, 3]
        filters = [GenericModel.pk.in_(pks)]
        payload = {"created_at": now()}
        async with sessionmaker() as session:
            r = await Repo(session).update(*filters, **payload)

        updated = r.all()
        assert len(updated) == len(pks)
        assert all(
            isinstance(updated[i], GenericModel)
            and updated[i].pk == pks[i]
            and updated[i].created_at == payload["created_at"]
            for i in range(len(updated))
        )

    async def test_update_with_mutually_exclusive_filters(self):
        filters = [GenericModel.pk == 1, GenericModel.pk == 2]
        payload = {"created_at": now()}
        async with sessionmaker() as session:
            r = await Repo(session).update(*filters, **payload)

        assert r.all() == []

    async def test_update_with_empty_payload(self):
        pk = 1
        async with sessionmaker() as session:
            r = await Repo(session).update(GenericModel.pk == pk)

        updated = r.all()
        assert len(updated) == 1
        assert isinstance(updated[0], GenericModel)
        assert updated[0].pk == pk

    @pytest.mark.xfail(raises=ProgrammingError, strict=True)
    async def test_update_with_invalid_filters(self):
        filters = [GenericModel.pk == "a12"]
        payload = {"created_at": now()}
        async with sessionmaker() as session:
            await Repo(session).update(*filters, **payload)

    @pytest.mark.xfail(raises=DBAPIError, strict=True)
    async def test_update_with_invalid_payload(self):
        filters = [GenericModel.pk == 1]
        payload = {"created_at": "INVALID"}
        async with sessionmaker() as session:
            await Repo(session).update(*filters, **payload)

    @pytest.mark.xfail(raises=CompileError, strict=True)
    async def test_update_with_extra_payload(self):
        filters = [GenericModel.pk == 1]
        payload = {"created_at": now(), "extra": "extra"}
        async with sessionmaker() as session:
            await Repo(session).update(*filters, **payload)

    async def test_update_one_by_pk_with_existing_pk(self):
        pk = 1
        payload = {"created_at": now()}
        async with sessionmaker() as session:
            updated = await Repo(session).update_one_by_pk(pk, **payload)

        assert isinstance(updated, GenericModel)
        assert updated.pk == pk
        assert updated.created_at == payload["created_at"]

        async with sessionmaker() as session:
            r = await Repo(session).fetch_one_by_pk(pk)
        assert r.pk == updated.pk
        assert r.created_at == updated.created_at

    async def test_update_one_by_pk_with_pk_does_not_exist(self):
        async with sessionmaker() as session:
            r = await Repo(session).update_one_by_pk(-999, created_at=now())

        assert r is None

    async def test_delete_with_unique_filters(self):
        pk = 1
        async with sessionmaker() as session:
            r = await Repo(session).delete(GenericModel.pk == pk)

        assert r == 1

    async def test_delete_with_generic_filters(self):
        pks = [2, 3, 4]
        async with sessionmaker() as session:
            r = await Repo(session).delete(GenericModel.pk.in_(pks))

        assert r == len(pks)

    async def test_delete_with_mutually_exclusive_filters(self):
        async with sessionmaker() as session:
            r = await Repo(session).delete(GenericModel.pk == 1, GenericModel.pk == 2)

        assert r == 0

    async def test_delete_with_row_does_not_exist(self):
        async with sessionmaker() as session:
            r = await Repo(session).delete(GenericModel.pk == -999)

        assert r == 0

    @pytest.mark.xfail(raises=ProgrammingError, strict=True)
    async def test_delete_with_invalid_filters(self):
        async with sessionmaker() as session:
            await Repo(session).delete(GenericModel.pk == "Invalid")

    async def test_exists_with_existing_pk(self):
        async with sessionmaker() as session:
            r = await Repo(session).exists(GenericModel.pk == 1)

        assert r is True

    async def test_exists_with_pk_does_not_exist(self):
        async with sessionmaker() as session:
            r = await Repo(session).exists(GenericModel.pk == -999)

        assert r is False

    @pytest.mark.xfail(raises=ProgrammingError, strict=True)
    async def test_exists_with_invalid_filters(self):
        async with sessionmaker() as session:
            await Repo(session).exists(GenericModel.pk == "Invalid")

    async def test_estimate(self):
        deviation_rate = 0.1
        deviation = round(TEST_SAMPLE * deviation_rate)
        async with sessionmaker() as session:
            r = await Repo(session).estimate()

        assert TEST_SAMPLE - deviation <= r <= TEST_SAMPLE + deviation
