from os import environ


DBAPI_CONN_URL = f"postgresql+psycopg://{environ['PGUSER']}:{environ['PGPASSWORD']}@{environ['TIMESCALEDB_SERVICE_NAME']}"
