import aiohttp_cors

from aiohttp import web
from aiohttp_apispec import AiohttpApiSpec, validation_middleware

from fhir_datasequence import config
from fhir_datasequence.api.health_records import (
    share_health_records,
    write_health_records,
    read_health_records,
)
from fhir_datasequence.metriport.api import metriport_events_handler

api_spec: AiohttpApiSpec | None = None
cors: aiohttp_cors.CorsConfig | None = None


async def application() -> web.Application:
    global api_spec, cors

    app = web.Application(middlewares=[validation_middleware])
    cors = aiohttp_cors.setup(app)
    app.router.add_post("/api/v1/records", write_health_records)
    cors.add(
        app.router.add_get("/api/v1/records", read_health_records),
        {
            config.EMR_WEB_URL: aiohttp_cors.ResourceOptions(
                allow_headers="*",
            ),
        },
    )
    cors.add(
        app.router.add_get("/api/v1/{patient}/records", share_health_records),
        {
            config.EMR_WEB_URL: aiohttp_cors.ResourceOptions(
                allow_headers="*",
            ),
        },
    )

    cors.add(app.router.add_post("/metriport/webhook", metriport_events_handler))


    api_spec = AiohttpApiSpec(
        app=app,
        url="/api/v1/docs/openapi.json",
        title="Time series data storage",
        version="v1",
    )
    return app
