import functools
import logging
from collections.abc import Callable

from aiohttp import web
from aiohttp_apispec import match_info_schema
from fhirpy import AsyncFHIRClient
from marshmallow import Schema, fields

from fhir_datasequence import config
from fhir_datasequence.auth import UserInfo, authorization


class UnableToAuthenticateRequestingActorError(Exception):
    pass


class RequestingActorConsentRoleIsMissingError(Exception):
    pass


class NoConsentIssuedError(Exception):
    pass


class ConsentProvisionDeniedError(Exception):
    pass


class ConsentPatientMatchInfoSchema(Schema):
    patient = fields.UUID(required=True, description="Consent patient identifier")


def requires_consent():
    def consent_validator(api_handler: Callable):
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
            except (
                UnableToAuthenticateRequestingActorError,
                RequestingActorConsentRoleIsMissingError,
                NoConsentIssuedError,
                ConsentProvisionDeniedError,
            ) as exc:
                logging.exception("Access Consent verification has failed")
                raise web.HTTPForbidden() from exc
            return await api_handler(request, userinfo=UserInfo(id=userid))

        return validate_consent

    return consent_validator


async def verify_patient_consent(patient_id: str, subject: str, authorization: str):
    fhir_api = AsyncFHIRClient(config.EMR_FHIR_URL, authorization=authorization)
    requesting_actor = await fhir_api.execute("/auth/userinfo", method="GET")
    if requesting_actor is None:
        raise UnableToAuthenticateRequestingActorError()
    requesting_actor_roles = extract_linked_roles(requesting_actor, role="practitioner")
    if not requesting_actor_roles:
        raise RequestingActorConsentRoleIsMissingError()
    patient = await fhir_api.reference("Patient", patient_id).to_resource()
    consent = (
        await fhir_api.resources("Consent")
        .search(
            actor=",".join(requesting_actor_roles),
            patient=patient.id,
            status="active",
            action="access",
            scope="patient-privacy",
            category="INFAO",
            purpose="CAREMGT",
            data__Endpoint__identifier=subject,
        )
        .first()
    )
    if consent is None:
        raise NoConsentIssuedError()
    if consent["provision"]["type"] != "permit":
        raise ConsentProvisionDeniedError()
    return next(
        identifier.value
        for identifier in patient.identifier
        if identifier.system == config.DATA_SEQUENCE_OPENID_ISS_SERVICE
    )


def extract_linked_roles(actor: dict, role: str):
    return (r.links[role].id for r in actor["role"] if role in r.links)


async def get_fhir_patient_by_identifier(
    client: AsyncFHIRClient, *, identifier_system: str, identifier_value: str
):
    return (
        await client.resources("Patient")
        .search(identifier=f"{identifier_system}|{identifier_value}")
        .get()
    )
