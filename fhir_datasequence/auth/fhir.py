from fhirpy import AsyncFHIRClient  # type: ignore

from fhir_datasequence import config


class UnableToAuthenticateRequestingActorError(Exception):
    pass


class RequestingActorConsentRoleIsMissingError(Exception):
    pass


class NoConsentIssuedError(Exception):
    pass


class ConsentProvisionDeniedError(Exception):
    pass


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
        if identifier.system == config.APPLE_OPENID_ISS_SERVICE
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
