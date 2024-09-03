from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from litestar import status_codes
from litestar.testing import AsyncTestClient

from src.domain.models import MedicationProducer
from src.restapi.app import app
from src.service.services import ProducerService
from src.utils import now as now_
from tests.conftest import DEFAULT_LIMIT

pytestmark = pytest.mark.asyncio

now = now_()
producer = MedicationProducer(
    producer_id=1, name="test1", created_at=now, updated_at=now
)
default_filters = {
    "pk": None,
    "name": None,
    "created_before": None,
    "created_after": None,
    "updated_before": None,
    "updated_after": None,
}


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def test_client():
    async with AsyncTestClient(app=app) as client:
        yield client


class TestProducerHandlers:
    list_create_url = "/api/v1/producers"

    @patch.object(ProducerService, "get_producers", return_value=[producer])
    async def test_list_producers_without_query_args_uses_default_values(
        self, mock: AsyncMock, test_client: AsyncTestClient
    ):
        resp = await test_client.get(self.list_create_url)

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
        assert all(MedicationProducer.model_validate(item) for item in body)

    @patch.object(ProducerService, "get_producers", return_value=[producer])
    async def test_list_producers_with_query_args_uses_provided_args(
        self, mock: AsyncMock, test_client: AsyncTestClient
    ):
        from datetime import datetime as dt

        limit = 10
        offset = 5
        datestring = "2015-01-16T16:52:00"
        date = dt.fromisoformat(datestring)
        names = ["FirstName", "SecondName"]
        ids = [1, 2, 3]
        url = (
            f"{self.list_create_url}?limit={limit}&offset={offset}"
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
        assert all(MedicationProducer.model_validate(item) for item in body)

    @patch.object(ProducerService, "get_producers", return_value=[])
    async def test_list_producers_with_empty_service_response(
        self, mock: AsyncMock, test_client: AsyncTestClient
    ):
        resp = await test_client.get(self.list_create_url)

        assert resp.status_code == status_codes.HTTP_200_OK
        mock.assert_awaited_once()
        assert resp.json() == []

    @patch.object(ProducerService, "get_producers", return_value=[producer])
    async def test_list_producers_with_extra_query_arg_is_ignored(
        self, mock: AsyncMock, test_client: AsyncTestClient
    ):
        resp = await test_client.get(f"{self.list_create_url}?extra=extra1")

        assert resp.status_code == status_codes.HTTP_200_OK
        mock.assert_awaited_once()
        assert "extra" not in mock.await_args.kwargs

    @patch.object(ProducerService, "get_producers")
    async def test_list_producers_with_invalid_query_arg_type_returns_error(
        self, mock: AsyncMock, test_client: AsyncTestClient
    ):
        resp = await test_client.get(f"{self.list_create_url}?createdBefore=hello")

        assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
        mock.assert_not_awaited()
        body = resp.json()
        assert set(body.keys()) == {"status_code", "detail", "extra"}

    @patch.object(ProducerService, "get_producers")
    async def test_list_producers_with_negative_limit_return_error(
        self, mock: AsyncMock, test_client: AsyncTestClient
    ):
        resp = await test_client.get(f"{self.list_create_url}?limit=-14")

        assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
        mock.assert_not_awaited()
        body = resp.json()
        assert set(body.keys()) == {"status_code", "detail", "extra"}

    @patch.object(ProducerService, "get_producers")
    async def test_list_producers_with_limit_too_high_return_error(
        self, mock: AsyncMock, test_client: AsyncTestClient
    ):
        resp = await test_client.get(f"{self.list_create_url}?limit=200")

        assert resp.status_code == status_codes.HTTP_400_BAD_REQUEST
        mock.assert_not_awaited()
        body = resp.json()
        assert set(body.keys()) == {"status_code", "detail", "extra"}
