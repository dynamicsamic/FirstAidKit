from datetime import datetime
from typing import Annotated

from litestar import Request, Router, delete, get, patch, post, status_codes
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotFoundException
from litestar.params import Dependency, Parameter

from src.data.providers import provide_db_session
from src.domain.models import Category, CreateCategory, PatchCategory
from src.service.exceptions import (
    DuplicateError,
    ExtraArgumentError,
    InvalidArgumentTypeError,
)
from src.service.providers import provide_category_service
from src.service.services import CategoryService

from ..dto import CategoryDTO, CreateCategoryDTO, PatchCategoryDTO
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


@get("/", return_dto=CategoryDTO)
async def list_categories(
    service: Annotated[CategoryService, Dependency(skip_validation=True)],
    limit: int | None = PageSizeParam,
    offset: int | None = OffsetParam,
    created_before: datetime | None = CreatedBeforeParam,
    created_after: datetime | None = CreatedAfterParam,
    updated_before: datetime | None = UpdatedBeforeParam,
    updated_after: datetime | None = UpdatedAfterParam,
    pks: list[int] | None = IdsParam,
    names: list[str] | None = NamesParam,
) -> list[Category]:
    return await service.list_items(
        limit=limit,
        offset=offset,
        created_before=created_before,
        created_after=created_after,
        updated_before=updated_before,
        updated_after=updated_after,
        pk=pks,
        name=names,
    )


@post("/", dto=CreateCategoryDTO, return_dto=CategoryDTO)
async def add_category(
    request: Request,
    service: Annotated[CategoryService, Dependency(skip_validation=True)],
    data: CreateCategory,
) -> Category:
    try:
        category = await service.create(data)
    except DuplicateError as err:
        request.logger.info(
            f"Attempt to create duplicate instance failed with error: {err}"
        )
        raise HTTPException(
            status_code=status_codes.HTTP_400_BAD_REQUEST,
            detail="Category with provided data already exists",
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

    return category


@get("/{category_id: int}", return_dto=CategoryDTO, raises=[NotFoundException])
async def get_category(
    service: Annotated[CategoryService, Dependency(skip_validation=True)],
    category_id: Annotated[int, Parameter(int, gt=0, required=True)],
) -> Category:
    category = await service.get(category_id)
    if not category:
        raise NotFoundException(
            detail=f"Category with id {category_id} not found",
        )
    return category


@patch(
    "/{category_id: int}",
    dto=PatchCategoryDTO,
    return_dto=CategoryDTO,
    raises=[NotFoundException],
)
async def update_category(
    request: Request,
    service: Annotated[CategoryService, Dependency(skip_validation=True)],
    category_id: Annotated[int, Parameter(int, gt=0, required=True)],
    data: PatchCategory,
) -> Category:
    try:
        category = await service.update(category_id, data)
    except DuplicateError as err:
        request.logger.info(
            f"Attempt to update producer with data already occupied. "
            f"?PK={category_id}, ?DATA={data}, ?ERROR={err}"
        )
        raise HTTPException(
            status_code=status_codes.HTTP_409_CONFLICT,
            detail="Category with provided data already exists",
        )
    except InvalidArgumentTypeError as err:
        request.logger.info(
            f"Invalid argument type detected, causing db query fail with error: {err}."
            f"?PK={category_id}, ?DATA={data}."
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
            f"?PK={category_id}, ?DATA={data}."
        )
        raise HTTPException(
            status_code=status_codes.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "At least one of the provided arguments does not belong to "
                "the database representation"
            ),
        )

    if not category:
        raise NotFoundException(detail=f"Category with id {category_id} not found")

    return category


@delete("/{category_id: int}", raises=[NotFoundException])
async def delete_category(
    service: Annotated[CategoryService, Dependency(skip_validation=True)],
    category_id: Annotated[int, Parameter(int, gt=0, required=True)],
) -> None:
    deleted = await service.delete(category_id)
    if not deleted:
        raise NotFoundException(detail=f"Category with id {category_id} not found")


router = Router(
    path="/categories",
    route_handlers=[
        list_categories,
        add_category,
        get_category,
        update_category,
        delete_category,
    ],
    dependencies={
        "db_session": Provide(provide_db_session),
        "service": Provide(provide_category_service),
    },
)
