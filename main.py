from datetime import datetime

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import random
import time
import asyncio

from reduct import Client as ReductClient

BLOB_SIZE = 100_000
BLOB_COUNT = min(1000, 1_000_000_000 // BLOB_SIZE)

CHUNK = random.randbytes(BLOB_SIZE)

HOST = "localhost"
CONNECTION = f"postgresql://postgres:postgres@{HOST}:5432"


def setup_timescale_table():
    con = psycopg2.connect(CONNECTION)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
    cur.execute(f"DROP DATABASE IF EXISTS benchmark")
    cur.execute(f"CREATE DATABASE benchmark")
    con.commit()
    con.close()


def write_to_timescale():
    setup_timescale_table()

    con = psycopg2.connect(CONNECTION + "/benchmark")
    cur = con.cursor()

    cur.execute(
        f"""
                       CREATE TABLE data (
                           time TIMESTAMPTZ NOT NULL,
                           blob_data BYTEA NOT NULL
                       );
                       """
    )
    cur.execute("SELECT create_hypertable('data', by_range('time'))")
    con.commit()

    count = 0
    for i in range(1, BLOB_COUNT):
        cur.execute(
            "INSERT INTO data (time, blob_data) VALUES (%s, %s);",
            (datetime.now(), psycopg2.Binary(CHUNK),),
        )
        count += BLOB_SIZE

    con.commit()
    con.close()
    return count


def read_from_timescale(t1, t2):
    con = psycopg2.connect(CONNECTION + "/benchmark")
    cur = con.cursor()
    count = 0
    cur.execute(
        "SELECT blob_data FROM data;",
        (datetime.fromtimestamp(t1), datetime.fromtimestamp(t2)),
    )
    while True:
        obj = cur.fetchone()
        if obj is None:
            break

        count += len(obj[0])
    con.close()
    return count


async def write_to_reduct():
    async with ReductClient(
            f"http://{HOST}:8383", api_token="reductstore"
    ) as reduct_client:
        count = 0
        bucket = await reduct_client.get_bucket("benchmark")
        for i in range(1, BLOB_COUNT):
            await bucket.write("data", CHUNK)
            count += BLOB_SIZE
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
    print(f"Write {size / 1000_000} Mb to TimescaleDB: {time.time() - ts} s")

    ts_read = time.time()
    size = read_from_timescale(ts, time.time())
    print(f"Read {size / 1000_000} Mb from TimescaleDB: {time.time() - ts_read} s")

    loop = asyncio.new_event_loop()
    ts = time.time()
    size = loop.run_until_complete(write_to_reduct())
    print(f"Write {size / 1000_000} Mb to ReductStore: {time.time() - ts} s")

    ts_read = time.time()
    size = loop.run_until_complete(read_from_reduct(ts, time.time()))
    print(f"Read {size / 1000_000} Mb from ReductStore: {time.time() - ts_read} s")
