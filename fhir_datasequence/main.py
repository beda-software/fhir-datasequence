import aiohttp_cors

from aiohttp import web
from aiohttp_apispec import AiohttpApiSpec, validation_middleware

from fhir_datasequence import config
from fhir_datasequence.api.health_records import (
    ingest_health_records,
    read_health_records,
)

api_spec: AiohttpApiSpec | None = None
cors: aiohttp_cors.CorsConfig | None = None


async def application() -> web.Application:
    global api_spec, cors

    app = web.Application(middlewares=[validation_middleware])
    cors = aiohttp_cors.setup(app)
    app.router.add_post("/api/v1/records", ingest_health_records)
    cors.add(
        app.router.add_get("/api/v1/records", read_health_records),
        {
            config.EMR_WEB_URL: aiohttp_cors.ResourceOptions(
                allow_headers="*",
            ),
        },
    )
    api_spec = AiohttpApiSpec(
        app=app,
        url="/api/docs/openapi.json",
        title="Time series data storage",
        version="v1",
    )
    return app
