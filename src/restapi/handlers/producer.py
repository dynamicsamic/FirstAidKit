from typing import Any

from litestar import Router, delete, get, patch, post
from litestar.di import Provide
from sqlalchemy import text

from src.data.providers import provide_db_session
from src.service.providers import provide_producer_service


@get("/")
async def list_producers(service: Any) -> None:
    print(service)
    # print(db_session)
    r = await service.repo.session.execute(text("select * from producers"))
    # print(state.dict())
    # async with sessionmaker(bind=state.db_engine) as session, session.begin():
    # r = await session.execute(text("select * from producers"))
    print(r.scalars().all())
    print(service.repo.select())


@post("/")
async def add_producer() -> None:
    pass


@get("/{prod_id: int}")
async def get_producer() -> None:
    pass


@patch("/{prod_id: int}")
async def update_producer() -> None:
    pass


@delete("/{prod_id: int}")
async def delete_producer() -> None:
    pass


router = Router(
    path="/producers",
    route_handlers=[
        list_producers,
        add_producer,
        get_producer,
        update_producer,
        delete_producer,
    ],
    dependencies={
        "db_session": Provide(provide_db_session),
        "service": Provide(provide_producer_service),
    },
)
