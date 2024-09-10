from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from litestar import status_codes
from litestar.testing import AsyncTestClient

from src.domain.constraints import (
    MEDICATION_BRAND_NAME_LENGTH,
    MEDICATION_GENERIC_NAME_LENGTH,
)
from src.domain.models import (
    BriefCategory,
    BriefProducer,
    CreateMedication,
    Medication,
    PatchMedication,
)
from src.domain.types import DosageForm
from src.restapi.app import app
from src.service.exceptions import (
    DuplicateError,
    ExtraArgumentError,
    InvalidArgumentTypeError,
)
from src.service.services import MedicationService as Service
from src.utils import now as now_
from tests.conftest import DEFAULT_LIMIT

from .mock_response import MedicationJSONResponse

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def test_client():
    async with AsyncTestClient(app=app) as client:
        yield client


now = now_()
medication_id = 1
medication = Medication(
    pk=medication_id,
    brand_name="name",
    generic_name="gname",
    dosage_form=DosageForm.TABLET,
    producer=BriefProducer(name="first_prod", pk=1),
    category=BriefCategory(name="cat", pk=1),
    created_at=now,
    updated_at=now,
)
medications = [medication for _ in range(3)]
base_url = "/api/v1/medications"
item_url = f"{base_url}/{medication_id}"


@patch.object(Service, "list_items", return_value=medications)
async def test_list_medications_without_query_args_use_default_values(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(base_url)

    mock.assert_awaited_once_with(
        limit=DEFAULT_LIMIT,
        offset=0,
        created_before=None,
        created_after=None,
        updated_before=None,
        updated_after=None,
        pk=None,
        brand_name=None,
        generic_name=None,
        dosage_form=None,
        producer_id=None,
        category_id=None,
    )
    assert resp.status_code == status_codes.HTTP_200_OK
    body = resp.json()
    assert isinstance(body, list)
    assert all(Medication.model_validate(MedicationJSONResponse(**item)) for item in body)


@patch.object(Service, "list_items", return_value=medications)
async def test_list_medications_with_query_args_uses_provided_args(
    mock: AsyncMock, test_client: AsyncTestClient
):
    from datetime import datetime as dt

    limit = 10
    offset = 5
    datestring = "2015-01-16T16:52:00"
    date = dt.fromisoformat(datestring)
    ids = [1, 2, 3]
    brand_names = ["name1", "name2"]
    generic_names = ["med1", "med2"]
    dosage_forms = [DosageForm.TABLET]
    producer_ids = [63, 11]
    category_ids = [12, 10]
    url = (
        f"{base_url}?limit={limit}&offset={offset}"
        f"&createdBefore={datestring}&createdAfter={datestring}"
        f"&updatedBefore={datestring}&updatedAfter={datestring}&brandNames={brand_names[0]}"
        f"&brandNames={brand_names[1]}&ids={ids[0]}&ids={ids[1]}&ids={ids[2]}"
        f"&genericNames={generic_names[0]}&genericNames={generic_names[1]}"
        f"&dosageForms={dosage_forms[0]}&producerIds={producer_ids[0]}"
        f"&producerIds={producer_ids[1]}&categoryIds={category_ids[0]}"
        f"&categoryIds={category_ids[1]}"
    )
    resp = await test_client.get(url)

    assert resp.status_code == status_codes.HTTP_200_OK
    mock.assert_awaited_once_with(
        limit=limit,
        offset=offset,
        pk=ids,
        brand_name=brand_names,
        generic_name=generic_names,
        dosage_form=dosage_forms,
        producer_id=producer_ids,
        category_id=category_ids,
        created_before=date,
        created_after=date,
        updated_before=date,
        updated_after=date,
    )
    body = resp.json()
    assert isinstance(body, list)
    assert all(Medication.model_validate(MedicationJSONResponse(**item)) for item in body)


@patch.object(Service, "list_items", return_value=[])
async def test_list_medications_with_empty_service_response(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(base_url)

    assert resp.status_code == status_codes.HTTP_200_OK
    mock.assert_awaited_once()
    assert resp.json() == []


@patch.object(Service, "list_items", return_value=medications)
async def test_list_medications_with_extra_query_arg_is_ignored(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(f"{base_url}?extra=extra1")

    assert resp.status_code == status_codes.HTTP_200_OK
    mock.assert_awaited_once()
    assert "extra" not in mock.await_args.kwargs


@patch.object(Service, "list_items")
async def test_list_medications_with_invalid_query_arg_type_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(f"{base_url}?createdBefore=hello")

    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    mock.assert_not_awaited()
    body = resp.json()
    assert set(body.keys()) == {"status_code", "detail", "extra"}


@patch.object(Service, "list_items")
async def test_list_medications_with_negative_limit_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(f"{base_url}?limit=-14")

    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    mock.assert_not_awaited()
    body = resp.json()
    assert set(body.keys()) == {"status_code", "detail", "extra"}


@patch.object(Service, "list_items")
async def test_list_medications_with_limit_too_high_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(f"{base_url}?limit=200")

    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    mock.assert_not_awaited()
    body = resp.json()
    assert set(body.keys()) == {"status_code", "detail", "extra"}


@patch.object(Service, "create", return_value=medication)
async def test_add_medication_with_valid_complete_payload_return_created_instance(
    mock: AsyncMock, test_client: AsyncTestClient
):
    data = {
        "brand_name": "test1",
        "generic_name": "test2",
        "dosage_form": DosageForm.TABLET,
        "producer_id": 1,
        "category_id": 1,
    }
    resp = await test_client.post(base_url, json=data)

    mock.assert_awaited_once_with(CreateMedication(**data))
    assert resp.status_code == status_codes.HTTP_201_CREATED
    assert Medication.model_validate(MedicationJSONResponse(**resp.json()))


@patch.object(Service, "create", return_value=medication)
async def test_add_medication_with_valid_partial_payload_return_created_instance(
    mock: AsyncMock, test_client: AsyncTestClient
):
    data = {
        "brand_name": "test1",
        "generic_name": "test2",
        "dosage_form": DosageForm.TABLET,
    }
    resp = await test_client.post(base_url, json=data)

    mock.assert_awaited_once_with(CreateMedication(**data))
    assert resp.status_code == status_codes.HTTP_201_CREATED
    assert Medication.model_validate(MedicationJSONResponse(**resp.json()))


@patch.object(Service, "create")
async def test_add_medication_with_invalid_name_type_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    data = {
        "brand_name": 13,
        "generic_name": "test2",
        "dosage_form": DosageForm.TABLET,
    }
    resp = await test_client.post(base_url, json=data)

    mock.assert_not_awaited()
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST


@patch.object(Service, "create")
async def test_add_medication_with_invalid_dosage_form_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    data = {
        "brand_name": "test1",
        "generic_name": "test2",
        "dosage_form": "INVALID",
    }
    resp = await test_client.post(base_url, json=data)

    mock.assert_not_awaited()
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST


@patch.object(Service, "create")
async def test_add_medication_with_generic_name_too_long_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    data = {
        "brand_name": "test1",
        "generic_name": "a" * (MEDICATION_GENERIC_NAME_LENGTH + 1),
        "dosage_form": "INVALID",
    }
    resp = await test_client.post(base_url, json=data)

    mock.assert_not_awaited()
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST


@patch.object(Service, "create")
async def test_add_medication_with_extra_data_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    data = {
        "brand_name": "test1",
        "generic_name": "test2",
        "dosage_form": DosageForm.TABLET,
        "extra": "extra",
    }
    resp = await test_client.post(base_url, json=data)

    mock.assert_not_awaited()
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST


@patch.object(Service, "create")
async def test_add_medication_with_empty_payload_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.post(base_url, json={})

    mock.assert_not_awaited()
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST


@patch.object(Service, "create", side_effect=DuplicateError)
async def test_add_medication_with_duplicate_payload_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    data = {
        "brand_name": "test1",
        "generic_name": "test2",
        "dosage_form": DosageForm.TABLET,
    }
    resp = await test_client.post(base_url, json=data)

    mock.assert_awaited_once()
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST


@patch.object(Service, "create", side_effect=InvalidArgumentTypeError)
async def test_add_medication_with_invalid_argument_type_return_422_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    data = {
        "brand_name": "test1",
        "generic_name": "test2",
        "dosage_form": DosageForm.TABLET,
    }
    resp = await test_client.post(base_url, json=data)

    mock.assert_awaited_once()
    assert resp.status_code == status_codes.HTTP_422_UNPROCESSABLE_ENTITY


@patch.object(Service, "create", side_effect=ExtraArgumentError)
async def test_add_medication_with_extra_argument_return_422_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    data = {
        "brand_name": "test1",
        "generic_name": "test2",
        "dosage_form": DosageForm.TABLET,
    }
    resp = await test_client.post(base_url, json=data)

    mock.assert_awaited_once()
    assert resp.status_code == status_codes.HTTP_422_UNPROCESSABLE_ENTITY


@patch.object(Service, "get", return_value=medication)
async def test_get_medication_with_existing_id_return_medication_instance(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(item_url)
    mock.assert_awaited_once_with(medication_id)
    assert resp.status_code == status_codes.HTTP_200_OK
    assert Medication.model_validate(MedicationJSONResponse(**resp.json()))


@patch.object(Service, "get", return_value=None)
async def test_get_medication_with_id_does_not_exist_return_404_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(item_url)
    mock.assert_awaited_once_with(medication_id)
    assert resp.status_code == status_codes.HTTP_404_NOT_FOUND


@patch.object(Service, "get", return_value=None)
async def test_get_medication_with_negative_id_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(f"{base_url}/-1")
    mock.assert_not_awaited()
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST


@patch.object(Service, "get")
async def test_get_medication_with_invalid_id_type_return_404_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(f"{base_url}/-INVALID")
    mock.assert_not_awaited()
    assert resp.status_code == status_codes.HTTP_404_NOT_FOUND


@patch.object(Service, "update", return_value=medication)
async def test_update_medication_with_valid_partial_data_return_category_instance(
    mock: AsyncMock, test_client: AsyncTestClient
):
    payload = {"brand_name": "new_name"}
    resp = await test_client.patch(item_url, json=payload)

    mock.assert_awaited_once_with(medication_id, PatchMedication(**payload))
    assert resp.status_code == status_codes.HTTP_200_OK
    assert Medication.model_validate(MedicationJSONResponse(**resp.json()))


@patch.object(Service, "update", return_value=medication)
async def test_update_medication_with_valid_complete_data_return_category_instance(
    mock: AsyncMock, test_client: AsyncTestClient
):
    date = f"{now:%Y-%m-%d %H:%M:%S}"
    payload = {
        "brand_name": "test1",
        "generic_name": "test1",
        "dosage_form": DosageForm.TABLET,
        "producer_id": 1,
        "category_id": 1,
        "created_at": date,
        "updated_at": date,
    }
    resp = await test_client.patch(item_url, json=payload)

    assert resp.status_code == status_codes.HTTP_200_OK
    mock.assert_awaited_once_with(medication_id, PatchMedication(**payload))
    assert Medication.model_validate(MedicationJSONResponse(**resp.json()))


@patch.object(Service, "update", return_value=None)
async def test_update_medication_with_id_does_not_exist_return_404_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    payload = {"brand_name": "test1"}
    resp = await test_client.patch(item_url, json=payload)

    mock.assert_awaited_once_with(medication_id, PatchMedication(**payload))
    assert resp.status_code == status_codes.HTTP_404_NOT_FOUND
    body = resp.json()
    assert "detail" in body and "status_code" in body


@patch.object(Service, "update")
async def test_update_producer_with_brand_name_too_long_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    long_name = "a" * (MEDICATION_BRAND_NAME_LENGTH + 1)
    resp = await test_client.patch(item_url, json={"brand_name": long_name})
    mock.assert_not_awaited()
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    body = resp.json()
    assert "detail" in body and "status_code" in body


@patch.object(Service, "update")
async def test_update_medication_with_invalid_dosage_form_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.patch(item_url, json={"dosage_form": "INVALID"})
    mock.assert_not_awaited()
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    body = resp.json()
    assert "detail" in body and "status_code" in body


@patch.object(Service, "update")
async def test_update_medication_with_negative_producer_id_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.patch(item_url, json={"producer_id": -22})
    mock.assert_not_awaited()
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    body = resp.json()
    assert "detail" in body and "status_code" in body


@patch.object(Service, "update")
async def test_update_medication_with_extra_payload_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.patch(item_url, json={"extra": "extra"})
    mock.assert_not_awaited()
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    body = resp.json()
    assert "detail" in body and "status_code" in body


@patch.object(Service, "update", side_effect=DuplicateError)
async def test_update_medication_with_duplicate_payload_return_409_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.patch(item_url, json={"brand_name": "test1"})
    mock.assert_awaited_once()
    assert resp.status_code == status_codes.HTTP_409_CONFLICT
    body = resp.json()
    assert "detail" in body and "status_code" in body


@patch.object(Service, "update")
async def test_update_medication_with_empty_payload_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    mock.assert_not_awaited()
    resp = await test_client.patch(item_url, json={})
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    body = resp.json()
    assert "detail" in body and "status_code" in body


@patch.object(Service, "update", side_effect=InvalidArgumentTypeError)
async def test_update_medication_with_invalid_argument_type_return_422_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.patch(item_url, json={"brand_name": "test1"})
    mock.assert_awaited_once()
    assert resp.status_code == status_codes.HTTP_422_UNPROCESSABLE_ENTITY


@patch.object(Service, "update", side_effect=ExtraArgumentError)
async def test_update_medication_with_extra_argument_return_422_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.patch(item_url, json={"brand_name": "test1"})
    mock.assert_awaited_once()
    assert resp.status_code == status_codes.HTTP_422_UNPROCESSABLE_ENTITY


@patch.object(Service, "delete", return_value=True)
async def test_delete(mock: AsyncMock, test_client: AsyncTestClient):
    resp = await test_client.delete(item_url)
    mock.assert_awaited_once_with(medication_id)
    assert resp.status_code == status_codes.HTTP_204_NO_CONTENT


@patch.object(Service, "delete", return_value=True)
async def test_delete_medication_with_existing_id_return_204_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.delete(item_url)
    mock.assert_awaited_once_with(medication_id)
    assert resp.status_code == status_codes.HTTP_204_NO_CONTENT


@patch.object(Service, "delete", return_value=False)
async def test_delete_medication_with_id_does_not_exist_return_404_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.delete(item_url)
    mock.assert_awaited_once_with(medication_id)
    assert resp.status_code == status_codes.HTTP_404_NOT_FOUND


@patch.object(Service, "delete")
async def test_delete_medication_with_negative_id_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.delete(f"{base_url}/-1")
    mock.assert_not_awaited()
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
