from typing import Optional

import sqlalchemy

from aiohttp import web
from sqlalchemy import MetaData, Table, insert
from aiohttp_apispec import json_schema, docs, response_schema
from marshmallow import Schema, fields, validate

from fhir_datasequence import config
from fhir_datasequence.auth import UserInfo, openid_userinfo

dbapi_engine = sqlalchemy.create_engine(config.DBAPI_CONN_URL)
dbapi_metadata = MetaData()


class RecordSchema(Schema):
    sid = fields.Str(required=True)
    ts = fields.DateTime(format="iso", required=True)
    code = fields.Str(required=True)
    duration = fields.Integer(strict=True)
    energy = fields.Integer(strict=True)
    start = fields.DateTime(format="iso", required=True)
    finish = fields.DateTime(format="iso", required=True)


class IngestRecordsRequestSchema(Schema):
    records = fields.List(
        fields.Nested(RecordSchema), required=True, validate=validate.Length(min=1)
    )


class IngestRecordsResponseSchema(Schema):
    status = fields.Constant("OK")


@docs(summary="Ingest time series data")
@json_schema(IngestRecordsRequestSchema())
@response_schema(
    IngestRecordsResponseSchema(),
    code=200,
    description="Time series data has been successfuly persisted",
)
@openid_userinfo(required=False)
async def ingest_health_records(request: web.Request, userinfo: Optional[UserInfo]):
    records_table = Table("records", dbapi_metadata, autoload_with=dbapi_engine)
    with dbapi_engine.begin() as connection:
        connection.execute(
            insert(records_table),
            [
                {
                    "uid": userinfo.id if userinfo else None,
                    "sid": record["sid"],
                    "ts": record["ts"],
                    "code": record["code"],
                    "duration": record.get("duration"),
                    "energy": record.get("energy"),
                    "start": record.get("start"),
                    "finish": record.get("finish"),
                }
                for record in request["json"]["records"]
            ],
        )
    return web.json_response({"status": "OK"})
