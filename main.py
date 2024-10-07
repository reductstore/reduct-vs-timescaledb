from datetime import datetime
from time import sleep

import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import random
import time
import asyncio

from reduct import Client as ReductClient, Batch

BLOB_SIZE = 1000_000
BATCH_MAX_SIZE = 8_000_000
BATCH_MAX_RECORDS = 80

BLOB_COUNT = min(1000, 1_000_000_000 // BLOB_SIZE)

CHUNK = random.randbytes(BLOB_SIZE)

HOST = "localhost"
CONNECTION = f"postgresql://postgres:postgres@{HOST}:5432"


def setup_database():
    con = psycopg2.connect(CONNECTION)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
    cur.execute(f"DROP DATABASE IF EXISTS benchmark")
    cur.execute(f"CREATE DATABASE benchmark")
    con.commit()
    con.close()


def write_to_timescale():
    setup_database()

    with psycopg2.connect(CONNECTION + "/benchmark") as con:
        with con.cursor() as cur:
            cur.execute(
                f"""CREATE TABLE data (
                       time TIMESTAMPTZ NOT NULL,
                       blob_data BYTEA NOT NULL);
                """
            )
            cur.execute("SELECT create_hypertable('data', by_range('time'))")
            con.commit()

            count = 0
            values = []
            for i in range(0, BLOB_COUNT):
                values.append((datetime.now(), psycopg2.Binary(CHUNK)))
                sleep(0.000001)  # To avoid time collisions
                count += BLOB_SIZE

                if len(values) >= BATCH_MAX_RECORDS or len(values) * BLOB_SIZE >= BATCH_MAX_SIZE:
                    psycopg2.extras.execute_values(
                        cur,
                        "INSERT INTO data (time, blob_data) VALUES %s;",
                        values,
                    )
                    values = []


            if len(values) > 0:
                psycopg2.extras.execute_values(
                    cur,
                    "INSERT INTO data (time, blob_data) VALUES %s;",
                    values,
                )


    return count


def read_from_timescale(t1, t2):
    count = 0
    with psycopg2.connect(CONNECTION + "/benchmark") as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT blob_data FROM data WHERE time >= %s AND time < %s;",
                (datetime.fromtimestamp(t1), datetime.fromtimestamp(t2)),
            )
            while True:
                obj = cur.fetchone()
                if obj is None:
                    break
                count += len(obj[0])

    return count


async def write_to_reduct():
    async with ReductClient(
        f"http://{HOST}:8383", api_token="reductstore"
    ) as reduct_client:
        count = 0
        bucket = await reduct_client.get_bucket("benchmark")
        batch = Batch()
        for i in range(0, BLOB_COUNT):
            batch.add(timestamp=datetime.now().timestamp(), data=CHUNK)
            await asyncio.sleep(0.000001)  # To avoid time collisions
            count += BLOB_SIZE

            if  batch.size >= BATCH_MAX_SIZE or len(batch) >= BATCH_MAX_RECORDS:
                await bucket.write_batch("data", batch)
                batch.clear()

        if len(batch) > 0:
            await bucket.write_batch("data", batch)

        return count


async def read_from_reduct(t1, t2):
    async with ReductClient(
        f"http://{HOST}:8383", api_token="reductstore"
    ) as reduct_client:
        count = 0
        bucket = await reduct_client.get_bucket("benchmark")
        async for rec in bucket.query("data", t1, t2, ttl=90):
            count += len(await rec.read_all())
        return count


if __name__ == "__main__":
    print(f"Chunk size={BLOB_SIZE / 1000_000} Mb, count={BLOB_COUNT}")
    ts = time.time()
    size = write_to_timescale()
    print(f"Write {size / 1000_000} Mb to TimescaleDB: {BLOB_COUNT / (time.time() - ts)} req/s")

    ts_read = time.time()
    size = read_from_timescale(ts, time.time())
    print(f"Read {size / 1000_000} Mb from TimescaleDB: {BLOB_COUNT / (time.time() - ts_read)} req/s")

    loop = asyncio.new_event_loop()
    ts = time.time()
    size = loop.run_until_complete(write_to_reduct())
    print(f"Write {size / 1000_000} Mb to ReductStore: {BLOB_COUNT / (time.time() - ts)} req/s")

    ts_read = time.time()
    size = loop.run_until_complete(read_from_reduct(ts, time.time()))
    print(f"Read {size / 1000_000} Mb from ReductStore: {BLOB_COUNT / (time.time() - ts_read)} req/s")
