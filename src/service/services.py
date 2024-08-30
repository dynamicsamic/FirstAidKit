from typing import Any, Iterable, Type

from src.data.repository import ProducerRepository, Repository
from src.domain.models import MedicationProducer


class Service:
    repo_type: Type[Repository]

    def __init__(self, db_session):
        self.repo = self.repo_type(db_session)

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
            attr = getattr(self.repo.model, k, None)
            if not attr or not v:
                continue

            if isinstance(v, Iterable):
                validated.append(attr.in_(v))
            else:
                validated.append(attr == v)

        return validated


class ProducerService(Service):
    repo_type = ProducerRepository

    async def get_producers(
        self, limit: int, offset: int, filters: dict[str, Any]
    ) -> list[MedicationProducer]:
        filters = self.parse_filters(filters)
        return (
            await self.repo.fetch_many(
                *filters, order_by=[self.repo.model.pk], limit=limit, offset=offset
            )
        ).all()
