from fhirpy import AsyncFHIRClient

from fhir_datasequence import config


class UnableToAuthenticateRequestingActor(Exception):
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
    patient = await fhir_api.reference("Patient", patient_id).to_resource()
    consent = (
        await fhir_api.resources("Consent")
        .search(
            actor=requesting_actor.id,
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
