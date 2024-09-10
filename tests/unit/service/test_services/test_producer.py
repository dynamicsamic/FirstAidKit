from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.exc import CompileError, DBAPIError, IntegrityError

from src.data.models import Producer as DBProducer
from src.data.repository import ProducerRepository as Repo
from src.domain.models import Producer
from src.service.exceptions import (
    DuplicateError,
    ExtraArgumentError,
    InvalidArgumentTypeError,
)
from src.service.services import ProducerService as Service
from src.utils import now as now_

from .mock_data import MockProducer

pytestmark = pytest.mark.asyncio


now = now_()
producer_id = 1
producer = DBProducer(pk=producer_id, name="test1", created_at=now, updated_at=now)
producers = [producer for _ in range(3)]


@patch.object(Repo, "fetch_many", return_value=producers)
async def test_list_without_filters_return_list_of_producers(
    mock: AsyncMock,
):
    limit, offset = 10, 11
    r = await Service(None).list_items(limit=limit, offset=offset)
    mock.assert_awaited_once_with(limit=limit, offset=offset, order_by=[DBProducer.pk])
    assert isinstance(r, list)
    assert all(isinstance(item, Producer) for item in r)


@patch.object(Repo, "fetch_many", return_value=producers)
async def test_list_with_some_filters_return_list_of_producers(
    mock: AsyncMock,
):
    limit, offset = 10, 11
    pks = [1, 2, 3]
    r = await Service(None).list_items(limit=limit, offset=offset, pk=pks)
    mock.assert_awaited_once()
    args, kwargs = mock.await_args
    assert kwargs == {"limit": limit, "offset": offset, "order_by": [DBProducer.pk]}
    assert args[0].compare(DBProducer.pk.in_(pks))
    assert isinstance(r, list)
    assert all(isinstance(item, Producer) for item in r)


@patch.object(Repo, "fetch_many", return_value=producers)
async def test_list_with_all_filters_return_list_of_producers(
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
    assert kwargs == {"limit": limit, "offset": offset, "order_by": [DBProducer.pk]}
    assert args[0].compare(DBProducer.created_at < created_before)
    assert args[1].compare(DBProducer.created_at > created_after)
    assert args[2].compare(DBProducer.updated_at < updated_before)
    assert args[3].compare(DBProducer.updated_at > updated_after)
    assert args[4].compare(DBProducer.pk.in_(pks))
    assert args[5].compare(DBProducer.name.in_(names))
    assert isinstance(r, list)
    assert all(isinstance(item, Producer) for item in r)


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
    assert all(isinstance(item, Producer) for item in r)


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


@patch.object(Repo, "insert_one", return_value=producer)
async def test_create_with_valid_payload_return_created_instance(mock: AsyncMock):
    data = {"name": "test"}
    r = await Service(None).create(MockProducer(**data))
    mock.assert_awaited_once_with(**data)
    assert isinstance(r, Producer)


@pytest.mark.xfail(raises=ExtraArgumentError, strict=True)
@patch.object(Repo, "insert_one", side_effect=CompileError)
async def test_create_with_extra_attribute_raises_extra_arg_error(_):
    await Service(None).create(MockProducer(**{"name": "test", "extra": "extra"}))


@pytest.mark.xfail(raises=InvalidArgumentTypeError, strict=True)
@patch.object(Repo, "insert_one", side_effect=DBAPIError(None, None, Exception))
async def test_create_with_invalid_attribute_type_raises_invalid_arg_type_error(_):
    await Service(None).create(MockProducer(name=1234))


@pytest.mark.xfail(raises=ValueError, strict=True)
@patch.object(Repo, "insert_one")
async def test_create_with_empty_payload_raises_value_error(_):
    await Service(None).create(MockProducer())


@pytest.mark.xfail(raises=DuplicateError, strict=True)
@patch.object(Repo, "insert_one", side_effect=IntegrityError(None, None, Exception))
async def test_create_duplicate_payload_raises_duplicate_error(_):
    await Service(None).create(MockProducer(name="test"))


@patch.object(Repo, "fetch_one_by_pk", return_value=producer)
async def test_get_with_existing_id_return_producer_object(mock: AsyncMock):
    r = await Service(None).get(producer_id)
    mock.assert_awaited_once_with(pk=producer_id)
    assert isinstance(r, Producer)


@patch.object(Repo, "fetch_one_by_pk", return_value=None)
async def test_get_with_id_does_not_exist_return_none(mock: AsyncMock):
    r = await Service(None).get(producer_id)
    mock.assert_awaited_once_with(pk=producer_id)
    assert r is None


@patch.object(Repo, "update_one_by_pk", return_value=producer)
async def test_update_with_valid_partial_data_return_producer_object(mock: AsyncMock):
    data = {"created_at": now}
    r = await Service(None).update(producer_id, MockProducer(**data))
    mock.assert_awaited_once_with(producer_id, **data)
    assert isinstance(r, Producer)


@patch.object(Repo, "update_one_by_pk", return_value=producer)
async def test_update_with_valid_complete_data_return_producer_object(mock: AsyncMock):
    data = {"name": "test", "created_at": now, "updated_at": now}
    r = await Service(None).update(producer_id, MockProducer(**data))
    mock.assert_awaited_once_with(producer_id, **data)
    assert isinstance(r, Producer)


@patch.object(Repo, "update_one_by_pk", return_value=None)
async def test_update_with_id_does_not_exist_return_none(mock: AsyncMock):
    data = {"name": "test"}
    r = await Service(None).update(producer_id, MockProducer(**data))
    mock.assert_awaited_once_with(producer_id, **data)
    assert r is None


@pytest.mark.xfail(raises=ExtraArgumentError, strict=True)
@patch.object(Repo, "update_one_by_pk", side_effect=CompileError)
async def test_update_with_extra_attribute_raises_(mock: AsyncMock):
    await Service(None).update(producer_id, MockProducer(extra="extra"))


@pytest.mark.xfail(raises=InvalidArgumentTypeError, strict=True)
@patch.object(Repo, "update_one_by_pk", side_effect=DBAPIError(None, None, Exception))
async def test_update_with_invalid_attribute_type_raises_invalid_arg_type_error(
    mock: AsyncMock,
):
    await Service(None).update(producer_id, MockProducer(name=4773))


@pytest.mark.xfail(raises=DuplicateError, strict=True)
@patch.object(
    Repo, "update_one_by_pk", side_effect=IntegrityError(None, None, Exception)
)
async def test_update_with_duplicate_payload_raises_duplicate_error(mock: AsyncMock):
    await Service(None).update(producer_id, MockProducer(name="test"))


@pytest.mark.xfail(raises=ValueError, strict=True)
@patch.object(Repo, "update_one_by_pk")
async def test_update_with_empty_data_raises_value_errror(mock: AsyncMock):
    await Service(None).update(producer_id, MockProducer())


@patch.object(Repo, "delete", return_value=1)
async def test_delete_existing_producer_return_true(mock: AsyncMock):
    r = await Service(None).delete(producer_id)
    mock.assert_awaited_once()
    db_filter,*_ = mock.await_args.args
    assert db_filter.compare(DBProducer.pk==producer_id)
    assert r is True

@patch.object(Repo, "delete", return_value=0)
async def test_delete_producer_does_not_exist_return_false(mock: AsyncMock):
    r = await Service(None).delete(producer_id)
    mock.assert_awaited_once()
    db_filter,*_ = mock.await_args.args
    assert db_filter.compare(DBProducer.pk==producer_id)
    assert r is False