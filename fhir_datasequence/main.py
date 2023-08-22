import aiohttp_cors  # type: ignore
import sqlalchemy  # type: ignore
from aiohttp import web
from aiohttp_apispec import AiohttpApiSpec, validation_middleware  # type: ignore

from fhir_datasequence import config
from fhir_datasequence.api.health_records import (
    read_health_records,
    share_health_records,
    write_health_records,
)
from fhir_datasequence.metriport.api import (
    connect_token_handler,
    read_metriport_records,
    share_metriport_records,
)
from fhir_datasequence.metriport.client import attach as metriport_attach
from fhir_datasequence.metriport.webhook import metriport_events_handler

api_spec: AiohttpApiSpec | None = None
cors: aiohttp_cors.CorsConfig | None = None


async def pg_engine(app: web.Application):
    app["dbapi_engine"] = sqlalchemy.create_engine(config.DBAPI_CONN_URL)
    app["dbapi_metadata"] = sqlalchemy.MetaData()


async def application() -> web.Application:
    global api_spec, cors

    app = web.Application(middlewares=[validation_middleware])
    app.on_startup.append(pg_engine)
    app.cleanup_ctx.append(metriport_attach)
    cors = aiohttp_cors.setup(
        app,
        defaults={
            config.EMR_WEB_URL: aiohttp_cors.ResourceOptions(
                allow_headers="*",
            ),
        },
    )
    app.router.add_post("/api/v1/records", write_health_records)
    cors.add(app.router.add_get("/api/v1/records", read_health_records))
    cors.add(app.router.add_get("/api/v1/{patient}/records", share_health_records))

    # Metriport routes
    app.router.add_post("/metriport/webhook", metriport_events_handler),
    app.router.add_post("/metriport/connect-token", connect_token_handler)
    cors.add(app.router.add_get("/metriport/records", read_metriport_records))
    cors.add(
        app.router.add_get("/metriport/{patient}/records", share_metriport_records)
    )

    api_spec = AiohttpApiSpec(
        app=app,
        url="/api/v1/docs/openapi.json",
        title="Time series data storage",
        version="v1",
    )
    return app
