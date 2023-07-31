from aiohttp import web
import logging

from marshmallow import Schema, fields

class RequestSchema(Schema):
    ping = fields.Str()


async def metriport_events_handler(request: web.Request):
    data = await request.json()

    # NOTE: https://docs.metriport.com/home/api-info/webhooks#the-ping-message
    if "ping" in data:
        return web.json_response({"pong": data["ping"]})

    logging.debug("DATA %s", data)

    return web.json_response({})