import datetime
import logging
from uuid import uuid4

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


def handle_activity_data(data: dict):
    for item in data.get("users", []):
        # Handle all keys (see data model)
        # Create map to work with each key (default handler, activity handler)
        if "activity" not in item:
            raise NotImplementedError

        for activity_item in item["activity"]:
            if "activity_logs" in activity_item:
                return map(prepare_db_record, activity_item["activity_logs"])
