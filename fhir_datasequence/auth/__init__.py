import functools

from dataclasses import dataclass
from typing import Literal, Optional

from aiohttp import web
from aiohttp_apispec import headers_schema
from marshmallow import Schema, fields, validate

from fhir_datasequence.auth.openid import verify_apple_id_token


class AuthorizationSchema(Schema):
    Authorization = fields.Str(required=True)

    def __init__(self, required: bool = True, kind: Optional[Literal["Bearer"]] = None):
        super().__init__()
        self.fields["Authorization"].required = required
        if kind == "Bearer":
            self.fields["Authorization"].validate = validate.Regexp(regex=r"^Bearer ")


def authorization(required: bool = True, kind: Optional[Literal["Bearer"]] = None):
    def authorization_provider(api_handler):
        @headers_schema(schema=AuthorizationSchema(required=required, kind=kind))
        @functools.wraps(api_handler)
        async def read_authorization(request: web.Request):
            authorization_header = request.headers.get("Authorization")
            if authorization_header is None:
                # Authorization header presence is validated by openapi
                return await api_handler(authorization=None)
            if kind == "Bearer":
                authorization_header = authorization_header[len("Bearer ") :]
            return await api_handler(
                request=request, authorization=authorization_header
            )

        return read_authorization

    return authorization_provider


@dataclass
class UserInfo:
    id: str


def openid_userinfo(required: bool = True):
    def openid_userinfo_provider(api_handler):
        @authorization(required=required, kind="Bearer")
        @functools.wraps(api_handler)
        async def verify_id_token(request: web.Request, authorization: str):
            if authorization is None:
                return await api_handler(request, userinfo=None)
            verified = await verify_apple_id_token(authorization)
            return await api_handler(request, userinfo=UserInfo(id=verified["sub"]))

        return verify_id_token

    return openid_userinfo_provider
