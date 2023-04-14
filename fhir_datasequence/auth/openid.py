from typing import Optional, cast

from aiohttp import web, ClientSession
from jwt import PyJWKSet, PyJWK, decode, get_unverified_header

from fhir_datasequence import config


class OpenIDSignatureKeyNotFound(Exception):
    pass


class OpendIDSignatureValidationError(Exception):
    pass


apple_jwks: Optional[PyJWKSet] = None


async def find_apple_openid_key(token: str) -> Optional[PyJWK]:
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
        raise OpenIDSignatureKeyNotFound()
    try:
        return decode(
            token,
            openid_sig_key.key,
            algorithms=["RS256"],
            audience=config.APPLE_OPENID_AUD_CLIENT_ID,
            issuer=config.APPLE_OPENID_ISS_SERVICE,
            options={
                "verify_iat": True,
                "verify_nbf": True,
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": True,
            },
        )
    except:
        raise OpendIDSignatureValidationError()
