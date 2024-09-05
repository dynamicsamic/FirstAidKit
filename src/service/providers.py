from sqlalchemy.ext.asyncio import AsyncSession

from .services import CategoryService, ProducerService


async def provide_producer_service(db_session: AsyncSession) -> ProducerService:
    return ProducerService(db_session)

async def provide_category_service(db_session: AsyncSession) -> CategoryService:
    return CategoryService(db_session)