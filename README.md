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
| 1 KB       | Write     | 3124                | 9322                |
|            | Read      | 40300               | 51505               |
| 10 KB      | Write     | 2114                | 8395                |
|            | Read      | 10241               | 42322               |
| 100 KB     | Write     | 491                 | 5026                |
|            | Read      | 1602                | 11244               |
| 1 Mb       | Write     | 56                  | 898                 |
|            | Read      | 173                 | 1336                |