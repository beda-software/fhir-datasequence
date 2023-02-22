import sqlalchemy

from aiohttp import web
from sqlalchemy import MetaData, Table, insert

from fhir_datasequence import config

routes = web.RouteTableDef()
dbapi_engine = sqlalchemy.create_engine(config.DBAPI_CONN_URL)
dbapi_metadata = MetaData()


@routes.post("/api/v1/records")
async def ingest_health_records(request: web.Request):
    payload = await request.json()
    records_table = Table("records", dbapi_metadata, autoload_with=dbapi_engine)
    with dbapi_engine.begin() as connection:
        connection.execute(
            insert(records_table),
            [
                {
                    "sid": record["sid"],
                    "ts": record["ts"],
                    "code": record["code"],
                    "duration": record.get("duration"),
                    "energy": record.get("energy"),
                    "start": record.get("start"),
                    "finish": record.get("finish"),
                }
                for record in payload["records"]
            ],
        )
    return web.json_response({"status": "OK"})


async def application() -> web.Application:
    app = web.Application()
    app.add_routes(routes)
    return app
