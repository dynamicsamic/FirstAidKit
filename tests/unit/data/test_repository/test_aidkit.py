from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import insert

from src.data.models import AidKit, Category, Medication, MedicationStock, Producer
from src.data.repository import AidKitRepository as Repo
from src.domain.types import DosageForm, MeasureUnit

from . import db_setup_generator, sessionmaker

pytestmark = pytest.mark.asyncio
TEST_SAMPLE = 30

aidkit_data = [{"name": f"kit-{i}", "location": f"room-{i}"} for i in range(3)]
medication_data = [
    {
        "brand_name": f"br_name{i}",
        "generic_name": f"gen_name{i}",
        "dosage_form": DosageForm.TABLET,
        "producer_id": 1,
        "category_id": 1,
    }
    for i in range(TEST_SAMPLE)
]
stock_data = [
    {
        "quantity": i,
        "measure_unit": MeasureUnit.GRAM,
        "production_date": date.today(),
        "best_before": date.today() + timedelta(days=1),
        "opened_at": date.today() - timedelta(days=-1),
        "medication_id": 1,
        "aidkit_id": 1,
    }
    for i in range(TEST_SAMPLE)
]
insert_stmts = [
    insert(AidKit).values(aidkit_data),
    insert(Category).values([{"name": f"cat-{i}"} for i in range(3)]),
    insert(Producer).values([{"name": f"prod-{i}"} for i in range(3)]),
    insert(Medication).values(medication_data),
    insert(MedicationStock).values(stock_data),
]

db_setup = pytest_asyncio.fixture(loop_scope="module", autouse=True)(
    db_setup_generator(*insert_stmts)
)


async def test_fetch_one_return_aidkit_with_stock_count_calculated():
    async with sessionmaker() as session:
        r = await Repo(session).fetch_one_by_any(AidKit.name == "kit-0")

    assert isinstance(r, AidKit)
    assert r.stock_count == TEST_SAMPLE


async def test_fetch_many_return_aidkits_stock_count_calculated():
    async with sessionmaker() as session:
        r = await Repo(session).fetch_many()

    items = r.all()
    assert all(isinstance(item, AidKit) for item in items)
    assert items[0].stock_count == TEST_SAMPLE
    assert items[1].stock_count == 0
