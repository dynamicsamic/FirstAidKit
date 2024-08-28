from litestar import Router

from .category import router as catrouter
from .medication import router as medrouter
from .producer import router as prodrouter
from .stock import router as stockrouter

router = Router(path="/api/v1", route_handlers=[medrouter, stockrouter, catrouter, prodrouter])
