from sqlalchemy.ext.asyncio import AsyncSession

from .producer import ProducerService


async def provide_producer_service(db_session: AsyncSession):
    return ProducerService(db_session)
