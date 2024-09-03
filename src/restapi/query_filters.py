from datetime import datetime
from typing import Any

from litestar.openapi.spec import Example
from litestar.params import Parameter

from src.settings import settings


def datetime_param(query: str, **kwargs: Any) -> Parameter:
    return Parameter(
        datetime,
        query=query,
        required=False,
        examples=[Example(value="2015-01-16T16:52:00")],
        **kwargs,
    )


OffsetParam = Parameter(required=False, ge=0, default=0)
CreatedBeforeParam = datetime_param(query="createdBefore")
CreatedAfterParam = datetime_param(query="createdAfter")
UpdatedBeforeParam = datetime_param(query="updatedBefore")
UpdatedAfterParam = datetime_param(query="updatedAfter")
PageSizeParam = Parameter(
    required=False,
    gt=0,
    le=settings.PAGINATION_LIMIT,
    default=settings.ITEMS_PER_PAGE,
)
IdsParam = Parameter(
    query="ids",
    required=False,
    default=None,
    examples=[Example(value="FirstName&names=AnotherName")],
)
NamesParam = Parameter(
    required=False,
    default=None,
    examples=[Example(value="FirstName&names=AnotherName")],
)
