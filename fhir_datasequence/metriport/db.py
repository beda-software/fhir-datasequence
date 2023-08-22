from sqlalchemy import Engine, Row, Table, and_, insert, select, update


def write_activity_record(record: dict, dbapi_engine: Engine, table: Table):
    with dbapi_engine.begin() as connection:
        exists_record = connection.execute(
            select(table).where(
                and_(
                    table.c.uid == record["uid"],
                    table.c.start == record["start"],
                    table.c.provider == record["provider"],
                )
            )
        ).first()

        if exists_record:
            connection.execute(
                update(table).where(table.c.ts == exists_record.ts).values(**record)
            )
        else:
            connection.execute(insert(table), record)


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


def write_unhandled_data(record: dict, dbapi_engine: Engine, table: Table):
    with dbapi_engine.begin() as connection:
        connection.execute(insert(table), record)
