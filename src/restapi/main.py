from litestar import Litestar, get

from src.data.providers import provide_engine
from src.restapi.handlers import router
from src.settings import settings


@get('/')
async def index()->str:
    return "Hello world!"

app = Litestar(debug=settings.DEBUG, route_handlers=[router], lifespan=[provide_engine])
