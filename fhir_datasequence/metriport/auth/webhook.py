import functools
from aiohttp import web
import logging

from marshmallow import Schema, fields
from aiohttp_apispec import json_schema, docs, headers_schema
from fhir_datasequence import config

import json


class RequestBodySchema(Schema):
    ping = fields.Str()


AuthorizationSchema = Schema.from_dict(
    {config.METRIPORT_API_KEY_REQUEST_HEADER: fields.Str(required=True)}
)


def auth_token(api_handler):
    @headers_schema(AuthorizationSchema)
    @functools.wraps(api_handler)
    async def verify_auth_key(request: web.BaseRequest):
        auth_key = request["headers"][config.METRIPORT_API_KEY_REQUEST_HEADER]
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

    # TODO: temporary write data to file for analyzing
    with open("metriport_data.ndjson", "+a") as f:
        f.write(json.dumps(data))
        f.write('\n')

    return web.HTTPOk()
