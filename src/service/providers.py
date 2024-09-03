from sqlalchemy.ext.asyncio import AsyncSession

from .services import ProducerService


async def provide_producer_service(db_session: AsyncSession) -> ProducerService:
    return ProducerService(db_session)
