from aiohttp import web
import logging

from marshmallow import Schema, fields
from aiohttp_apispec import json_schema, docs, headers_schema
from fhir_datasequence import config


class RequestSchema(Schema):
    ping = fields.Str()


AuthorizationSchema = Schema.from_dict(
    {config.METRIPORT_API_KEY_REQUEST_HEADER: fields.Str(required=True)}
)


@headers_schema(AuthorizationSchema)
async def metriport_events_handler(request: web.Request):
    data = await request.json()
    logging.debug("DATA %s", data)

    # NOTE: https://docs.metriport.com/home/api-info/webhooks#the-ping-message
    if "ping" in data:
        return web.json_response({"pong": data["ping"]})

    return web.json_response({})
