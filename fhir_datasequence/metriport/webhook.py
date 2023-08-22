from aiohttp import web

from fhir_datasequence.metriport.client import authorize_webhook
from fhir_datasequence.metriport.utils import default_handler, handle_activity_data

event_handler_map = {
    "activity": handle_activity_data,
    "sleep": default_handler,
    "biometrics": default_handler,
    "body": default_handler,
    "nutrition": default_handler,
    "user": default_handler,
}


@authorize_webhook
async def metriport_events_handler(request: web.Request):
    data = await request.json()

    # NOTE: https://docs.metriport.com/home/api-info/webhooks#the-ping-message
    if "ping" in data:
        return web.json_response({"pong": data["ping"]})

    for user in data.get("users", []):
        for event_name, event_data in user.items():
            handler = event_handler_map.get(event_name, default_handler)
            handler({event_name: event_data, "userId": user["userId"]}, request.app)

    return web.HTTPOk()
