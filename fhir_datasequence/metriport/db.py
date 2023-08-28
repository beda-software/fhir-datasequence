import sqlalchemy
from sqlalchemy import MetaData, Row, and_, insert, select, update
from sqlalchemy.ext.asyncio import AsyncEngine

from fhir_datasequence.metriport import (
    METRIPORT_RECORDS_TABLE_NAME,
    METRIPORT_UNHANDLED_RECORDS_TABLE_NAME,
)


async def write_activity_record(
    record: dict, dbapi_engine: AsyncEngine, metadata: MetaData
):
    async with dbapi_engine.begin() as connection:
        table = await connection.run_sync(
            lambda conn: sqlalchemy.Table(
                METRIPORT_RECORDS_TABLE_NAME,
                metadata,
                autoload_with=conn,
            )
        )
        exists_record = (
            await connection.execute(
                select(table).where(
                    and_(
                        table.c.uid == record["uid"],
                        table.c.start == record["start"],
                        table.c.provider == record["provider"],
                    )
                )
            )
        ).first()

        if exists_record:
            await connection.execute(
                update(table).where(table.c.ts == exists_record.ts).values(**record)
            )
        else:
            await connection.execute(insert(table), record)


def parse_row(row: Row):
    return {
        "uid": row.uid,
        "sid": row.sid,
        "ts": row.ts.isoformat(),
        "code": row.code,
        "duration": row.duration,
        "energy": row.energy,
        "start": row.start.isoformat(),
        "finish": row.finish.isoformat(),
        "provider": row.provider,
    }


async def write_unhandled_data(
    record: dict, dbapi_engine: AsyncEngine, metadata: MetaData
):
    async with dbapi_engine.begin() as connection:
        table = await connection.run_sync(
            lambda conn: sqlalchemy.Table(
                METRIPORT_UNHANDLED_RECORDS_TABLE_NAME,
                metadata,
                autoload_with=conn,
            )
        )
        await connection.execute(insert(table), record)


async def read_records(user_id: str, dbapi_engine: AsyncEngine, metadata: MetaData):
    async with dbapi_engine.begin() as connection:
        table = await connection.run_sync(
            lambda conn: sqlalchemy.Table(
                METRIPORT_RECORDS_TABLE_NAME,
                metadata,
                autoload_with=conn,
            )
        )
        return [
            parse_row(row)
            for row in await connection.execute(
                select(table).where(table.c.uid == user_id).order_by(table.c.ts.desc())
            )
        ]
