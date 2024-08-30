from datetime import datetime

from litestar import Router, delete, get, patch, post
from litestar.di import Provide
from litestar.dto import DataclassDTO

from src.data.providers import provide_db_session
from src.domain.models import MedicationProducer
from src.service.producer import ProducerService
from src.service.providers import provide_producer_service

from ..query_filters import list_producers_deps


class ReadProducer(DataclassDTO[MedicationProducer]): ...


@get(
    "/",
    return_dto=ReadProducer,
    dependencies=list_producers_deps(),
)
async def list_producers(
    service: ProducerService,
    page_size: int,
    skip: int,
    created: dict[str, datetime | None],
    updated: dict[str, datetime | None],
    id_array: list[int] | None,
    name_array: list[str] | None,
) -> list[ReadProducer]:
    filters = {"pk": id_array, "name": name_array}
    filters = filters | created | updated
    return await service.get_producers(limit=page_size, offset=skip, filters=filters)


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
