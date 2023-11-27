from aiohttp import web
from jwt import encode

from fhir_datasequence import config
from fhir_datasequence.auth import UserInfo
from fhir_datasequence.auth.apple import apple_openid_userinfo


@apple_openid_userinfo()
async def fetch_auth_token_handler(request: web.Request, userinfo: UserInfo):
    token = encode(
        {
            "aud": [
                config.APPLE_OPENID_AUD_MOBILE_CLIENT_ID,
                config.APPLE_OPENID_AUD_WEB_CLIENT_ID,
            ],
            "iss": config.DATA_SEQUENCE_OPENID_ISS_SERVICE,
            "sub": userinfo.id,
        },
        config.JWT_TOKEN_ENCODE_SECRET,
        algorithm="HS256",
    )

    return web.json_response({"access_token": token})
