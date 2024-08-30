from litestar import Litestar, get

from src.data.providers import provide_engine
from src.restapi.handlers import router
from src.settings import settings

from .cli import CLIPlugin


@get("/health")
async def index() -> str:
    return "FirstAidKit REST API is running"


def create_app():
    route_handlers = [router]
    lifespan = [provide_engine]

    return Litestar(
        debug=settings.DEBUG, route_handlers=route_handlers, lifespan=lifespan,
        plugins=[CLIPlugin()]
    )


app = create_app()
