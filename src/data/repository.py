from typing import Any, Iterable, Type

from sqlalchemy import Select, delete, insert, select, text, update
from sqlalchemy.engine import CursorResult, Result, ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql._typing import _ColumnExpressionArgument
from sqlalchemy.sql.base import Executable

from src.settings import settings

from .models import BaseModel, Category, Producer


class Repository:
    model: Type[BaseModel] = BaseModel

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def fetch_many(
        self,
        *filters: _ColumnExpressionArgument[bool],
        order_by: Iterable[InstrumentedAttribute] = None,
        limit: int = settings.ITEMS_PER_PAGE,
        offset: int = 0,
    ) -> ScalarResult[BaseModel]:
        if offset:
            filters = list(filters)
            filters.append(self.model.pk > offset)

        qry = self._select(*filters, order_by=order_by).limit(limit)
        return (await self.execute(qry)).scalars()

    async def fetch_one_by_any(
        self,
        *filters: _ColumnExpressionArgument[bool],
        order_by: Iterable[InstrumentedAttribute] = None,
    ) -> BaseModel | None:
        return (await self.fetch_many(*filters, order_by=order_by)).first()

    async def fetch_one_by_pk(self, pk: Any) -> BaseModel | None:
        return await self.fetch_one_by_any(self.model.pk == pk)

    async def insert_one(self, **create_data: Any) -> BaseModel | None:
        res = await self.execute(
            insert(self.model).values(create_data).returning(self.model)
        )
        await self.commit()
        return res.scalars().first()

    async def update(
        self,
        *filters: _ColumnExpressionArgument[bool],
        **update_data: Any,
    ) -> ScalarResult[BaseModel]:
        res = await self.execute(
            update(self.model)
            .values(**update_data)
            .where(*filters)
            .returning(self.model)
        )
        await self.commit()
        return res.scalars()

    async def update_one_by_pk(
        self,
        pk: Any,
        **update_data: Any,
    ) -> BaseModel | None:
        return (await self.update(self.model.pk == pk, **update_data)).first()

    async def delete(self, *filters: _ColumnExpressionArgument[bool]) -> int:
        res = await self.execute(delete(self.model).where(*filters))
        await self.commit()
        return res.rowcount

    async def exists(self, *filters: _ColumnExpressionArgument[bool]) -> bool:
        res = await self.execute(select(self.model.pk).where(*filters))
        return (res.scalars().first() or 0) > 0

    async def estimate(self) -> int:
        qry = """
        SELECT  reltuples::bigint AS estimate
        FROM    pg_class
        WHERE   oid = 'public.{tablename}'::regclass;
        """
        count = await self.session.scalar(
            text(qry.format(tablename=self.model.__tablename__))
        )
        if count < 0:
            await self.execute(text(f"ANALYZE {self.model.__tablename__};"))
            count = await self.session.scalar(
                text(qry.format(tablename=self.model.__tablename__))
            )
        return count

    async def execute(self, stmt: Executable, *args, **kwargs) -> Result | CursorResult:
        return await self.session.execute(stmt, *args, **kwargs)

    async def commit(self) -> None:
        return await self.session.commit()

    def _select(
        self,
        *filters: _ColumnExpressionArgument[bool],
        order_by: Iterable[InstrumentedAttribute] = None,
    ) -> Select:
        qry = select(self.model).where(*filters)

        if order_by:
            qry = qry.order_by(*order_by)

        return qry


class ProducerRepository(Repository):
    model = Producer


class CategoryRepository(Repository):
    model = Category
