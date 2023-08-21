from sqlalchemy import Engine, Table, and_, insert, select, update


def write_record(record: dict, dbapi_engine: Engine, table: Table):
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
