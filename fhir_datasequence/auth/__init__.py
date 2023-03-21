import functools

from dataclasses import dataclass

from aiohttp import web
from aiohttp_apispec import headers_schema
from marshmallow import Schema, fields

from fhir_datasequence.auth.openid import verify_apple_id_token


class AuthorizationSchema(Schema):
    Authorization = fields.Str()


@dataclass
class UserInfo:
    id: str


def openid_userinfo(required: bool = True):
    def openid_userinfo_provider(api_handler):
        auth_schema = AuthorizationSchema()
        auth_schema.fields["Authorization"].required = required

        @headers_schema(schema=auth_schema)
        @functools.wraps(api_handler)
        async def authorize_id_token(request: web.Request):
            authorization = request.headers.get("Authorization")
            if not authorization:
                # Authorization header presence is validated by openapi
                return await api_handler(request, userinfo=None)
            if not authorization.startswith("Bearer "):
                raise web.HTTPUnauthorized()
            token = authorization[len("Bearer ") :]
            verified = await verify_apple_id_token(token)
            return await api_handler(request, userinfo=UserInfo(id=verified["sub"]))

        return authorize_id_token

    return openid_userinfo_provider
