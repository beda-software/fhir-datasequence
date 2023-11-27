import functools
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from aiohttp import web
from aiohttp_apispec import headers_schema
from jwt import PyJWTError, decode
from marshmallow import Schema, fields, validate

from fhir_datasequence import config


class OpenIDSignatureKeyNotFoundError(Exception):
    pass


class OpendIDSignatureValidationError(Exception):
    pass


class AuthorizationSchema(Schema):
    Authorization = fields.Str(required=True)

    def __init__(
        self: "AuthorizationSchema",
        required: bool = True,
        kind: Literal["Bearer"] | None = None,
    ) -> None:
        super().__init__()
        self.fields["Authorization"].required = required
        if kind == "Bearer":
            bearer_format = validate.Regexp(regex=r"^Bearer ")
            self.fields["Authorization"].validate = bearer_format
            self.fields["Authorization"].validators = [bearer_format]


def authorization(required: bool = True, kind: Literal["Bearer"] | None = None):
    def authorization_provider(api_handler: Callable):
        @headers_schema(schema=AuthorizationSchema(required=required, kind=kind))
        @functools.wraps(api_handler)
        async def read_authorization(request: web.Request):
            authorization_header = request.headers.get("Authorization")
            if authorization_header:
                match kind:
                    case "Bearer":
                        # Authorization header presence is validated by openapi
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
    def openid_userinfo_provider(api_handler: Callable):
        @authorization(required=required, kind="Bearer")
        @functools.wraps(api_handler)
        async def verify_id_token(request: web.Request, authorization: str):
            if authorization is None:
                return await api_handler(request, userinfo=None)
            try:
                verified = await verify_user_id_token(authorization)
            except OpendIDSignatureValidationError as exc:
                logging.exception("OpenID token verification has failed")
                raise web.HTTPUnauthorized() from exc
            return await api_handler(request, userinfo=UserInfo(id=verified["sub"]))

        return verify_id_token

    return openid_userinfo_provider


async def verify_user_id_token(token: str):
    try:
        return decode(
            token,
            config.JWT_TOKEN_ENCODE_SECRET,
            algorithms=["HS256"],
            audience=[
                config.APPLE_OPENID_AUD_MOBILE_CLIENT_ID,
                config.APPLE_OPENID_AUD_WEB_CLIENT_ID,
            ],
            issuer=config.DATA_SEQUENCE_OPENID_ISS_SERVICE,
            options={
                "verify_exp": False,
                "verify_iss": True,
                "verify_aud": True,
            },
        )
    except PyJWTError as exc:
        raise OpendIDSignatureValidationError() from exc
