from os import environ


DBAPI_CONN_URL = f"postgresql+psycopg://{environ['PGUSER']}:{environ['PGPASSWORD']}@timescaledb"
