from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.exc import CompileError, DBAPIError, IntegrityError

from src.data.models import Category as DBCategory
from src.data.repository import CategoryRepository as Repo
from src.domain.models import Category, CreateCategory
from src.service.exceptions import (
    DuplicateError,
    ExtraArgumentError,
    InvalidArgumentTypeError,
)
from src.service.services import CategoryService as Service
from src.utils import now as now_

from .mock_data import MockCategory

pytestmark = pytest.mark.asyncio


now = now_()
category_id = 1
category = DBCategory(pk=category_id, name="test1", created_at=now, updated_at=now)
categories = [category for _ in range(3)]


@patch.object(Repo, "fetch_many", return_value=categories)
async def test_list_without_filters_return_list_of_categories(
    mock: AsyncMock,
):
    limit, offset = 10, 11
    r = await Service(None).list_items(limit=limit, offset=offset)
    mock.assert_awaited_once_with(limit=limit, offset=offset, order_by=[DBCategory.pk])
    assert isinstance(r, list)
    assert all(isinstance(item, Category) for item in r)


@patch.object(Repo, "fetch_many", return_value=categories)
async def test_list_with_some_filters_return_list_of_categories(
    mock: AsyncMock,
):
    limit, offset = 10, 11
    pks = [1, 2, 3]
    r = await Service(None).list_items(limit=limit, offset=offset, pk=pks)
    mock.assert_awaited_once()
    args, kwargs = mock.await_args
    assert kwargs == {"limit": limit, "offset": offset, "order_by": [DBCategory.pk]}
    assert args[0].compare(DBCategory.pk.in_(pks))
    assert isinstance(r, list)
    assert all(isinstance(item, Category) for item in r)


@patch.object(Repo, "fetch_many", return_value=categories)
async def test_list_with_all_filters_return_list_of_categories(
    mock: AsyncMock,
):
    limit, offset = 10, 11
    pks = [1, 2, 3]
    names = ["test1", "test2"]
    created_before = now_()
    created_after = now_()
    updated_before = now_()
    updated_after = now_()
    r = await Service(None).list_items(
        limit=limit,
        offset=offset,
        pk=pks,
        name=names,
        created_before=created_before,
        created_after=created_after,
        updated_before=updated_before,
        updated_after=updated_after,
    )
    mock.assert_awaited_once()
    args, kwargs = mock.await_args
    assert kwargs == {"limit": limit, "offset": offset, "order_by": [DBCategory.pk]}
    assert args[0].compare(DBCategory.created_at < created_before)
    assert args[1].compare(DBCategory.created_at > created_after)
    assert args[2].compare(DBCategory.updated_at < updated_before)
    assert args[3].compare(DBCategory.updated_at > updated_after)
    assert args[4].compare(DBCategory.pk.in_(pks))
    assert args[5].compare(DBCategory.name.in_(names))
    assert isinstance(r, list)
    assert all(isinstance(item, Category) for item in r)


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
    assert all(isinstance(item, Category) for item in r)


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


@patch.object(Repo, "insert_one", return_value=category)
async def test_create_with_valid_payload_return_created_instance(mock: AsyncMock):
    data = {"name": "test"}
    r = await Service(None).create(CreateCategory(**data))
    mock.assert_awaited_once_with(**data)
    assert isinstance(r, Category)


@pytest.mark.xfail(raises=ExtraArgumentError, strict=True)
@patch.object(Repo, "insert_one", side_effect=CompileError)
async def test_create_with_extra_attribute_raises_extra_arg_error(_):
    await Service(None).create(MockCategory(**{"name": "test", "extra": "extra"}))


@pytest.mark.xfail(raises=InvalidArgumentTypeError, strict=True)
@patch.object(Repo, "insert_one", side_effect=DBAPIError(None, None, Exception))
async def test_create_with_invalid_attribute_type_raises_invalid_arg_type_error(_):
    await Service(None).create(MockCategory(name=1234))


@pytest.mark.xfail(raises=ValueError, strict=True)
@patch.object(Repo, "insert_one")
async def test_create_with_empty_payload_raises_value_error(_):
    await Service(None).create(MockCategory())


@pytest.mark.xfail(raises=DuplicateError, strict=True)
@patch.object(Repo, "insert_one", side_effect=IntegrityError(None, None, Exception))
async def test_create_duplicate_payload_raises_duplicate_error(_):
    await Service(None).create(MockCategory(name="test"))


@patch.object(Repo, "fetch_one_by_pk", return_value=category)
async def test_get_with_existing_id_return_category_object(mock: AsyncMock):
    r = await Service(None).get(category_id)
    mock.assert_awaited_once_with(pk=category_id)
    assert isinstance(r, Category)


@patch.object(Repo, "fetch_one_by_pk", return_value=None)
async def test_get_with_id_does_not_exist_return_none(mock: AsyncMock):
    r = await Service(None).get(category_id)
    mock.assert_awaited_once_with(pk=category_id)
    assert r is None


@patch.object(Repo, "update_one_by_pk", return_value=category)
async def test_update_with_valid_partial_data_return_category_object(mock: AsyncMock):
    data = {"created_at": now}
    r = await Service(None).update(category_id, MockCategory(**data))
    mock.assert_awaited_once_with(category_id, **data)
    assert isinstance(r, Category)


@patch.object(Repo, "update_one_by_pk", return_value=category)
async def test_update_with_valid_complete_data_return_category_object(mock: AsyncMock):
    data = {"name": "test", "created_at": now, "updated_at": now}
    r = await Service(None).update(category_id, MockCategory(**data))
    mock.assert_awaited_once_with(category_id, **data)
    assert isinstance(r, Category)


@patch.object(Repo, "update_one_by_pk", return_value=None)
async def test_update_with_id_does_not_exist_return_none(mock: AsyncMock):
    data = {"name": "test"}
    r = await Service(None).update(category_id, MockCategory(**data))
    mock.assert_awaited_once_with(category_id, **data)
    assert r is None


@pytest.mark.xfail(raises=ExtraArgumentError, strict=True)
@patch.object(Repo, "update_one_by_pk", side_effect=CompileError)
async def test_update_with_extra_attribute_raises_(mock: AsyncMock):
    await Service(None).update(category_id, MockCategory(extra="extra"))


@pytest.mark.xfail(raises=InvalidArgumentTypeError, strict=True)
@patch.object(Repo, "update_one_by_pk", side_effect=DBAPIError(None, None, Exception))
async def test_update_with_invalid_attribute_type_raises_invalid_arg_type_error(
    mock: AsyncMock,
):
    await Service(None).update(category_id, MockCategory(name=4773))


@pytest.mark.xfail(raises=DuplicateError, strict=True)
@patch.object(
    Repo, "update_one_by_pk", side_effect=IntegrityError(None, None, Exception)
)
async def test_update_with_duplicate_payload_raises_duplicate_error(mock: AsyncMock):
    await Service(None).update(category_id, MockCategory(name="test"))


@pytest.mark.xfail(raises=ValueError, strict=True)
@patch.object(Repo, "update_one_by_pk")
async def test_update_with_empty_data_raises_value_errror(mock: AsyncMock):
    await Service(None).update(category_id, MockCategory())


@patch.object(Repo, "delete", return_value=1)
async def test_delete_existing_category_return_true(mock: AsyncMock):
    r = await Service(None).delete(category_id)
    mock.assert_awaited_once()
    db_filter, *_ = mock.await_args.args
    assert db_filter.compare(DBCategory.pk == category_id)
    assert r is True


@patch.object(Repo, "delete", return_value=0)
async def test_delete_category_does_not_exist_return_false(mock: AsyncMock):
    r = await Service(None).delete(category_id)
    mock.assert_awaited_once()
    db_filter, *_ = mock.await_args.args
    assert db_filter.compare(DBCategory.pk == category_id)
    assert r is False
