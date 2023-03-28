import functools

from dataclasses import dataclass

from aiohttp import web
from aiohttp_apispec import headers_schema
from marshmallow import Schema, fields, validate

from fhir_datasequence.auth.openid import verify_apple_id_token


class AuthorizationSchema(Schema):
    Authorization = fields.Str(validate=validate.Regexp(regex=r"^Bearer "))


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
            if authorization is None:
                # Authorization header presence is validated by openapi
                return await api_handler(request, userinfo=None)
            token = authorization[len("Bearer ") :]
            verified = await verify_apple_id_token(token)
            return await api_handler(request, userinfo=UserInfo(id=verified["sub"]))

        return authorize_id_token

    return openid_userinfo_provider
