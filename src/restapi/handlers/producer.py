from datetime import datetime
from typing import Annotated

from litestar import Router, delete, get, patch, post
from litestar.contrib.pydantic import PydanticDTO
from litestar.di import Provide
from litestar.params import Dependency

from service.services import ProducerService
from src.data.providers import provide_db_session
from src.domain.models import MedicationProducer
from src.service.providers import provide_producer_service

from ..query_filters import (
    CreatedAfterParam,
    CreatedBeforeParam,
    IdsParam,
    NamesParam,
    OffsetParam,
    PageSizeParam,
    UpdatedAfterParam,
    UpdatedBeforeParam,
)

ProducerDTO = PydanticDTO[MedicationProducer]


@get("/")
async def list_producers(
    service: Annotated[ProducerService, Dependency(skip_validation=True)],
    limit: int | None = PageSizeParam,
    offset: int | None = OffsetParam,
    created_before: datetime | None = CreatedBeforeParam,
    created_after: datetime | None = CreatedAfterParam,
    updated_before: datetime | None = UpdatedBeforeParam,
    updated_after: datetime | None = UpdatedAfterParam,
    pks: list[int] | None = IdsParam,
    names: list[str] | None = NamesParam,
) -> list[MedicationProducer]:
    return await service.get_producers(
        limit=limit,
        offset=offset,
        created_before=created_before,
        created_after=created_after,
        updated_before=updated_before,
        updated_after=updated_after,
        pk=pks,
        name=names,
    )


@post("/")
async def add_producer() -> None:
    pass


@get("/{prod_id: int}")
async def get_producer() -> None:
    pass


@patch("/{prod_id: int}")
async def update_producer() -> None:
    pass


@delete("/{prod_id: int}")
async def delete_producer() -> None:
    pass


router = Router(
    path="/producers",
    route_handlers=[
        list_producers,
        add_producer,
        get_producer,
        update_producer,
        delete_producer,
    ],
    dependencies={
        "db_session": Provide(provide_db_session),
        "service": Provide(provide_producer_service),
    },
)
