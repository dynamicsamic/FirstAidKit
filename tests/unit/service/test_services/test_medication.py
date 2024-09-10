from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.exc import CompileError, DBAPIError, IntegrityError

from src.data.models import Medication as DBMedication
from src.data.repository import MedicationRepository as Repo
from src.domain.models import CreateMedication, Medication, PatchMedication
from src.domain.types import DosageForm
from src.service.exceptions import (
    DuplicateError,
    ExtraArgumentError,
    InvalidArgumentTypeError,
)
from src.service.services import MedicationService as Service
from src.utils import now as now_

from .mock_data import MockMedication

pytestmark = pytest.mark.asyncio


now = now_()
medication_id = 1
medication = DBMedication(
    pk=medication_id,
    brand_name="test1",
    generic_name="test1",
    dosage_form=DosageForm.TABLET,
    producer_id=1,
    category_id=1,
    created_at=now,
    updated_at=now,
)
medications = [medication for _ in range(3)]


@patch.object(Repo, "fetch_many", return_value=medications)
async def test_list_without_filters_return_list_of_medications(
    mock: AsyncMock,
):
    limit, offset = 10, 11
    r = await Service(None).list_items(limit=limit, offset=offset)
    mock.assert_awaited_once_with(
        limit=limit, offset=offset, order_by=[DBMedication.pk]
    )
    assert isinstance(r, list)
    assert all(isinstance(item, Medication) for item in r)


@patch.object(Repo, "fetch_many", return_value=medications)
async def test_list_with_some_filters_return_list_of_medications(
    mock: AsyncMock,
):
    limit, offset = 10, 11
    pks = [1, 2, 3]
    r = await Service(None).list_items(limit=limit, offset=offset, pk=pks)
    mock.assert_awaited_once()
    args, kwargs = mock.await_args
    assert kwargs == {"limit": limit, "offset": offset, "order_by": [DBMedication.pk]}
    assert args[0].compare(DBMedication.pk.in_(pks))
    assert isinstance(r, list)
    assert all(isinstance(item, Medication) for item in r)


@patch.object(Repo, "fetch_many", return_value=medications)
async def test_list_with_all_filters_return_list_of_medications(
    mock: AsyncMock,
):
    limit, offset = 10, 11
    pks = [1, 2, 3]
    brand_names = ["test1", "test2"]
    generic_names = ["test1", "test2", "test3"]
    dosage_forms = [DosageForm.TABLET]
    producer_ids = [534, 3, 11]
    category_ids = [91, 555, 1]
    created_before = now_()
    created_after = now_()
    updated_before = now_()
    updated_after = now_()
    r = await Service(None).list_items(
        limit=limit,
        offset=offset,
        pk=pks,
        brand_name=brand_names,
        generic_name=generic_names,
        dosage_form=dosage_forms,
        producer_id=producer_ids,
        category_id=category_ids,
        created_before=created_before,
        created_after=created_after,
        updated_before=updated_before,
        updated_after=updated_after,
    )
    mock.assert_awaited_once()
    args, kwargs = mock.await_args
    assert kwargs == {"limit": limit, "offset": offset, "order_by": [DBMedication.pk]}
    assert args[0].compare(DBMedication.created_at < created_before)
    assert args[1].compare(DBMedication.created_at > created_after)
    assert args[2].compare(DBMedication.updated_at < updated_before)
    assert args[3].compare(DBMedication.updated_at > updated_after)
    assert args[4].compare(DBMedication.pk.in_(pks))
    assert args[5].compare(DBMedication.brand_name.in_(brand_names))
    assert args[6].compare(DBMedication.generic_name.in_(generic_names))
    assert args[7].compare(DBMedication.dosage_form.in_(dosage_forms))
    assert args[8].compare(DBMedication.producer_id.in_(producer_ids))
    assert args[9].compare(DBMedication.category_id.in_(category_ids))
    assert isinstance(r, list)
    assert all(isinstance(item, Medication) for item in r)


@patch.object(Repo, "fetch_many", return_value=[])
async def test_list_with_empty_db_response_return_empty_list(
    mock: AsyncMock,
):
    r = await Service(None).list_items(limit=1, offset=1)
    mock.assert_awaited_once()
    assert r == []


@patch.object(Repo, "fetch_many")
async def test_list_items_with_invalid_column_name_filter_ignored(mock: AsyncMock):
    r = await Service(None).list_items(limit=1, offset=1, invalid="invalid")
    mock.assert_awaited_once()
    assert "invalid" not in mock.await_args.kwargs
    assert isinstance(r, list)
    assert all(isinstance(item, Medication) for item in r)


@pytest.mark.xfail(raises=ValueError, strict=True)
@patch.object(Repo, "fetch_many")
async def test_list_items_with_invalid_column_type_filter_ignored(mock: AsyncMock):
    await Service(None).list_items(limit=1, offset=1, pk=["one", "two"])
    mock.assert_awaited_once()


@pytest.mark.xfail(raises=ValueError, strict=True)
@patch.object(Repo, "fetch_many")
async def test_list_with_zero_limit_raises_value_error(mock: AsyncMock):
    await Service(None).list_items(limit=0, offset=1)
    mock.assert_not_awaited()


@pytest.mark.xfail(raises=ValueError, strict=True)
@patch.object(Repo, "fetch_many")
async def test_list_with_limit_too_high_raises_value_error(mock: AsyncMock):
    from src.settings import settings

    await Service(None).list_items(limit=settings.PAGINATION_LIMIT + 1, offset=1)
    mock.assert_not_awaited()


@pytest.mark.xfail(raises=ValueError, strict=True)
@patch.object(Repo, "fetch_many")
async def test_list_with_negative_offset_raises_value_error(mock: AsyncMock):
    await Service(None).list_items(limit=1, offset=-1)
    mock.assert_not_awaited()


@patch.object(Repo, "insert_one", return_value=medication)
async def test_create_with_valid_required_payload_return_created_instance(mock: AsyncMock):
    data = {
        "brand_name": "test1",
        "generic_name": "test1",
        "dosage_form": DosageForm.TABLET,
    }
    r = await Service(None).create(CreateMedication(**data))
    mock.assert_awaited_once_with(**data)
    assert isinstance(r, Medication)

@patch.object(Repo, "insert_one", return_value=medication)
async def test_create_with_valid_complete_payload_return_created_instance(mock: AsyncMock):
    data = {
        "brand_name": "test1",
        "generic_name": "test1",
        "dosage_form": DosageForm.TABLET,
        "producer_id": 1,
        "category_id": 1,
    }
    r = await Service(None).create(CreateMedication(**data))
    mock.assert_awaited_once_with(**data)
    assert isinstance(r, Medication)

@pytest.mark.xfail(raises=ExtraArgumentError, strict=True)
@patch.object(Repo, "insert_one", side_effect=CompileError)
async def test_create_with_extra_attribute_raises_extra_arg_error(_):
    data = {
        "brand_name": "test1",
        "generic_name": "test1",
        "dosage_form": DosageForm.TABLET,
        "extra": "extra"
    }
    await Service(None).create(MockMedication(**data))


@pytest.mark.xfail(raises=InvalidArgumentTypeError, strict=True)
@patch.object(Repo, "insert_one", side_effect=DBAPIError(None, None, Exception))
async def test_create_with_invalid_attribute_type_raises_invalid_arg_type_error(_):
    data = {
        "brand_name": 12344,
        "generic_name": "test1",
        "dosage_form": DosageForm.TABLET,
    }
    await Service(None).create(MockMedication(**data))


@pytest.mark.xfail(raises=ValueError, strict=True)
@patch.object(Repo, "insert_one")
async def test_create_with_empty_payload_raises_value_error(_):
    await Service(None).create(MockMedication())


@pytest.mark.xfail(raises=DuplicateError, strict=True)
@patch.object(Repo, "insert_one", side_effect=IntegrityError(None, None, Exception))
async def test_create_duplicate_payload_raises_duplicate_error(_):
    data = {
        "brand_name": "test1",
        "generic_name": "test1",
        "dosage_form": DosageForm.TABLET,
    }
    await Service(None).create(MockMedication(**data))


@patch.object(Repo, "fetch_one_by_pk", return_value=medication)
async def test_get_with_existing_id_return_medication_object(mock: AsyncMock):
    r = await Service(None).get(medication_id)
    mock.assert_awaited_once_with(pk=medication_id)
    assert isinstance(r, Medication)


@patch.object(Repo, "fetch_one_by_pk", return_value=None)
async def test_get_with_id_does_not_exist_return_none(mock: AsyncMock):
    r = await Service(None).get(medication_id)
    mock.assert_awaited_once_with(pk=medication_id)
    assert r is None


@patch.object(Repo, "update_one_by_pk", return_value=medication)
async def test_update_with_valid_partial_data_return_medication_object(mock: AsyncMock):
    data = {"created_at": now}
    r = await Service(None).update(medication_id, PatchMedication(**data))
    mock.assert_awaited_once_with(medication_id, **data)
    assert isinstance(r, Medication)


@patch.object(Repo, "update_one_by_pk", return_value=medication)
async def test_update_with_valid_complete_data_return_medication_object(
    mock: AsyncMock,
):
    data = {
        "brand_name": "test1",
        "generic_name": "test1",
        "dosage_form": DosageForm.TABLET,
        "producer_id": 1,
        "category_id": 1,
        "created_at": now,
        "updated_at": now,
    }
    r = await Service(None).update(medication_id, PatchMedication(**data))
    mock.assert_awaited_once_with(medication_id, **data)
    assert isinstance(r, Medication)


@patch.object(Repo, "update_one_by_pk", return_value=None)
async def test_update_with_id_does_not_exist_return_none(mock: AsyncMock):
    data = {"brand_name": "test"}
    r = await Service(None).update(medication_id, MockMedication(**data))
    mock.assert_awaited_once_with(medication_id, **data)
    assert r is None


@pytest.mark.xfail(raises=ExtraArgumentError, strict=True)
@patch.object(Repo, "update_one_by_pk", side_effect=CompileError)
async def test_update_with_extra_attribute_raises_(mock: AsyncMock):
    await Service(None).update(medication_id, MockMedication(extra="extra"))


@pytest.mark.xfail(raises=InvalidArgumentTypeError, strict=True)
@patch.object(Repo, "update_one_by_pk", side_effect=DBAPIError(None, None, Exception))
async def test_update_with_invalid_attribute_type_raises_invalid_arg_type_error(
    mock: AsyncMock,
):
    await Service(None).update(medication_id, MockMedication(brand_name=4773))


@pytest.mark.xfail(raises=DuplicateError, strict=True)
@patch.object(
    Repo, "update_one_by_pk", side_effect=IntegrityError(None, None, Exception)
)
async def test_update_with_duplicate_payload_raises_duplicate_error(mock: AsyncMock):
    await Service(None).update(medication_id, MockMedication(name="test"))


@pytest.mark.xfail(raises=ValueError, strict=True)
@patch.object(Repo, "update_one_by_pk")
async def test_update_with_empty_data_raises_value_errror(mock: AsyncMock):
    await Service(None).update(medication_id, MockMedication())


@patch.object(Repo, "delete", return_value=1)
async def test_delete_existing_medication_return_true(mock: AsyncMock):
    r = await Service(None).delete(medication_id)
    mock.assert_awaited_once()
    db_filter, *_ = mock.await_args.args
    assert db_filter.compare(DBMedication.pk == medication_id)
    assert r is True


@patch.object(Repo, "delete", return_value=0)
async def test_delete_medication_does_not_exist_return_false(mock: AsyncMock):
    r = await Service(None).delete(medication_id)
    mock.assert_awaited_once()
    db_filter, *_ = mock.await_args.args
    assert db_filter.compare(DBMedication.pk == medication_id)
    assert r is False
