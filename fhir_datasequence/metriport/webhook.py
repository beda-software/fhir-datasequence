import functools
import json
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from aiohttp import web
from aiohttp_apispec import headers_schema  # type: ignore
from marshmallow import Schema, fields

from fhir_datasequence import config


class RequestBodySchema(Schema):
    ping = fields.Str()


WEBHOOK_KEY_HEADER = "x-webhook-key"

AuthorizationSchema = Schema.from_dict({WEBHOOK_KEY_HEADER: fields.Str(required=True)})


def auth_token(
    api_handler: Callable[[web.Request], Coroutine[Any, Any, web.Response | web.HTTPOk]]
):
    @headers_schema(AuthorizationSchema)
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


# @json_schema(RequestBodySchema())
@auth_token
async def metriport_events_handler(request: web.Request):
    # data = request["json"]
    data = await request.json()

    # NOTE: https://docs.metriport.com/home/api-info/webhooks#the-ping-message
    if "ping" in data:
        return web.json_response({"pong": data["ping"]})

    # NOTE: temporary write data to file for analyzing
    with open("metriport_data.ndjson", "+a") as f:
        f.write(json.dumps(data))
        f.write("\n")

    return web.HTTPOk()
