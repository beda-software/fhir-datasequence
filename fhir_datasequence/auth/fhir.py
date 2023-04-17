from fhirpy import AsyncFHIRClient

from fhir_datasequence import config


class UnableToAuthenticateRequestingActor(Exception):
    pass


class RequestingActorConsentRoleIsMissing(Exception):
    pass


class NoConsentIssued(Exception):
    pass


class ConsentProvisionDenied(Exception):
    pass


async def verify_patient_consent(patient_id: str, subject: str, authorization: str):
    fhir_api = AsyncFHIRClient(config.EMR_FHIR_URL, authorization=authorization)
    requesting_actor = await fhir_api.execute("/auth/userinfo", method="GET")
    if requesting_actor is None:
        raise UnableToAuthenticateRequestingActor()
    requesting_actor_roles = extract_linked_roles(requesting_actor, role="practitioner")
    if not requesting_actor_roles:
        raise RequestingActorConsentRoleIsMissing()
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
        raise NoConsentIssued()
    if consent["provision"]["type"] != "permit":
        raise ConsentProvisionDenied()
    return next(
        identifier.value
        for identifier in patient.identifier
        if identifier.system == config.APPLE_OPENID_ISS_SERVICE
    )


def extract_linked_roles(actor, role=str):
    return (r.links[role].id for r in actor.role if role in r.links)
