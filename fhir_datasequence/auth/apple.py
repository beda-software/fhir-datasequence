import functools
import logging
from collections.abc import Callable
from typing import cast

from aiohttp import ClientSession, web
from jwt import PyJWK, PyJWKSet, PyJWTError, decode, get_unverified_header

from fhir_datasequence import config
from fhir_datasequence.auth import (
    OpendIDSignatureValidationError,
    OpenIDSignatureKeyNotFoundError,
    UserInfo,
    authorization,
)


def apple_openid_userinfo(required: bool = True):
    def openid_userinfo_provider(api_handler: Callable):
        @authorization(required=required, kind="Bearer")
        @functools.wraps(api_handler)
        async def verify_id_token(request: web.Request, authorization: str):
            if authorization is None:
                return await api_handler(request, userinfo=None)
            try:
                verified = await verify_apple_id_token(authorization)
            except OpendIDSignatureValidationError as exc:
                logging.exception("OpenID token verification has failed")
                raise web.HTTPUnauthorized() from exc
            return await api_handler(request, userinfo=UserInfo(id=verified["sub"]))

        return verify_id_token

    return openid_userinfo_provider


apple_jwks: PyJWKSet | None = None


async def find_apple_openid_key(token: str) -> PyJWK | None:
    global apple_jwks

    unverified = get_unverified_header(token)

    if not apple_jwks:
        async with ClientSession() as session:
            async with session.get(config.APPLE_JWKS_API) as resp:
                apple_jwks = PyJWKSet.from_dict(await resp.json())

    return next(
        (
            k
            for k in cast(PyJWKSet, apple_jwks).keys
            if k.public_key_use == "sig" and k.key_id == unverified["kid"]
        ),
        None,
    )


async def verify_apple_id_token(token: str):
    openid_sig_key = await find_apple_openid_key(token)
    if not openid_sig_key:
        raise OpenIDSignatureKeyNotFoundError()
    try:
        return decode(
            token,
            openid_sig_key.key,
            algorithms=["RS256"],
            audience=[
                config.APPLE_OPENID_AUD_WEB_CLIENT_ID,
                config.APPLE_OPENID_AUD_MOBILE_CLIENT_ID,
            ],
            issuer=config.APPLE_OPENID_ISS_SERVICE,
            options={
                "verify_iat": True,
                "verify_nbf": True,
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": True,
            },
        )
    except PyJWTError as exc:
        raise OpendIDSignatureValidationError() from exc
