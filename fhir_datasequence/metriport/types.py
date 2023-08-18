from typing import Literal, TypedDict


class Meta(TypedDict):
    messageId: str
    when: str
    type: str


class MetaData(TypedDict):
    date: str
    source: str


class Duration(TypedDict):
    strain: dict[str, int]
    active_seconds: int


class HeartRate(TypedDict):
    max_bpm: int
    min_bpm: int


class Biometrics(TypedDict):
    heart_rate: HeartRate


class EnergyExpenditure(TypedDict):
    active_kcal: int | None
    basal_metabolic_rate_kcal: int | None
    total_watts: int | None
    avg_watts: int | None


class ActivityLogItem(TypedDict):
    name: str
    metadata: MetaData
    start_time: str
    movement: dict[Literal["steps_count"], int] | None
    durations: Duration | None
    energy_expenditure: EnergyExpenditure | None


class Activity(TypedDict):
    metadata: MetaData
    activity_logs: list[ActivityLogItem] | None


class UserData(TypedDict):
    userId: str
    activity: list[Activity] | None


class MetriportMessage(TypedDict):
    meta: Meta
    users: list[UserData]
