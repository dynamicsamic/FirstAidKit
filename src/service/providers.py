from sqlalchemy.ext.asyncio import AsyncSession

from .services import AidKitService, CategoryService, MedicationService, ProducerService


async def provide_producer_service(db_session: AsyncSession) -> ProducerService:
    return ProducerService(db_session)


async def provide_category_service(db_session: AsyncSession) -> CategoryService:
    return CategoryService(db_session)


async def provide_medication_service(db_session: AsyncSession) -> MedicationService:
    return MedicationService(db_session)


async def provide_aidkit_service(db_session: AsyncSession) -> AidKitService:
    return AidKitService(db_session)
