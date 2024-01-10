from aiohttp import web
from fhirpy import AsyncFHIRClient  # type: ignore
from fhirpy.base.exceptions import OperationOutcome  # type: ignore

from fhir_datasequence import config
from fhir_datasequence.auth import UserInfo, openid_userinfo
from fhir_datasequence.auth.fhir import get_fhir_patient_by_identifier, requires_consent
from fhir_datasequence.metriport.client import get_connect_token, get_user
from fhir_datasequence.metriport.db import read_records


@openid_userinfo(required=True)
async def connect_token_handler(request: web.Request, userinfo: UserInfo):
    session = request.app["metriport_client"]
    metriport_user_id = await get_user(session, userinfo.id)

    token_data, response_status = await get_connect_token(session, metriport_user_id)

    return web.json_response(
        {**token_data, "metriportUserId": metriport_user_id}, status=response_status
    )


def get_metriport_user_id(patient: dict):
    try:
        metriport_user_id = [
            identifier["value"]
            for identifier in patient.get("identifier", [])
            if identifier["system"] == config.METRIPORT_IDENTIFIER_SYSTEM_URL
        ][0]
    except IndexError:
        return None

    return metriport_user_id


@openid_userinfo(required=True)
async def read_metriport_records(request: web.Request, userinfo: UserInfo):
    fhir_api_client = AsyncFHIRClient(
        config.EMR_FHIR_URL, authorization=request["headers"]["Authorization"]
    )
    patient = await get_fhir_patient_by_identifier(
        fhir_api_client,
        identifier_system=config.APPLE_IDENTIFIER_SYSTEM_URL,
        identifier_value=userinfo.id,
    )

    metriport_user_id = get_metriport_user_id(patient)
    if not metriport_user_id:
        operation_outcome = OperationOutcome(
            reason="Metriport identifier does not specified for the patient"
        )
        return web.json_response(
            operation_outcome.resource,
            status=422,
        )
    records = await read_records(
        metriport_user_id,
        request.app["dbapi_engine"],
        request.app["dbapi_metadata"],
    )

    return web.json_response({"records": records})


@requires_consent()
async def share_metriport_records(request: web.Request, userinfo: UserInfo):
    fhir_api_client = AsyncFHIRClient(
        config.EMR_FHIR_URL, authorization=request["headers"]["Authorization"]
    )
    patient = await fhir_api_client.reference(
        "Patient", request.match_info["patient"]
    ).to_resource()
    metriport_user_id = get_metriport_user_id(patient)
    if not metriport_user_id:
        operation_outcome = OperationOutcome(
            reason="Metriport identifier does not specified for the patient"
        )
        return web.json_response(
            operation_outcome.resource,
            status=422,
        )
    records = await read_records(
        metriport_user_id,
        request.app["dbapi_engine"],
        request.app["dbapi_metadata"],
    )

    return web.json_response({"records": records})
