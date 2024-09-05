from datetime import datetime
from typing import Annotated

from litestar import Request, Router, delete, get, patch, post, status_codes
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotFoundException
from litestar.params import Dependency, Parameter

from service.services import ProducerService
from src.data.providers import provide_db_session
from src.domain.models import CreateProducer, PatchProducer, Producer
from src.service.exceptions import (
    DuplicateError,
    ExtraArgumentError,
    InvalidArgumentTypeError,
)
from src.service.providers import provide_producer_service

from ..dto import CreateProducerDTO, PatchProducerDTO, ProducerDTO
from ..query_params import (
    CreatedAfterParam,
    CreatedBeforeParam,
    IdsParam,
    NamesParam,
    OffsetParam,
    PageSizeParam,
    UpdatedAfterParam,
    UpdatedBeforeParam,
)


@get("/", return_dto=ProducerDTO)
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
) -> list[Producer]:
    return await service.list(
        limit=limit,
        offset=offset,
        created_before=created_before,
        created_after=created_after,
        updated_before=updated_before,
        updated_after=updated_after,
        pk=pks,
        name=names,
    )


@post("/", dto=CreateProducerDTO, return_dto=ProducerDTO)
async def add_producer(
    request: Request,
    service: Annotated[ProducerService, Dependency(skip_validation=True)],
    data: CreateProducer,
) -> Producer:
    try:
        producer = await service.create(data)
    except DuplicateError as err:
        request.logger.info(
            f"Attempt to create duplicate instance failed with error: {err}"
        )
        raise HTTPException(
            status_code=status_codes.HTTP_400_BAD_REQUEST,
            detail="Producer with provided data already exists",
        )
    except InvalidArgumentTypeError as err:
        request.logger.info(
            f"Invalid argument type detected, causing db query fail with error: {err}"
        )
        raise HTTPException(
            status_code=status_codes.HTTP_400_BAD_REQUEST,
            detail=(
                "At least one of the provided arguments has incompatible "
                "type with database representation"
            ),
        )
    except ExtraArgumentError as err:
        request.logger.info(
            f"Extra argument detected, causing db query fail with error: {err}"
        )
        raise HTTPException(
            status_code=status_codes.HTTP_400_BAD_REQUEST,
            detail=(
                "At least one of the provided arguments does not belong to "
                "the database representation"
            ),
        )

    return producer


@get("/{producer_id: int}", return_dto=ProducerDTO, raises=[NotFoundException])
async def get_producer(
    service: Annotated[ProducerService, Dependency(skip_validation=True)],
    producer_id: Annotated[int, Parameter(int, gt=0, required=True)],
) -> Producer:
    producer = await service.get(producer_id)
    if not producer:
        raise NotFoundException(
            detail=f"Producer with id {producer_id} not found",
        )
    return producer


@patch(
    "/{producer_id: int}",
    dto=PatchProducerDTO,
    return_dto=ProducerDTO,
    raises=[NotFoundException],
)
async def update_producer(
    request: Request,
    service: Annotated[ProducerService, Dependency(skip_validation=True)],
    producer_id: Annotated[int, Parameter(int, gt=0, required=True)],
    data: PatchProducer,
) -> Producer:
    try:
        producer = await service.update(producer_id, data)
    except DuplicateError as err:
        request.logger.info(
            f"Attempt to update producer with data already occupied. "
            f"?PK={producer_id}, ?DATA={data}, ?ERROR={err}"
        )
        raise HTTPException(
            status_code=status_codes.HTTP_409_CONFLICT,
            detail="Producer with provided data already exists",
        )
    except InvalidArgumentTypeError as err:
        request.logger.info(
            f"Invalid argument type detected, causing db query fail with error: {err}."
            f"?PK={producer_id}, ?DATA={data}."
        )
        raise HTTPException(
            status_code=status_codes.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "At least one of the provided arguments has incompatible "
                "type with database representation"
            ),
        )
    except ExtraArgumentError as err:
        request.logger.info(
            f"Extra argument detected, causing db query fail with error: {err}"
            f"?PK={producer_id}, ?DATA={data}."
        )
        raise HTTPException(
            status_code=status_codes.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "At least one of the provided arguments does not belong to "
                "the database representation"
            ),
        )

    if not producer:
        raise NotFoundException(detail=f"Producer with id {producer_id} not found")

    return producer


@delete("/{producer_id: int}", raises=[NotFoundException])
async def delete_producer(
    service: Annotated[ProducerService, Dependency(skip_validation=True)],
    producer_id: Annotated[int, Parameter(int, gt=0, required=True)],
) -> None:
    deleted = await service.delete(producer_id)
    if not deleted:
        raise NotFoundException(detail=f"Producer with id {producer_id} not found")


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
