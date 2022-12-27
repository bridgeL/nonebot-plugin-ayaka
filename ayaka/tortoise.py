from tortoise import Tortoise
from nonebot import get_driver

driver = get_driver()


@driver.on_startup
async def init():
    # Here we create a SQLite DB using file "db.sqlite3"
    #  also specify the app name of "models"
    #  which contain models from "app.models"
    await Tortoise.init(
        db_url='sqlite://ayaka.db',
        modules={'models': ['app.models']}
    )
    # Generate the schema
    await Tortoise.generate_schemas()
