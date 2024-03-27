# Benchmarks for TimescaleDB and ReductStore in Python


The benchmarks write and read blobs of different sizes to TimescaleDB and ReductStore. 
The benchmarks are written in Python and use the `psycopg2` and `reduct-py` libraries to interact with TimescaleDB and ReductStore,
respectively.


## Running

```
pip install -r requirements.txt
docker-compose up -d
python main.py
```

## Results

The script displays results for the specified `BLOB_SIZE` and `SIZE_COUNT`. On my device, which has an NVMe drive, here are the results I obtained:

| Chunk Size | Operation | TimescaleDB, blob/s | ReductStore, blob/s |
|------------|-----------|---------------------|---------------------|
| 10 KB      | Write     | 1557                | 1500                |
|            | Read      | 1333                | 1280                |
| 100 KB     | Write     | 447                 | 1366                |
|            | Read      | 353                 | 1120                |
| 1 MB       | Write     | 53                  | 571                 |
|            | Read      | 40                  | 382                 |
| 10 Mb      | Write     | 5                   | 70                  |
|            | Read      | 4                   | 38                  |