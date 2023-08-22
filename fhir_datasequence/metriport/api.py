from aiohttp import web
from aiohttp_apispec import json_schema, querystring_schema  # type: ignore
from marshmallow import Schema, fields
from sqlalchemy import Table, select

from fhir_datasequence.auth import UserInfo, openid_userinfo, requires_consent
from fhir_datasequence.metriport import METRIPORT_RECORDS_TABLE_NAME
from fhir_datasequence.metriport.client import get_connect_token, get_user
from fhir_datasequence.metriport.db import parse_row

RequestQueryParamsSchema = Schema.from_dict(
    {"metriportUserId": fields.Str(required=True)}
)

GetTokenRequestBodySchema = Schema.from_dict({"userId": fields.Str(required=True)})


@openid_userinfo(required=True)
@json_schema(GetTokenRequestBodySchema())
async def connect_token_handler(request: web.Request, userinfo: UserInfo):
    async with request.app["metriport_client"] as session:
        # get userId from userinfo
        metriport_user_id = await get_user(session, request["json"]["userId"])
        token_data, response_status = await get_connect_token(
            session, metriport_user_id
        )

        return web.json_response(
            {**token_data, "metriportUserId": metriport_user_id}, status=response_status
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
            parse_row(row)
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
            parse_row(row)
            for row in connection.execute(
                select(records_table)
                .where(records_table.c.uid == metriport_user_id)
                .order_by(records_table.c.ts.desc())
            )
        ]
    return web.json_response({"records": records})
