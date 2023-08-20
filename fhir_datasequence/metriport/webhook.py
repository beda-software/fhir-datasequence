import datetime
import functools
import json
import logging
from collections.abc import Callable, Coroutine
from typing import Any
from uuid import uuid4

from aiohttp import web
from aiohttp_apispec import headers_schema  # type: ignore
from marshmallow import Schema, fields
from sqlalchemy import Engine, Table, and_, insert, select, update
from sqlalchemy import MetaData as DBMetaData

from fhir_datasequence import config
from fhir_datasequence.metriport import METRIPORT_RECORDS_TABLE_NAME

WEBHOOK_KEY_HEADER = "x-webhook-key"

AuthorizationSchema = Schema.from_dict({WEBHOOK_KEY_HEADER: fields.Str(required=True)})

DATETIME_MASK = "%Y-%m-%dT%H:%M:%S.%f%z"


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


def write_record(record: dict, dbapi_engine: Engine, table: Table):
    with dbapi_engine.begin() as connection:
        exists_record = connection.execute(
            select(table).where(
                and_(
                    table.c.uid == record["uid"],
                    table.c.start
                    == datetime.datetime.strptime(record["start"], DATETIME_MASK),
                    table.c.provider == record["provider"],
                )
            )
        ).first()

        if exists_record:
            connection.execute(
                update(table).where(table.c.ts == exists_record.ts).values(**record)
            )
        else:
            connection.execute(insert(table), record)


def parse_end_datetime(activity_log_item: dict):
    if activity_log_item.get("end_time"):
        return activity_log_item["end_time"]
    parsed_start_datetime = None
    duration: int | None = None
    if activity_log_item.get("durations"):
        start_datetime: str = activity_log_item["start_time"]
        duration = activity_log_item["durations"]["active_seconds"]
        try:
            parsed_start_datetime = datetime.datetime.strptime(
                start_datetime, DATETIME_MASK
            )
        except ValueError as err:
            logging.error(str(err))
            return None

    if parsed_start_datetime and duration:
        ts = int(parsed_start_datetime.timestamp())
        return datetime.datetime.fromtimestamp(
            ts + duration, parsed_start_datetime.tzinfo
        )


def parse_duration(activity_log_item: dict):
    duration = None
    if "durations" in activity_log_item:
        duration = activity_log_item["durations"]["active_seconds"]

    return duration


def parse_energy(activity_log_item: dict):
    energy = None
    if "energy_expenditure" in activity_log_item:
        energy = activity_log_item["energy_expenditure"].get("active_kcal")
    return energy


async def handle_activity_data(
    data: dict, dbapi_engine: Engine, dbapi_metadata: DBMetaData
):
    records_table = Table(
        METRIPORT_RECORDS_TABLE_NAME,
        dbapi_metadata,
        autoload_with=dbapi_engine,
    )

    for item in data.get("users", []):
        if "activity" not in item:
            raise NotImplementedError

        for activity_item in item["activity"]:
            if "activity_logs" in activity_item:
                for activity_log in activity_item["activity_logs"]:
                    ts = datetime.datetime.strftime(
                        datetime.datetime.now().astimezone(), DATETIME_MASK
                    )
                    record = {
                        "uid": item["userId"],
                        "sid": str(uuid4()),
                        "ts": ts,
                        "code": activity_log["name"],
                        "duration": parse_duration(activity_log),
                        "energy": parse_energy(activity_log),
                        "start": activity_log["start_time"],
                        "finish": parse_end_datetime(activity_log),
                        "provider": activity_log["metadata"]["source"],
                    }
                    write_record(record, dbapi_engine, records_table)


@auth_token
async def metriport_events_handler(request: web.Request):
    data = await request.json()

    # NOTE: https://docs.metriport.com/home/api-info/webhooks#the-ping-message
    if "ping" in data:
        return web.json_response({"pong": data["ping"]})

    try:
        await handle_activity_data(
            data, request.app["dbapi_engine"], request.app["dbapi_metadata"]
        )
    except NotImplementedError:
        # NOTE: All unhandled messages are written to a file
        with open(config.METRIPORT_UNHANDLED_DATA_FILENAME, "+a") as f:
            f.write(json.dumps(data))
            f.write("\n")

    return web.HTTPOk()
