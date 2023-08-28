from aiohttp import web
from aiohttp_apispec import docs, json_schema, response_schema  # type: ignore
from marshmallow import Schema, fields, validate
from sqlalchemy import Table, insert, select
from sqlalchemy.ext.asyncio import AsyncEngine

from fhir_datasequence.auth import UserInfo, openid_userinfo, requires_consent


class RecordSchema(Schema):
    sid = fields.Str(required=True)
    ts = fields.DateTime(format="iso", required=True)
    code = fields.Str(required=True)
    duration = fields.Integer(strict=True)
    energy = fields.Integer(strict=True)
    start = fields.DateTime(format="iso", required=True)
    finish = fields.DateTime(format="iso", required=True)


class RecordsListSchema(Schema):
    records = fields.List(
        fields.Nested(RecordSchema), required=True, validate=validate.Length(min=1)
    )


class SuccessResponseSchema(Schema):
    status = fields.Constant("OK")


@docs(summary="Ingest time series data")
@json_schema(RecordsListSchema())
@response_schema(
    SuccessResponseSchema(),
    code=200,
    description="Time series data has been successfully persisted",
)
@openid_userinfo(required=False)
async def write_health_records(request: web.Request, userinfo: UserInfo | None):
    engine: AsyncEngine = request.app["dbapi_engine"]
    async with engine.begin() as connection:
        records_table = await connection.run_sync(
            lambda conn: Table(
                "records",
                request.app["dbapi_metadata"],
                autoload_with=conn,
            )
        )
        await connection.execute(
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


@docs(summary="Access time series data for a given openid user")
@response_schema(
    RecordsListSchema(),
    code=200,
    description="Array of records associated with a given openid user",
)
@openid_userinfo(required=True)
async def read_health_records(request: web.Request, userinfo: UserInfo):
    engine: AsyncEngine = request.app["dbapi_engine"]
    async with engine.begin() as connection:
        records_table = await connection.run_sync(
            lambda conn: Table(
                "records",
                request.app["dbapi_metadata"],
                autoload_with=conn,
            )
        )
        records = [
            {
                "uid": row.uid,
                "sid": row.sid,
                "ts": row.ts.isoformat(),
                "code": row.code,
                "duration": row.duration,
                "energy": row.energy,
                "start": row.start.isoformat(),
                "finish": row.finish.isoformat(),
            }
            for row in await connection.execute(
                select(records_table)
                .where(records_table.c.uid == userinfo.id)
                .order_by(records_table.c.ts.desc())
            )
        ]
    return web.json_response({"records": records})


@docs(summary="Access time series data shared by patient")
@response_schema(
    RecordsListSchema(),
    code=200,
    description="Array of records shared by patient",
)
@requires_consent()
async def share_health_records(request: web.Request, userinfo: UserInfo):
    engine: AsyncEngine = request.app["dbapi_engine"]
    async with engine.begin() as connection:
        records_table = await connection.run_sync(
            lambda conn: Table(
                "records",
                request.app["dbapi_metadata"],
                autoload_with=conn,
            )
        )
        records = [
            {
                "uid": row.uid,
                "sid": row.sid,
                "ts": row.ts.isoformat(),
                "code": row.code,
                "duration": row.duration,
                "energy": row.energy,
                "start": row.start.isoformat(),
                "finish": row.finish.isoformat(),
            }
            for row in await connection.execute(
                select(records_table)
                .where(records_table.c.uid == userinfo.id)
                .order_by(records_table.c.ts.desc())
            )
        ]
    return web.json_response({"records": records})
