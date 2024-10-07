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

| Chunk Size | Operation | TimescaleDB, blob/s | ReductStore, blob/s | ReductStore, % |
|------------|-----------|---------------------|---------------------|----------------|
| 1 KB       | Write     | 3124                | 9322                | +198%          |
|            | Read      | 40300               | 51505               | +28%           |
| 10 KB      | Write     | 2114                | 8395                | +297%          |
|            | Read      | 10241               | 42322               | +313%          |
| 100 KB     | Write     | 491                 | 5026                | +924%          |
|            | Read      | 1602                | 11244               | +603%          |
| 1 MB       | Write     | 56                  | 898                 | +1604%         |
|            | Read      | 173                 | 1336                | +671%          |