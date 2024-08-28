from litestar import Router, delete, get, post


@get("/")
async def list_stock_items() -> None:
    pass


@post("/")
async def add_item_in_stock() -> None:
    pass


@get("/{stock_id: int}")
async def get_stock_item() -> None:
    pass


@delete("/{stock_id: int}")
async def remove_item_from_stock() -> None:
    pass


@post("/{stock_id: int}/consume")
async def consume_stock_item() -> None:
    pass


router = Router(
    path="/medications/{meds_id: int}/stock",
    route_handlers=[
        list_stock_items,
        add_item_in_stock,
        get_stock_item,
        remove_item_from_stock,
        consume_stock_item,
    ],
)
