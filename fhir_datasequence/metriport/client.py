import functools
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from aiohttp import ClientResponse, ClientSession, web
from aiohttp_apispec import headers_schema  # type: ignore
from marshmallow import Schema, fields

from fhir_datasequence import config

WEBHOOK_KEY_HEADER = "x-webhook-key"

WebhookAuthorizationSchema = Schema.from_dict(
    {WEBHOOK_KEY_HEADER: fields.Str(required=True)}
)


async def attach(app: web.Application):
    session = ClientSession(
        config.METRIPORT_API_BASE_URL,
        headers={config.METRIPORT_API_KEY_REQUEST_HEADER: config.METRIPORT_API_SECRET},
    )
    app["metriport_client"] = session

    yield

    await app["metriport_client"].close()


def authorize_webhook(
    api_handler: Callable[[web.Request], Coroutine[Any, Any, web.Response | web.HTTPOk]]
):
    @headers_schema(WebhookAuthorizationSchema)
    @functools.wraps(api_handler)
    async def verify_auth_key(request: web.Request):
        auth_key = request["headers"][WEBHOOK_KEY_HEADER]
        if (
            not config.METRIPORT_WEBHOOK_AUTH_KEY
            or auth_key != config.METRIPORT_WEBHOOK_AUTH_KEY
        ):
            logging.exception("Metriport webhook auth key verification has failed")
            raise web.HTTPUnauthorized()

        return await api_handler(request)

    return verify_auth_key


async def get_user(session: ClientSession, app_user_id: str):
    async with session.post("/user", params={"appUserId": app_user_id}) as resp:
        data, _status = await handle_response(resp)
        return data["userId"]


async def get_connect_token(session: ClientSession, user_id: str):
    async with session.get("/user/connect/token", params={"userId": user_id}) as resp:
        return await handle_response(resp)


async def handle_response(response: ClientResponse):
    if 200 <= response.status < 300:
        data = await response.json()
        return (data, response.status)
    # NOTE: should we handle errors or aiohttp raises appropriate exception itself?
    raise web.HTTPClientError(text=await response.text())
