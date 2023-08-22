from aiohttp import ClientResponse, ClientSession, web

from fhir_datasequence import config


async def attach(app: web.Application):
    session = ClientSession(
        config.METRIPORT_API_BASE_URL,
        headers={config.METRIPORT_API_KEY_REQUEST_HEADER: config.METRIPORT_API_SECRET},
    )
    app["metriport_client"] = session

    yield

    await app["metriport_client"].close()


async def get_user(session: ClientSession, app_user_id: str):
    async with session.post("/user", params={"appUserId": app_user_id}) as resp:
        data, _status = await handle_response(resp)
        return data["userId"]


async def get_connect_token(session: ClientSession, user_id: str):
    async with session.get("/user/connect/token", params={"userId": user_id}) as resp:
        return await handle_response(resp)


async def handle_response(response: ClientResponse):
    if 200 <= response.status < 300:
        data = await response.json()
        return (data, response.status)
    # NOTE: should we handle errors or aiohttp raises appropriate exception itself?
    raise web.HTTPClientError(text=await response.text())
