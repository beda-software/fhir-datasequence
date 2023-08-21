from aiohttp import ClientSession, web
from aiohttp_apispec import json_schema, querystring_schema  # type: ignore
from marshmallow import Schema, fields
from sqlalchemy import Table, select

from fhir_datasequence import config
from fhir_datasequence.auth import UserInfo, openid_userinfo, requires_consent
from fhir_datasequence.metriport import METRIPORT_RECORDS_TABLE_NAME

RequestQueryParamsSchema = Schema.from_dict(
    {"metriportUserId": fields.Str(required=True)}
)

GetTokenRequestBodySchema = Schema.from_dict({"userId": fields.Str(required=True)})


@openid_userinfo(required=True)
@json_schema(GetTokenRequestBodySchema())
async def connect_token_handler(request: web.Request, userinfo: UserInfo):
    # Move to app init
    async with ClientSession(
        config.METRIPORT_API_BASE_URL,
        headers={config.METRIPORT_API_KEY_REQUEST_HEADER: config.METRIPORT_API_SECRET},
    ) as session:
        # get userId from userinfo
        metriport_user_id = None
        async with session.post(
            "/user", params={"appUserId": request["json"]["userId"]}
        ) as resp:
            if resp.status != 200:
                return web.json_response(await resp.json(), status=resp.status)

            data = await resp.json()
            metriport_user_id = data["userId"]

        async with session.get(
            "/user/connect/token", params={"userId": metriport_user_id}
        ) as resp:
            data = await resp.json()
            return web.json_response(
                {**data, "metriportUserId": metriport_user_id}, status=resp.status
            )


@openid_userinfo(required=True)
@querystring_schema(RequestQueryParamsSchema())
async def read_metriport_records(request: web.Request, userinfo: UserInfo):
    records_table = Table(
        METRIPORT_RECORDS_TABLE_NAME,
        request.app["dbapi_metadata"],
        autoload_with=request.app["dbapi_engine"],
    )

    metriport_user_id = request["querystring"]["metriportUserId"]
    with request.app["dbapi_engine"].begin() as connection:
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
                "provider": row.provider,
            }
            for row in connection.execute(
                select(records_table)
                .where(records_table.c.uid == metriport_user_id)
                .order_by(records_table.c.ts.desc())
            )
        ]
    return web.json_response({"records": records})


@requires_consent()
@querystring_schema(RequestQueryParamsSchema())
async def share_metriport_records(request: web.Request, userinfo: UserInfo):
    records_table = Table(
        METRIPORT_RECORDS_TABLE_NAME,
        request.app["dbapi_metadata"],
        autoload_with=request.app["dbapi_engine"],
    )
    metriport_user_id = request["querystring"]["metriportUserId"]
    with request.app["dbapi_engine"].begin() as connection:
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
                "provider": row.provider,
            }
            for row in connection.execute(
                select(records_table)
                .where(records_table.c.uid == metriport_user_id)
                .order_by(records_table.c.ts.desc())
            )
        ]
    return web.json_response({"records": records})
