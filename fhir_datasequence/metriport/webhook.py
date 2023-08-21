import functools
import json
import logging
from collections.abc import Callable, Coroutine
from typing import Any

import aiofiles
from aiohttp import web
from aiohttp_apispec import headers_schema  # type: ignore
from marshmallow import Schema, fields
from sqlalchemy import Table

from fhir_datasequence import config
from fhir_datasequence.metriport import METRIPORT_RECORDS_TABLE_NAME
from fhir_datasequence.metriport.db import write_record
from fhir_datasequence.metriport.utils import handle_activity_data

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


@auth_token
async def metriport_events_handler(request: web.Request):
    data = await request.json()

    # NOTE: https://docs.metriport.com/home/api-info/webhooks#the-ping-message
    if "ping" in data:
        return web.json_response({"pong": data["ping"]})

    records_table = Table(
        METRIPORT_RECORDS_TABLE_NAME,
        request.app["dbapi_metadata"],
        autoload_with=request.app["dbapi_engine"],
    )

    try:
        records = handle_activity_data(data)
        for record in records:
            write_record(record, request.app["dbapi_engine"], records_table)
    except NotImplementedError:
        # NOTE: All unhandled messages are written to a file
        async with aiofiles.open(config.METRIPORT_UNHANDLED_DATA_FILENAME, "+a") as f:
            await f.write(json.dumps(data))
            await f.write("\n")

    return web.HTTPOk()
