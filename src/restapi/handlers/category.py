from litestar import Router, delete, get, patch, post


@get("/")
async def list_categories() -> None:
    pass


@post("/")
async def add_category() -> None:
    pass


@get("/{cat_id: int}")
async def get_category() -> None:
    pass


@patch("/{cat_id: int}")
async def update_category() -> None:
    pass


@delete("/{cat_id: int}")
async def delete_category() -> None:
    pass


router = Router(
    path="/categories",
    route_handlers=[
        list_categories,
        add_category,
        get_category,
        update_category,
        delete_category,
    ],
)
