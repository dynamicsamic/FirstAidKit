from litestar import Router, delete, get, patch, post


@get("/")
async def list_medications() -> None:
    pass


@post("/")
async def add_medication() -> None:
    pass


@get("/{meds_id: int}")
async def get_medication() -> None:
    pass


@patch("/{meds_id: int}")
async def update_medication() -> None:
    pass


@delete("/{meds_id: int}")
async def delete_medication() -> None:
    pass


router = Router(
    path="/medications",
    route_handlers=[
        list_medications,
        add_medication,
        get_medication,
        update_medication,
        delete_medication,
    ],
)
