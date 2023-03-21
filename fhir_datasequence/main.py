from aiohttp import web
from aiohttp_apispec import AiohttpApiSpec, validation_middleware

from fhir_datasequence.api.health_records import ingest_health_records

api_spec: AiohttpApiSpec | None = None


async def application() -> web.Application:
    global api_spec
    app = web.Application(middlewares=[validation_middleware])
    app.router.add_post("/api/v1/records", ingest_health_records)
    api_spec = AiohttpApiSpec(
        app=app,
        url="/api/docs/openapi.json",
        title="Time series data storage",
        version="v1",
    )
    return app
