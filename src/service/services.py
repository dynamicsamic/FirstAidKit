from typing import Any, Iterable, Type, override

from sqlalchemy.exc import CompileError, DBAPIError, IntegrityError
from sqlalchemy.sql._typing import _ColumnExpressionArgument

from src.data.repository import (
    CategoryRepository,
    MedicationRepository,
    ProducerRepository,
    Repository,
)
from src.domain.models import (
    BaseModel,
    Category,
    CreateCategory,
    CreateMedication,
    CreateProducer,
    Medication,
    PatchCategory,
    PatchMedication,
    PatchProducer,
    Producer,
)
from src.settings import settings

from .exceptions import DuplicateError, ExtraArgumentError, InvalidArgumentTypeError


class Service:
    repo_type: Type[Repository]
    model_type: BaseModel

    def __init__(self, db_session):
        self.repo = self.repo_type(db_session)

    async def list_items(
        self, limit: int, offset: int, **filters: dict[str, Any]
    ) -> list[BaseModel]:
        if offset < 0 or limit < 1 or limit > settings.PAGINATION_LIMIT:
            raise ValueError(
                "Offset must be greater or equal to 0. Limit must be greater or eqaul "
                f"to 1 and less then or equal to {settings.PAGINATION_LIMIT}."
            )
        filters = self.parse_filters(filters)
        items = await self.repo.fetch_many(
            *filters, order_by=[self.repo.model.pk], limit=limit, offset=offset
        )
        return [self.model_type.model_validate(item) for item in items]

    async def create(self, data: BaseModel) -> BaseModel:
        if not (data := data.model_dump(exclude_none=True)):
            raise ValueError("Empty data not allowed.")
        try:
            obj = await self.repo.insert_one(**data)
        except IntegrityError as err:
            raise DuplicateError from err
        except DBAPIError as err:
            raise InvalidArgumentTypeError from err
        except CompileError as err:
            raise ExtraArgumentError from err

        return self.model_type.model_validate(obj)

    async def get(self, pk: Any) -> BaseModel | None:
        instance = await self.repo.fetch_one_by_pk(pk=pk)
        return (
            self.model_type.model_validate(instance) if instance is not None else None
        )

    async def update(self, pk: Any, data: BaseModel) -> BaseModel | None:
        if not (data := data.model_dump(exclude_none=True)):
            raise ValueError("Empty data not allowed.")
        try:
            updated = await self.repo.update_one_by_pk(pk, **data)
        except IntegrityError as err:
            raise DuplicateError from err
        except DBAPIError as err:
            raise InvalidArgumentTypeError from err
        except CompileError as err:
            raise ExtraArgumentError from err

        return self.model_type.model_validate(updated) if updated is not None else None

    async def delete(self, pk: Any) -> bool:
        return await self.repo.delete(self.repo.model.pk == pk)

    def parse_filters(
        self, filters: dict[str, Any]
    ) -> list[_ColumnExpressionArgument[bool]]:
        validated = []

        if created_before := filters.pop("created_before", None):
            validated.append(self.repo.model.created_at < created_before)

        if created_after := filters.pop("created_after", None):
            validated.append(self.repo.model.created_at > created_after)

        if updated_before := filters.pop("updated_before", None):
            validated.append(self.repo.model.updated_at < updated_before)

        if updated_after := filters.pop("updated_after", None):
            validated.append(self.repo.model.updated_at > updated_after)

        for k, v in filters.items():
            if v is None or (attr := getattr(self.repo.model, k, None)) is None:
                continue

            attr_type = attr.type.python_type
            if isinstance(v, Iterable):
                if not all(isinstance(i, attr_type) for i in v):
                    raise ValueError(
                        f"Provided filter values {v} do not match database "
                        f"column {attr} type. Column type is {attr_type}."
                    )
                validated.append(attr.in_(v))
            else:
                if not isinstance(v, attr_type):
                    raise ValueError(
                        f"Provided filter value {v} do not match database "
                        f"column {attr} type. Column type is {attr_type}."
                    )
                validated.append(attr == v)

        return validated


class ProducerService(Service):
    repo_type = ProducerRepository
    model_type = Producer

    @override
    async def list_items(
        self, limit: int, offset: int, **filters: dict[str, Any]
    ) -> list[Producer]:
        return await super().list_items(limit=limit, offset=offset, **filters)

    @override
    async def create(self, data: CreateProducer) -> Producer:
        return await super().create(data=data)

    @override
    async def get(self, producer_id: int) -> Producer | None:
        return await super().get(pk=producer_id)

    @override
    async def update(self, producer_id: int, data: PatchProducer) -> Producer | None:
        return await super().update(pk=producer_id, data=data)

    @override
    async def delete(self, producer_id: int) -> bool:
        return await super().delete(pk=producer_id)


class CategoryService(Service):
    repo_type = CategoryRepository
    model_type = Category

    @override
    async def list_items(
        self, limit: int, offset: int, **filters: dict[str, Any]
    ) -> list[Category]:
        return await super().list_items(limit=limit, offset=offset, **filters)

    @override
    async def create(self, data: CreateCategory) -> Category:
        return await super().create(data=data)

    @override
    async def get(self, category_id: int) -> Category | None:
        return await super().get(pk=category_id)

    @override
    async def update(self, category_id: int, data: PatchCategory) -> Category | None:
        return await super().update(pk=category_id, data=data)

    @override
    async def delete(self, category_id: int) -> bool:
        return await super().delete(pk=category_id)


class MedicationService(Service):
    repo_type = MedicationRepository
    model_type = Medication

    @override
    async def list_items(
        self, limit: int, offset: int, **filters: dict[str, Any]
    ) -> list[Medication]:
        return await super().list_items(limit=limit, offset=offset, **filters)

    @override
    async def create(self, data: CreateMedication) -> Medication:
        return await super().create(data=data)

    @override
    async def get(self, medication_id: int) -> Medication | None:
        return await super().get(pk=medication_id)

    @override
    async def update(
        self, medication_id: int, data: PatchMedication
    ) -> Medication | None:
        return await super().update(pk=medication_id, data=data)

    @override
    async def delete(self, medication_id: int) -> bool:
        return await super().delete(pk=medication_id)
