from aiohttp import ClientSession, web
from aiohttp_apispec import json_schema  # type: ignore
from marshmallow import Schema, fields

from fhir_datasequence import config
from fhir_datasequence.auth import UserInfo, openid_userinfo

RequestBodySchema = Schema.from_dict({"userId": fields.Str(required=True)})


@openid_userinfo(required=True)
@json_schema(RequestBodySchema())
async def connect_token_handler(request: web.Request, userinfo: UserInfo):
    async with ClientSession(
        config.METRIPORT_API_BASE_URL,
        headers={config.METRIPORT_API_KEY_REQUEST_HEADER: config.METRIPORT_API_SECRET},
    ) as session:
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
