from typing import Any, Iterable

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql._typing import _ColumnExpressionArgument

from .models import BaseModel, Producer


class Repository:
    _model = BaseModel
    _pk = BaseModel.pk

    @classmethod
    def model(cls):
        return cls._model

    @classmethod
    def pk(cls):
        return cls._model.pk

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _select(
        self,
        *filters: _ColumnExpressionArgument[bool],
        order_by: Iterable[InstrumentedAttribute] = None,
    ) -> Select:
        qry = select(self.model()).where(*filters)

        if order_by:
            qry = qry.order_by(*order_by)

        return qry

    async def fetch_many(self):
        qry = self._select()
        return await self.session.execute(qry)

    async def fetch_one_by_pk(self, pk: Any)-> BaseModel:
        qry = self._select(self.pk()==pk)
        return (await self.session.execute(qry)).scalars().first()

    async def fetch_any_one():
        pass


class ProducerRepository(Repository):
    _model = Producer
