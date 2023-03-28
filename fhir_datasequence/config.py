from os import environ


DBAPI_CONN_URL = f"postgresql+psycopg://{environ['PGUSER']}:{environ['PGPASSWORD']}@{environ['TIMESCALEDB_SERVICE_NAME']}"

APPLE_JWKS_API = "https://appleid.apple.com/auth/keys"
APPLE_OPENID_ISS_SERVICE = "https://appleid.apple.com"
APPLE_OPENID_AUD_CLIENT_ID = "software.beda.emr"

EMR_WEB_URL = environ.get("EMR_WEB_URL", "https://emr.beda.software")
