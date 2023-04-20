import functools
import logging

from dataclasses import dataclass
from typing import Literal, Optional

from aiohttp import web
from aiohttp_apispec import headers_schema, match_info_schema
from marshmallow import Schema, fields, validate

from fhir_datasequence import config
from fhir_datasequence.auth.fhir import verify_patient_consent
from fhir_datasequence.auth.openid import verify_apple_id_token


class AuthorizationSchema(Schema):
    Authorization = fields.Str(required=True)

    def __init__(self, required: bool = True, kind: Optional[Literal["Bearer"]] = None):
        super().__init__()
        self.fields["Authorization"].required = required
        if kind == "Bearer":
            bearer_format = validate.Regexp(regex=r"^Bearer ")
            self.fields["Authorization"].validate = bearer_format
            self.fields["Authorization"].validators = [bearer_format]


def authorization(required: bool = True, kind: Optional[Literal["Bearer"]] = None):
    def authorization_provider(api_handler):
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
    def openid_userinfo_provider(api_handler):
        @authorization(required=required, kind="Bearer")
        @functools.wraps(api_handler)
        async def verify_id_token(request: web.Request, authorization: str):
            if authorization is None:
                return await api_handler(request, userinfo=None)
            try:
                verified = await verify_apple_id_token(authorization)
            except:
                logging.exception("OpenID token verification has failed")
                raise web.HTTPUnauthorized()
            return await api_handler(request, userinfo=UserInfo(id=verified["sub"]))

        return verify_id_token

    return openid_userinfo_provider


class ConsentPatientMatchInfoSchema(Schema):
    patient = fields.UUID(required=True, description="Consent patient identifier")


def requires_consent():
    def consent_validator(api_handler):
        @authorization(required=True)
        @match_info_schema(ConsentPatientMatchInfoSchema())
        @functools.wraps(api_handler)
        async def validate_consent(request: web.Request, authorization: str):
            try:
                userid = await verify_patient_consent(
                    patient_id=request.match_info["patient"],
                    subject=config.EMR_RECORDS_SERVICE_IDENTIFIER,
                    authorization=authorization,
                )
            except:
                logging.exception("Access Consent verification has failed")
                raise web.HTTPForbidden()
            return await api_handler(request, userinfo=UserInfo(id=userid))

        return validate_consent

    return consent_validator
