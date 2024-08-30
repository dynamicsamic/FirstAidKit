from datetime import datetime

from litestar.di import Provide
from litestar.openapi.spec import Example
from litestar.params import Parameter

from src.settings import settings


def limit_filter(
    limit: int = Parameter(
        query="limit", default=settings.ITEMS_PER_PAGE, required=False, gt=0
    )
) -> int:
    return limit


def offset_filter(
    offset: int = Parameter(query="offset", default=0, required=False, ge=0)
) -> int:
    return offset


def created_filter(
    created_before: datetime | None = Parameter(
        query="createdBefore",
        default=None,
        required=False,
        examples=[Example(value="2015-01-16T16:52:00")],
    ),
    created_after: datetime | None = Parameter(
        query="createdAfter",
        default=None,
        required=False,
        examples=[Example(value="2015-01-16T16:52:00")],
    ),
) -> dict[str, datetime | None]:
    return {"created_before": created_before, "created_after": created_after}


def updated_filter(
    updated_before: datetime | None = Parameter(
        query="updatedBefore",
        default=None,
        required=False,
        examples=[Example(value="2015-01-16T16:52:00")],
    ),
    updated_after: datetime | None = Parameter(
        query="updatedAfter",
        default=None,
        required=False,
        examples=[Example(value="2015-01-16T16:52:00")],
    ),
) -> dict[str, datetime | None]:
    return {"updated_before": updated_before, "updated_after": updated_after}


def ids_filter(
    ids: list[int] | None = Parameter(
        query="ids",
        default=None,
        required=False,
        examples=[Example(value="2&ids=4")],
    )
) -> list[int] | None:
    return ids


def names_filter(
    names: list[str] | None = Parameter(
        query="names",
        default=None,
        required=False,
        examples=[Example(value="FirstName&names=AnotherName")],
    ),
) -> list[str] | None:
    return names


def list_producers_deps() -> dict[str, Provide]:
    return {
        "page_size": Provide(limit_filter, sync_to_thread=False),
        "skip": Provide(offset_filter, sync_to_thread=False),
        "created": Provide(created_filter, sync_to_thread=False),
        "updated": Provide(updated_filter, sync_to_thread=False),
        "id_array": Provide(ids_filter, sync_to_thread=False),
        "name_array": Provide(names_filter, sync_to_thread=False),
    }
