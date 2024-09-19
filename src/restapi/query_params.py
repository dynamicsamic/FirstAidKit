from datetime import datetime
from typing import Any

from litestar.openapi.spec import Example
from litestar.params import Parameter

from src.domain.types import DosageForm
from src.settings import settings


def datetime_param(query: str, **kwargs: Any) -> Parameter:
    """Generate datetime-type query parameter."""
    return Parameter(
        datetime,
        query=query,
        required=False,
        examples=[Example(summary="example-1", value="2015-01-16T16:52:00")],
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
    examples=[Example(summary="example-1", value="ids=FirstName&ids=AnotherName")],
)
NamesParam = Parameter(
    required=False,
    default=None,
    examples=[Example(summary="example-1", value="names=FirstName&names=AnotherName")],
)
BrandNamesParam = Parameter(
    list[str],
    query="brandNames",
    required=False,
    default=None,
    examples=[Example(summary="example-1", value="brandNames=CoolTabs300mg")],
)
GenericNamesParam = Parameter(
    list[str],
    query="genericNames",
    required=False,
    default=None,
    examples=[
        Example(
            summary="example-1",
            value="genericNames=NikotinAcid&genericNames=GreenMixture",
        )
    ],
)
DosageFormsParam = Parameter(
    list[DosageForm],
    query="dosageForms",
    required=False,
    default=None,
    examples=[
        Example(summary="example-1", value="dosageForms=tablet&dosageForms=mixture")
    ],
)
ProducerIdsParam = Parameter(
    list[int],
    query="producerIds",
    required=False,
    default=None,
    examples=[Example(summary="example-1", value="producerIds=1&producerIds=2")],
)
CategoryIdsParam = Parameter(
    list[int],
    query="categoryIds",
    required=False,
    default=None,
    examples=[Example(summary="example-1", value="categoryIds=1&categoryIds=2")],
)
LocationsParam = Parameter(
    list[str],
    query="locations",
    required=False,
    default=None,
    examples=[Example(summary="example-1", value="locations=1&locations=2")],
)
