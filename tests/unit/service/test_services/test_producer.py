from unittest.mock import AsyncMock, patch

import pytest

from src.data.models import Producer as DBProducer
from src.data.repository import ProducerRepository as Repo
from src.domain.models import Producer
from src.service.services import ProducerService as Service
from src.utils import now as now_

pytestmark = pytest.mark.asyncio

now = now_()
producer_id = 1
producer = DBProducer(pk=1, name="test1", created_at=now, updated_at=now)
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
async def test_list_with_zero_limit_raises_value_error(
    mock: AsyncMock,
):
    await Service(None).list_items(limit=0, offset=1)
    mock.assert_not_awaited()


@pytest.mark.xfail(raises=ValueError, strict=True)
@patch.object(Repo, "fetch_many")
async def test_list_with_limit_too_high_raises_value_error(
    mock: AsyncMock,
):
    from src.settings import settings

    await Service(None).list_items(limit=settings.PAGINATION_LIMIT + 1, offset=1)
    mock.assert_not_awaited()


@pytest.mark.xfail(raises=ValueError, strict=True)
@patch.object(Repo, "fetch_many")
async def test_list_with_negative_offset_raises_value_error(
    mock: AsyncMock,
):
    await Service(None).list_items(limit=1, offset=-1)
    mock.assert_not_awaited()


@patch.object(Repo, "fetch_one_by_pk", return_value=producer)
async def test_get_return_producer_object(mock: AsyncMock):
    p = await Service(None).get(producer_id)
    assert isinstance(p, Producer)
