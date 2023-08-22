import datetime
import logging
from uuid import uuid4

from aiohttp import web

from fhir_datasequence.metriport.db import write_activity_record, write_unhandled_data

DATETIME_MASK_WITH_MS = "%Y-%m-%dT%H:%M:%S.%f%z"
DATETIME_MASK = "%Y-%m-%dT%H:%M:%S%z"


def parse_datetime(datetime_value: str):
    parsed_value = None
    try:
        parsed_value = datetime.datetime.strptime(datetime_value, DATETIME_MASK_WITH_MS)
    except ValueError:
        try:
            parsed_value = datetime.datetime.strptime(datetime_value, DATETIME_MASK)
        except ValueError as err:
            logging.error(str(err))
    return parsed_value


def parse_end_datetime(activity_log_item: dict):
    if activity_log_item.get("end_time"):
        return activity_log_item["end_time"]
    parsed_start_datetime = None
    duration: int | None = None
    if activity_log_item.get("durations"):
        start_datetime: str = activity_log_item["start_time"]
        duration = activity_log_item["durations"]["active_seconds"]
        parsed_start_datetime = parse_datetime(start_datetime)

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


def prepare_db_record(activity_item: dict):
    ts = datetime.datetime.strftime(
        datetime.datetime.now().astimezone(), DATETIME_MASK_WITH_MS
    )

    start_time = parse_datetime(activity_item["start_time"])
    if not start_time:
        return {}

    return {
        "uid": activity_item["userId"],
        "sid": str(uuid4()),
        "ts": ts,
        "code": activity_item["name"],
        "duration": parse_duration(activity_item),
        "energy": parse_energy(activity_item),
        "start": start_time,
        "finish": parse_end_datetime(activity_item),
        "provider": activity_item["metadata"]["source"],
    }


def handle_activity_data(data: dict, app: web.Application):
    for activity_item in data["activity"]:
        for activity_log in activity_item.get("activity_logs", []):
            record = prepare_db_record({**activity_log, "userId": data["userId"]})
            write_activity_record(
                record, app["dbapi_engine"], app["metriport_records_table"]
            )


def default_handler(data: dict, app: web.Application):
    ts = datetime.datetime.strftime(
        datetime.datetime.now().astimezone(), DATETIME_MASK_WITH_MS
    )

    record = {"ts": ts, "uid": data["userId"], "data": data}
    write_unhandled_data(
        record, app["dbapi_engine"], app["metriport_unhandled_records_table"]
    )
