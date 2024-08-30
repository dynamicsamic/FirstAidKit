import asyncio

from click import Group
from litestar import Litestar
from litestar.plugins import CLIPluginProtocol
from sqlalchemy.ext.asyncio import create_async_engine

from src.data.db import create_db_url
from src.data.models import Base


class CLIPlugin(CLIPluginProtocol):
    def on_cli_init(self, cli: Group) -> None:
        @cli.command(name="create-tables")
        def create_tables_wrapper(app: Litestar):
            async def create_db_tables():
                engine = create_async_engine(create_db_url())
                async with engine.begin() as con:
                    await con.run_sync(Base.metadata.create_all)
            
            print("Creating database tables")
            asyncio.get_event_loop().run_until_complete(create_db_tables())

        @cli.command(name="drop-tables")
        def drop_tables_wrapper(app: Litestar):
            async def create_db_tables():
                engine = create_async_engine(create_db_url())
                async with engine.begin() as con:
                    await con.run_sync(Base.metadata.drop_all)

            print("Dropping database tables")
            asyncio.get_event_loop().run_until_complete(create_db_tables())