from typing import Any, Iterable, Type, override

from sqlalchemy.exc import CompileError, DBAPIError, IntegrityError

from src.data.repository import ProducerRepository, Repository
from src.domain.models import BaseModel, CreateProducer, Producer

from .exceptions import DuplicateError, ExtraArgumentError, InvalidArgumentTypeError


class Service:
    repo_type: Type[Repository]
    model_type: BaseModel

    def __init__(self, db_session):
        self.repo = self.repo_type(db_session)

    async def list(
        self, limit: int, offset: int, **filters: dict[str, Any]
    ) -> list[BaseModel]:
        filters = self.parse_filters(filters)
        items = await self.repo.fetch_many(
            *filters, order_by=[self.repo.model.pk], limit=limit, offset=offset
        )
        return [self.model_type.model_validate(item) for item in items]

    async def create(self, data: BaseModel) -> BaseModel:
        try:
            obj = await self.repo.insert_one(**data.model_dump(exclude_none=True))
        except IntegrityError as err:
            raise DuplicateError from err
        except DBAPIError as err:
            raise InvalidArgumentTypeError from err
        except CompileError as err:
            raise ExtraArgumentError from err

        return self.model_type.model_validate(obj)

    def parse_filters(self, filters: dict[str, Any]) -> dict[str, Any]:
        validated = []

        if created_before := filters.pop("created_before", None):
            validated.append(self.repo.model.created_at < created_before)

        if created_after := filters.pop("created_after", None):
            validated.append(self.repo.model.created_at > created_after)

        if updated_before := filters.pop("updated_before", None):
            validated.append(self.repo.model.updated_at > updated_before)

        if updated_after := filters.pop("updated_after", None):
            validated.append(self.repo.model.updated_at > updated_after)

        for k, v in filters.items():
            if v is None or (attr := getattr(self.repo.model, k, None)) is None:
                continue

            if isinstance(v, Iterable):
                validated.append(attr.in_(v))
            else:
                validated.append(attr == v)

        return validated


class ProducerService(Service):
    repo_type = ProducerRepository
    model_type: Producer

    @override
    async def list(
        self, limit: int, offset: int, **filters: dict[str, Any]
    ) -> list[Producer]:
        return await super().list(limit=limit, offset=offset, **filters)

    @override
    async def create(self, data: CreateProducer) -> Producer:
        return await super().create(data=data)
