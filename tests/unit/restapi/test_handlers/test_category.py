from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from litestar import status_codes
from litestar.testing import AsyncTestClient

from src.domain.constraints import CATEGORY_NAME_LENGTH
from src.domain.models import Category, CreateCategory, PatchCategory
from src.restapi.app import app
from src.service.exceptions import DuplicateError
from src.service.services import CategoryService
from src.utils import now as now_
from tests.conftest import DEFAULT_LIMIT

from .mock_response import CategoryJSONResponse

pytestmark = pytest.mark.asyncio


now = now_()
category_id = 1
category = Category(pk=category_id, name="test1", created_at=now, updated_at=now)
categories = [category for _ in range(5)]
base_url = "/api/v1/categories"
item_url = f"{base_url}/{category_id}"


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def test_client():
    async with AsyncTestClient(app=app) as client:
        yield client


@patch.object(CategoryService, "list", return_value=categories)
async def test_list_categories_without_query_args_uses_default_values(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(base_url)

    assert resp.status_code == status_codes.HTTP_200_OK
    mock.assert_awaited_once_with(
        limit=DEFAULT_LIMIT,
        offset=0,
        pk=None,
        name=None,
        created_before=None,
        created_after=None,
        updated_before=None,
        updated_after=None,
    )
    body = resp.json()
    assert isinstance(body, list)
    assert all(Category.model_validate(CategoryJSONResponse(**item)) for item in body)


@patch.object(CategoryService, "list", return_value=categories)
async def test_list_categories_with_query_args_uses_provided_args(
    mock: AsyncMock, test_client: AsyncTestClient
):
    from datetime import datetime as dt

    limit = 10
    offset = 5
    datestring = "2015-01-16T16:52:00"
    date = dt.fromisoformat(datestring)
    names = ["FirstName", "SecondName"]
    ids = [1, 2, 3]
    url = (
        f"{base_url}?limit={limit}&offset={offset}"
        f"&createdBefore={datestring}&createdAfter={datestring}"
        f"&updatedBefore={datestring}&updatedAfter={datestring}&names={names[0]}"
        f"&names={names[1]}&ids={ids[0]}&ids={ids[1]}&ids={ids[2]}"
    )
    resp = await test_client.get(url)

    assert resp.status_code == status_codes.HTTP_200_OK
    mock.assert_awaited_once_with(
        limit=limit,
        offset=offset,
        pk=ids,
        name=names,
        created_before=date,
        created_after=date,
        updated_before=date,
        updated_after=date,
    )
    body = resp.json()
    assert isinstance(body, list)
    assert all(Category.model_validate(CategoryJSONResponse(**item)) for item in body)


@patch.object(CategoryService, "list", return_value=[])
async def test_list_categories_with_empty_service_response(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(base_url)

    assert resp.status_code == status_codes.HTTP_200_OK
    mock.assert_awaited_once()
    assert resp.json() == []


@patch.object(CategoryService, "list", return_value=categories)
async def test_list_categories_with_extra_query_arg_is_ignored(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(f"{base_url}?extra=extra1")

    assert resp.status_code == status_codes.HTTP_200_OK
    mock.assert_awaited_once()
    assert "extra" not in mock.await_args.kwargs


@patch.object(CategoryService, "list")
async def test_list_categories_with_invalid_query_arg_type_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(f"{base_url}?createdBefore=hello")

    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    mock.assert_not_awaited()
    body = resp.json()
    assert set(body.keys()) == {"status_code", "detail", "extra"}


@patch.object(CategoryService, "list")
async def test_list_categories_with_negative_limit_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(f"{base_url}?limit=-14")

    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    mock.assert_not_awaited()
    body = resp.json()
    assert set(body.keys()) == {"status_code", "detail", "extra"}


@patch.object(CategoryService, "list")
async def test_list_categories_with_limit_too_high_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(f"{base_url}?limit=200")

    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    mock.assert_not_awaited()
    body = resp.json()
    assert set(body.keys()) == {"status_code", "detail", "extra"}


@patch.object(CategoryService, "create", return_value=category)
async def test_add_category_with_valid_payload_return_created_instance(
    mock: AsyncMock, test_client: AsyncTestClient
):
    data = {"name": "hello"}
    resp = await test_client.post(base_url, json=data)

    assert resp.status_code == status_codes.HTTP_201_CREATED
    mock.assert_awaited_once_with(CreateCategory(**data))
    assert Category.model_validate(CategoryJSONResponse(**resp.json()))


@patch.object(CategoryService, "create")
async def test_add_category_with_invalid_payload_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.post(base_url, json={"name": 123})
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    mock.assert_not_awaited()


@patch.object(CategoryService, "create")
async def test_add_category_with_name_too_long_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    long_name = "a" * (CATEGORY_NAME_LENGTH + 1)
    resp = await test_client.post(base_url, json={"name": long_name})
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    mock.assert_not_awaited()


@patch.object(CategoryService, "create")
async def test_add_category_with_empty_payload_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.post(base_url, json={})
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    mock.assert_not_awaited()


@patch.object(CategoryService, "create")
async def test_add_category_with_extra_payload_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.post(base_url, json={"extra": "extra"})
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    mock.assert_not_awaited()


@patch.object(CategoryService, "create", side_effect=DuplicateError)
async def test_add_category_with_duplicate_payload_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.post(base_url, json={"name": "new_name"})
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    mock.assert_awaited_once()


@patch.object(CategoryService, "get", return_value=category)
async def test_get_category_with_existing_id_return_category_instance(
    mock: AsyncMock, test_client: AsyncTestClient
):
    category_id = 1
    resp = await test_client.get(item_url)

    assert resp.status_code == status_codes.HTTP_200_OK
    mock.assert_awaited_once_with(category_id)
    assert Category.model_validate(CategoryJSONResponse(**resp.json()))


@patch.object(CategoryService, "get", return_value=None)
async def test_get_category_with_id_does_not_exist_return_404_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(item_url)
    assert resp.status_code == status_codes.HTTP_404_NOT_FOUND
    mock.assert_awaited_once()


@patch.object(CategoryService, "get", return_value=None)
async def test_get_category_with_negative_id_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(f"{base_url}/-1")
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    mock.assert_not_awaited()


@patch.object(CategoryService, "get")
async def test_get_category_with_invalid_id_type_return_404_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.get(f"{base_url}/-INVALID")
    assert resp.status_code == status_codes.HTTP_404_NOT_FOUND
    mock.assert_not_awaited()


@patch.object(CategoryService, "update", return_value=category)
async def test_update_category_with_valid_partial_data_return_category_instance(
    mock: AsyncMock, test_client: AsyncTestClient
):
    payload = {"name": "hello"}
    resp = await test_client.patch(item_url, json=payload)

    assert resp.status_code == status_codes.HTTP_200_OK
    mock.assert_awaited_once_with(category_id, PatchCategory(**payload))
    assert Category.model_validate(CategoryJSONResponse(**resp.json()))


@patch.object(CategoryService, "update", return_value=category)
async def test_update_category_with_valid_complete_data_return_category_instance(
    mock: AsyncMock, test_client: AsyncTestClient
):
    date = f"{now:%Y-%m-%d %H:%M:%S}"
    payload = {"name": "hello", "created_at": date, "updated_at": date}
    resp = await test_client.patch(item_url, json=payload)

    assert resp.status_code == status_codes.HTTP_200_OK
    mock.assert_awaited_once_with(category_id, PatchCategory(**payload))
    assert Category.model_validate(CategoryJSONResponse(**resp.json()))


@patch.object(CategoryService, "update", return_value=None)
async def test_update_category_with_id_does_not_exist_return_404_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    payload = {"name": "hello"}
    resp = await test_client.patch(item_url, json=payload)

    assert resp.status_code == status_codes.HTTP_404_NOT_FOUND
    mock.assert_awaited_once_with(category_id, PatchCategory(**payload))
    body = resp.json()
    assert "detail" in body and "status_code" in body


@patch.object(CategoryService, "update")
async def test_update_producer_with_name_too_long_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    long_name = "a" * (CATEGORY_NAME_LENGTH + 1)
    resp = await test_client.patch(item_url, json={"name": long_name})
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    mock.assert_not_awaited()
    body = resp.json()
    assert "detail" in body and "status_code" in body


@patch.object(CategoryService, "update")
async def test_update_category_with_extra_payload_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.patch(item_url, json={"extra": "extra"})
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    mock.assert_not_awaited()
    body = resp.json()
    assert "detail" in body and "status_code" in body


@patch.object(CategoryService, "update", side_effect=DuplicateError)
async def test_update_category_with_duplicate_payload_return_409_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.patch(item_url, json={"name": "hello"})
    assert resp.status_code == status_codes.HTTP_409_CONFLICT
    mock.assert_awaited_once()
    body = resp.json()
    assert "detail" in body and "status_code" in body


@patch.object(CategoryService, "update")
async def test_update_category_with_empty_payload_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.patch(item_url, json={})
    mock.assert_not_awaited()
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
    body = resp.json()
    assert "detail" in body and "status_code" in body


@patch.object(CategoryService, "delete", return_value=True)
async def test_delete_category_with_existing_id_return_204_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    category_id = 1
    resp = await test_client.delete(item_url)

    mock.assert_awaited_once_with(category_id)
    assert resp.status_code == status_codes.HTTP_204_NO_CONTENT


@patch.object(CategoryService, "delete", return_value=False)
async def test_delete_category_with_id_does_not_exist_return_404_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    category_id = 1
    resp = await test_client.delete(item_url)

    mock.assert_awaited_once_with(category_id)
    assert resp.status_code == status_codes.HTTP_404_NOT_FOUND


@patch.object(CategoryService, "delete")
async def test_delete_category_with_negative_id_return_400_status(
    mock: AsyncMock, test_client: AsyncTestClient
):
    resp = await test_client.delete(f"{base_url}/-1")

    mock.assert_not_awaited()
    assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
