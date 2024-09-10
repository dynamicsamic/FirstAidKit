from datetime import datetime
from typing import Annotated

from litestar import Request, Router, delete, get, patch, post, status_codes
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotFoundException
from litestar.params import Dependency, Parameter

from src.data.providers import provide_db_session
from src.domain.models import CreateMedication, Medication, PatchMedication
from src.domain.types import DosageForm
from src.service.exceptions import (
    DuplicateError,
    ExtraArgumentError,
    InvalidArgumentTypeError,
)
from src.service.providers import provide_medication_service
from src.service.services import MedicationService

from ..dto import CreateMedicationDTO, MedicationDTO, PatchMedicationDTO
from ..query_params import (
    BrandNamesParam,
    CategoryIdsParam,
    CreatedAfterParam,
    CreatedBeforeParam,
    DosageFormsParam,
    GenericNamesParam,
    IdsParam,
    OffsetParam,
    PageSizeParam,
    ProducerIdsParam,
    UpdatedAfterParam,
    UpdatedBeforeParam,
)


@get("/", return_dto=MedicationDTO)
async def list_medications(
    service: Annotated[MedicationService, Dependency(skip_validation=True)],
    limit: int | None = PageSizeParam,
    offset: int | None = OffsetParam,
    created_before: datetime | None = CreatedBeforeParam,
    created_after: datetime | None = CreatedAfterParam,
    updated_before: datetime | None = UpdatedBeforeParam,
    updated_after: datetime | None = UpdatedAfterParam,
    pks: list[int] | None = IdsParam,
    brand_names: list[str] | None = BrandNamesParam,
    generic_names: list[str] | None = GenericNamesParam,
    dosage_forms: list[DosageForm] | None = DosageFormsParam,
    producer_ids: list[int] | None = ProducerIdsParam,
    category_ids: list[int] | None = CategoryIdsParam,
) -> list[Medication]:
    return await service.list_items(
        limit=limit,
        offset=offset,
        created_before=created_before,
        created_after=created_after,
        updated_before=updated_before,
        updated_after=updated_after,
        pk=pks,
        brand_name=brand_names,
        generic_name=generic_names,
        dosage_form=dosage_forms,
        producer_id=producer_ids,
        category_id=category_ids,
    )


@post("/", dto=CreateMedicationDTO, return_dto=MedicationDTO)
async def add_medication(
    request: Request,
    service: Annotated[MedicationService, Dependency(skip_validation=True)],
    data: CreateMedication,
) -> Medication:
    try:
        medication = await service.create(data)
    except DuplicateError as err:
        request.logger.info(
            f"Attempt to create duplicate instance failed with error: {err}"
        )
        raise HTTPException(
            status_code=status_codes.HTTP_400_BAD_REQUEST,
            detail="Medication with provided data already exists",
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

    return medication


@get("/{medication_id: int}", return_dto=MedicationDTO, raises=[NotFoundException])
async def get_medication(
    service: Annotated[MedicationService, Dependency(skip_validation=True)],
    medication_id: Annotated[int, Parameter(int, gt=0, required=True)],
) -> Medication:
    medication = await service.get(medication_id)
    if not medication:
        raise NotFoundException(
            detail=f"Medication with id {medication_id} not found",
        )
    return medication


@patch("/{medication_id: int}", dto=PatchMedicationDTO, return_dto=MedicationDTO)
async def update_medication(
    request: Request,
    service: Annotated[MedicationService, Dependency(skip_validation=True)],
    medication_id: Annotated[int, Parameter(int, gt=0, required=True)],
    data: PatchMedication,
) -> Medication:
    try:
        medication = await service.update(medication_id, data)
    except DuplicateError as err:
        request.logger.info(
            f"Attempt to update producer with data already occupied. "
            f"?PK={medication_id}, ?DATA={data}, ?ERROR={err}"
        )
        raise HTTPException(
            status_code=status_codes.HTTP_409_CONFLICT,
            detail="Medication with provided data already exists",
        )
    except InvalidArgumentTypeError as err:
        request.logger.info(
            f"Invalid argument type detected, causing db query fail with error: {err}."
            f"?PK={medication_id}, ?DATA={data}."
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
            f"?PK={medication_id}, ?DATA={data}."
        )
        raise HTTPException(
            status_code=status_codes.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "At least one of the provided arguments does not belong to "
                "the database representation"
            ),
        )
    if not medication:
        raise NotFoundException(
            detail=f"Medication with id {medication_id} not found",
        )
    return medication


@delete("/{medication_id: int}")
async def delete_medication(
    service: Annotated[MedicationService, Dependency(skip_validation=True)],
    medication_id: Annotated[int, Parameter(int, gt=0, required=True)],
) -> None:
    deleted = await service.delete(medication_id)
    if not deleted:
        raise NotFoundException(detail=f"Medication with id {medication_id} not found")


router = Router(
    path="/medications",
    route_handlers=[
        list_medications,
        add_medication,
        get_medication,
        update_medication,
        delete_medication,
    ],
    dependencies={
        "db_session": Provide(provide_db_session),
        "service": Provide(provide_medication_service),
    },
)
