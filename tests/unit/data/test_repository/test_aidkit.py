from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import insert
from sqlalchemy.orm.exc import DetachedInstanceError

from src.data.models import AidKit, Category, Medication, MedicationStock, Producer
from src.data.repository import AidKitRepository as Repo
from src.domain.types import DosageForm, MeasureUnit
from tests.conftest import DEFAULT_LIMIT

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


async def test_fetch_many_return_aidkits_without_loading_relations():
    async with sessionmaker() as session:
        r = await Repo(session).fetch_many()

    aidkit = r.all()[0]
    assert isinstance(aidkit, AidKit)
    assert aidkit.stocks == []


async def test_fetch_one_return_aidkit_with_stocks_and_their_relations_loaded():
    async with sessionmaker() as session:
        r = await Repo(session).fetch_one_by_any(AidKit.name == "kit-0")

    assert isinstance(r, AidKit)

    stocks = r.stocks
    assert isinstance(stocks, list)
    assert len(stocks) == DEFAULT_LIMIT
    assert all(isinstance(item, MedicationStock) for item in stocks)

    stock = stocks[0]
    assert isinstance(stock.pk, int)
    assert isinstance(stock.quantity, int)
    assert isinstance(stock.measure_unit, MeasureUnit)
    assert isinstance(stock.production_date, date)
    assert isinstance(stock.best_before, date)
    assert isinstance(stock.opened_at, date)

    medication = stock.medication
    assert isinstance(medication, Medication)
    assert isinstance(medication.pk, int)
    assert isinstance(medication.brand_name, str)
    assert isinstance(medication.generic_name, str)
    assert isinstance(medication.dosage_form, DosageForm)

    producer = medication.producer
    assert isinstance(producer, Producer)
    assert isinstance(producer.pk, int)
    assert isinstance(producer.name, str)

    category = medication.category
    assert isinstance(category, Category)
    assert isinstance(category.pk, int)
    assert isinstance(category.name, str)


async def test_fetch_one_with_custom_stock_limit_and_offset_changes_the_size_of_stocks():
    limit, offset = 5, 2
    async with sessionmaker() as session:
        r = await Repo(session).fetch_one_by_any(
            AidKit.pk == 1, stock_limit=limit, stock_offset=offset
        )

    assert len(r.stocks) == limit
    assert all(item.pk > offset for item in r.stocks)


async def test_accessing_defered_attributes_raises_error():
    async with sessionmaker() as session:
        r = await Repo(session).fetch_one_by_any(AidKit.location == "room-0")

    stock = r.stocks[0]
    stock_deferred_cols = ["aidkit_id", "medication_id", "created_at", "updated_at"]
    for col in stock_deferred_cols:
        with pytest.raises(DetachedInstanceError):
            getattr(stock, col)

    medication = stock.medication
    medication_deferred_cols = [
        "category_id",
        "producer_id",
        "created_at",
        "updated_at",
    ]
    for col in medication_deferred_cols:
        with pytest.raises(DetachedInstanceError):
            getattr(medication, col)

    producer_and_category_deferred_cols = ["created_at", "updated_at"]

    producer = medication.producer
    for col in producer_and_category_deferred_cols:
        with pytest.raises(DetachedInstanceError):
            getattr(producer, col)

    category = medication.category
    for col in producer_and_category_deferred_cols:
        with pytest.raises(DetachedInstanceError):
            getattr(category, col)
