from datetime import datetime
from typing import Annotated

from litestar import Request, Router, delete, get, patch, post, status_codes
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotFoundException
from litestar.params import Dependency, Parameter

from src.data.providers import provide_db_session
from src.domain.models import (
    AidKit,
    CreateAidKit,
    Medication,
    PatchMedication,
)
from src.service.exceptions import (
    DuplicateError,
    ExtraArgumentError,
    InvalidArgumentTypeError,
)
from src.service.providers import provide_aidkit_service
from src.service.services import AidKitService

from ..dto import (
    AidKitDTO,
    CreateAidKitDTO,
    PatchAidKitDTO,
)
from ..query_params import (
    CreatedAfterParam,
    CreatedBeforeParam,
    IdsParam,
    LocationsParam,
    NamesParam,
    OffsetParam,
    PageSizeParam,
    UpdatedAfterParam,
    UpdatedBeforeParam,
)


@get("/", return_dto=AidKitDTO)
async def list_aidkits(
    service: Annotated[AidKitService, Dependency(skip_validation=True)],
    limit: int | None = PageSizeParam,
    offset: int | None = OffsetParam,
    created_before: datetime | None = CreatedBeforeParam,
    created_after: datetime | None = CreatedAfterParam,
    updated_before: datetime | None = UpdatedBeforeParam,
    updated_after: datetime | None = UpdatedAfterParam,
    pks: list[int] | None = IdsParam,
    names: list[str] | None = NamesParam,
    locations: list[str] | None = LocationsParam,
) -> list[AidKit]:
    return await service.list_items(
        limit=limit,
        offset=offset,
        created_before=created_before,
        created_after=created_after,
        updated_before=updated_before,
        updated_after=updated_after,
        pk=pks,
        name=names,
        location=locations,
    )


@post("/", dto=CreateAidKitDTO, return_dto=AidKitDTO)
async def add_aidkit(
    request: Request,
    service: Annotated[AidKitService, Dependency(skip_validation=True)],
    data: CreateAidKit,
) -> AidKit:
    try:
        aidkit = await service.create(data)
    except DuplicateError as err:
        request.logger.info(
            f"Attempt to create duplicate instance failed with error: {err}"
        )
        raise HTTPException(
            status_code=status_codes.HTTP_400_BAD_REQUEST,
            detail="Aidkit with provided data already exists",
        )
    except InvalidArgumentTypeError as err:
        request.logger.info(
            f"Invalid argument type detected, causing db query fail with error: {err}"
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
        )
        raise HTTPException(
            status_code=status_codes.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "At least one of the provided arguments does not belong to "
                "the database representation"
            ),
        )

    return aidkit


@get("/{aidkit_id: int}", return_dto=AidKitDTO, raises=[NotFoundException])
async def get_aidkit(
    service: Annotated[AidKitService, Dependency(skip_validation=True)],
    aidkit_id: Annotated[int, Parameter(int, gt=0, required=True)],
) -> Medication:
    aidkit = await service.get(aidkit_id)
    if not aidkit:
        raise NotFoundException(
            detail=f"Aidkit with id {aidkit_id} not found",
        )
    return aidkit


@patch("/{aidkit_id: int}", dto=PatchAidKitDTO, return_dto=AidKitDTO)
async def update_aidkit(
    request: Request,
    service: Annotated[AidKitService, Dependency(skip_validation=True)],
    aidkit_id: Annotated[int, Parameter(int, gt=0, required=True)],
    data: PatchMedication,
) -> Medication:
    try:
        aidkit = await service.update(aidkit_id, data)
    except DuplicateError as err:
        request.logger.info(
            f"Attempt to update producer with data already occupied. "
            f"?PK={aidkit_id}, ?DATA={data}, ?ERROR={err}"
        )
        raise HTTPException(
            status_code=status_codes.HTTP_409_CONFLICT,
            detail="Medication with provided data already exists",
        )
    except InvalidArgumentTypeError as err:
        request.logger.info(
            f"Invalid argument type detected, causing db query fail with error: {err}."
            f"?PK={aidkit_id}, ?DATA={data}."
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
            f"?PK={aidkit_id}, ?DATA={data}."
        )
        raise HTTPException(
            status_code=status_codes.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "At least one of the provided arguments does not belong to "
                "the database representation"
            ),
        )
    if not aidkit:
        raise NotFoundException(
            detail=f"Aidkit with id {aidkit_id} not found",
        )
    return aidkit


@delete("/{aidkit_id: int}")
async def delete_aidkit(
    service: Annotated[AidKitService, Dependency(skip_validation=True)],
    aidkit_id: Annotated[int, Parameter(int, gt=0, required=True)],
) -> None:
    deleted = await service.delete(aidkit_id)
    if not deleted:
        raise NotFoundException(detail=f"Aidkit with id {aidkit_id} not found")


router = Router(
    path="/aidkits",
    route_handlers=[
        list_aidkits,
        add_aidkit,
        get_aidkit,
        update_aidkit,
        delete_aidkit,
    ],
    dependencies={
        "db_session": Provide(provide_db_session),
        "service": Provide(provide_aidkit_service),
    },
)
