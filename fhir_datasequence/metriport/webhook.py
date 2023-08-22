import json

import aiofiles
from aiohttp import web
from sqlalchemy import Table

from fhir_datasequence import config
from fhir_datasequence.metriport import METRIPORT_RECORDS_TABLE_NAME
from fhir_datasequence.metriport.client import authorize_webhook
from fhir_datasequence.metriport.db import write_record
from fhir_datasequence.metriport.utils import handle_activity_data


@authorize_webhook
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
