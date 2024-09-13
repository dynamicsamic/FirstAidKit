import pytest
import pytest_asyncio
from sqlalchemy import insert
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import DetachedInstanceError

from src.data.models import Category, Medication, Producer
from src.data.repository import MedicationRepository as Repo
from src.domain.types import DosageForm
from tests.conftest import DEFAULT_LIMIT

from . import db_setup_generator, sessionmaker

pytestmark = pytest.mark.asyncio
TEST_SAMPLE = 30

insert_stmts = [
    insert(Category).values([{"name": f"cat{i}"} for i in range(3)]),
    insert(Producer).values([{"name": f"prod{i}"} for i in range(3)]),
    insert(Medication).values(
        [
            {
                "brand_name": f"br_name{i}",
                "generic_name": f"gen_name{i}",
                "dosage_form": DosageForm.TABLET,
                "producer_id": 1,
                "category_id": 1,
            }
            for i in range(TEST_SAMPLE)
        ]
    ),
]

db_setup = pytest_asyncio.fixture(loop_scope="module", autouse=True)(
    db_setup_generator(*insert_stmts)
)


async def test_fetch_one_return_medication_with_producer_and_category_names_and_pks():
    async with sessionmaker() as session:
        r = await Repo(session).fetch_one_by_any(Medication.brand_name == "br_name1")

    assert isinstance(r, Medication)
    assert r.producer.name is not None and r.producer.pk is not None
    assert r.category.name is not None and r.category.pk is not None

    from src.data.repository import CategoryRepository, ProducerRepository

    async with sessionmaker() as session:
        producer = await ProducerRepository(session).fetch_one_by_pk(r.producer.pk)
        category = await CategoryRepository(session).fetch_one_by_pk(r.category.pk)

    assert r.producer.name == producer.name
    assert r.category.name == category.name


@pytest.mark.xfail(raises=DetachedInstanceError, strict=True)
async def test_accessing_deffered_producer_and_category_attrs_raises_alchemy_error():
    async with sessionmaker() as session:
        r = await Repo(session).fetch_one_by_any(Medication.brand_name == "br_name1")

    assert r.producer.created_at
    assert r.producer.updated_at


async def test_fetch_many_return_medications_with_producer_and_category_names():
    async with sessionmaker() as session:
        r = await Repo(session).fetch_many()

    assert isinstance(r, ScalarResult)
    items = r.all()
    assert len(items) == DEFAULT_LIMIT
    assert all(isinstance(obj, Medication) for obj in items)
    assert all(
        isinstance(i.producer.name, str)
        and isinstance(i.producer.pk, int)
        and isinstance(i.category.name, str)
        and isinstance(i.category.pk, int)
        for i in items
    )


@pytest.mark.xfail(raises=IntegrityError, strict=True)
async def test_insert_medication_breaking_unique_constraint_raises_error():
    async with sessionmaker() as session:
        data = {
            "brand_name": "br_name1",
            "generic_name": "gen_name1",
            "dosage_form": DosageForm.TABLET,
            "producer_id": 1,
            "category_id": 1,
        }
        await Repo(session).insert_one(**data)
