from typing import Any, Iterable, Type

from sqlalchemy import Select, SQLColumnExpression, delete, insert, select, text, update
from sqlalchemy.engine import CursorResult, Result, ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, defer, joinedload, load_only
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql._typing import _ColumnExpressionArgument
from sqlalchemy.sql.base import Executable, ExecutableOption

from src.settings import settings

from .models import AidKit, BaseModel, Category, Medication, MedicationStock, Producer


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
        order_by: Iterable[InstrumentedAttribute] | None = None,
        columns: Iterable[SQLColumnExpression] | None = None,
        options: Iterable[ExecutableOption] | None = None,
    ) -> Select:
        selected = columns or self.model
        order_by = order_by or [self.model.pk]

        qry = select(selected).where(*filters).order_by(*order_by)

        if options:
            qry = qry.options(*options)

        return qry


class ProducerRepository(Repository):
    model = Producer


class CategoryRepository(Repository):
    model = Category


class MedicationRepository(Repository):
    model = Medication

    def _select(
        self,
        *filters: _ColumnExpressionArgument[bool],
        order_by: Iterable[InstrumentedAttribute] | None = None,
    ):
        return super()._select(
            *filters,
            order_by=order_by,
            options=(
                joinedload(Medication.producer).options(
                    load_only(Producer.name, Producer.pk)
                ),
                joinedload(Medication.category).options(
                    load_only(Category.name, Category.pk)
                ),
            ),
        )


class AidKitRepository(Repository):
    model = AidKit

    async def fetch_one_by_any(
        self,
        *filters: _ColumnExpressionArgument[bool],
        order_by: Iterable[InstrumentedAttribute] = None,
        stock_limit: int = settings.ITEMS_PER_PAGE,
        stock_offset: int = 0,
        stock_order_by: Iterable[InstrumentedAttribute] = None,
    ) -> AidKit | None:
        order_by = order_by or [AidKit.created_at]
        stock_order_by = stock_order_by or [MedicationStock.created_at]

        # Select stocks in subquery to apply custom limit, offset and ordering.
        stocks_query = (
            select(MedicationStock)
            .where(
                MedicationStock.aidkit_id == AidKit.pk,
                MedicationStock.pk > stock_offset,
            )
            .order_by(*stock_order_by)
            .limit(stock_limit)
            .subquery("aidkit_stock")
            .lateral()
        )

        # Join aidkit, stocks, medications, producers and categories.
        # Defer loading columns with repeating data.
        qry = (
            select(AidKit)
            .where(*filters)
            .order_by(*order_by)
            .outerjoin(stocks_query)
            .options(
                contains_eager(AidKit.stocks, alias=stocks_query).options(
                    joinedload(MedicationStock.medication).options(
                        defer(Medication.producer_id),
                        defer(Medication.category_id),
                        defer(Medication.created_at),
                        defer(Medication.updated_at),
                        joinedload(Medication.producer).options(
                            load_only(Producer.name, Producer.pk)
                        ),
                        joinedload(Medication.category).options(
                            load_only(Category.name, Category.pk)
                        ),
                    ),
                    defer(MedicationStock.aidkit_id),
                    defer(MedicationStock.medication_id),
                    defer(MedicationStock.created_at),
                    defer(MedicationStock.updated_at),
                )
            )
        )

        return (await self.session.scalars(qry)).unique().first()

    async def fetch_one_by_pk(
        self,
        pk: int,
        stock_limit: int = settings.ITEMS_PER_PAGE,
        stock_offset: int = 0,
        stock_order_by: Iterable[InstrumentedAttribute] = None,
    ) -> AidKit | None:
        return await self.fetch_one_by_any(
            self.model.pk == pk,
            stock_limit=stock_limit,
            stock_offset=stock_offset,
            stock_order_by=stock_order_by,
        )
