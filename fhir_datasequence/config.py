from os import environ


DBAPI_CONN_URL = f"postgresql+psycopg://{environ['PGUSER']}:{environ['PGPASSWORD']}@{environ['TIMESCALEDB_SERVICE_NAME']}"

APPLE_JWKS_API = "https://appleid.apple.com/auth/keys"
APPLE_OPENID_ISS_SERVICE = "https://appleid.apple.com"
APPLE_OPENID_AUD_CLIENT_ID = "software.beda.emr"

EMR_RECORDS_SERVICE_IDENTIFIER = environ.get(
    "EMR_RECORDS_ACCESS_ENDPOINT",
    "https://fhir.emr.beda.software/CodeSystem/consent-subject|emr-datasequence-records"
)

EMR_WEB_URL = environ.get("EMR_WEB_URL", "https://emr.beda.software")
EMR_FHIR_URL = environ.get("EMR_FHIR_URL", "https://aidbox.emr.beda.software")
