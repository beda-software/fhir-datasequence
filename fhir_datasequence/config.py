from os import environ


DBAPI_CONN_URL = f"postgresql+psycopg://{environ['PGUSER']}:{environ['PGPASSWORD']}@{environ['TIMESCALEDB_SERVICE_NAME']}"

APPLE_JWKS_API = "https://appleid.apple.com/auth/keys"
APPLE_OPENID_ISS_SERVICE = "https://appleid.apple.com"
APPLE_OPENID_AUD_WEB_CLIENT_ID = "software.beda.emr"
APPLE_OPENID_AUD_MOBILE_CLIENT_ID = "software.beda.fhirmhealth.fhirmhealth"

EMR_RECORDS_SERVICE_IDENTIFIER = environ.get(
    "EMR_RECORDS_ACCESS_ENDPOINT",
    "https://fhir.emr.beda.software/CodeSystem/consent-subject|emr-datasequence-records",
)

EMR_WEB_URL = environ.get("EMR_WEB_URL", "https://emr.beda.software")
EMR_FHIR_URL = environ.get("EMR_FHIR_URL", "https://aidbox.emr.beda.software")

METRIPORT_API_MAIN_URL = environ.get(
    "METRIPORT_API_MAIN_URL", "https://api.metriport.com"
)
METRIPORT_API_SANDBOX_URL = environ.get(
    "METRIPORT_API_SANDBOX_URL", "https://api.sandbox.metriport.com"
)
METRIPORT_USE_SANDBOX = environ.get("METRIPORT_USE_SANDBOX", False)
METRIPORT_API_BASE_URL = (
    METRIPORT_API_SANDBOX_URL if METRIPORT_USE_SANDBOX else METRIPORT_API_MAIN_URL
)
METRIPORT_API_KEY_REQUEST_HEADER = environ.get(
    "METRIPORT_API_KEY_REQUEST_HEADER", "x-api-key"
)
METRIPORT_WEBHOOK_AUTH_KEY = environ.get("METRIPORT_WEBHOOK_AUTH_KEY")
