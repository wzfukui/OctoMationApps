# ActiveList Manager Performance Benchmark

## Test Environment

- Date: 2026-07-04
- Machine: local macOS development machine
- MySQL: Homebrew MySQL 9.7.1
- Python: local virtual environment under `/tmp/octomation-activelist-venv`
- Test database: `octomation_activelist_test`
- Test data: 10,000 randomly generated IP activity-list records
- Table: `_al_bench_10000`

The timing below measures the app action path, not only raw SQL. Each existence check creates a MySQL connection, executes one `COUNT(*)` query, reads the result, and closes the cursor and connection.

## Seed Data

10,000 rows were inserted in one `executemany` batch.

| Operation | Rows | Time |
| --- | ---: | ---: |
| Bulk insert seed records | 10,000 | 184.008 ms |

## Existence Check Timing

Each scenario ran 100 times after a warm-up pass.

| Scenario | Result | Count | Min | P50 | Average | P95 | Max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Key hit | exists | 1 | 1.887 ms | 3.946 ms | 3.410 ms | 4.293 ms | 4.583 ms |
| Key miss | missing | 0 | 2.483 ms | 3.516 ms | 3.577 ms | 4.197 ms | 4.474 ms |
| Value hit | exists | 1 | 2.156 ms | 5.323 ms | 4.614 ms | 5.671 ms | 5.967 ms |
| Key and value hit | exists | 1 | 2.620 ms | 3.743 ms | 3.775 ms | 4.425 ms | 4.637 ms |
| Key and value miss | missing | 0 | 2.267 ms | 5.383 ms | 4.588 ms | 5.819 ms | 6.473 ms |
| Key and value hit within 60 minutes | exists | 1 | 3.374 ms | 5.667 ms | 5.469 ms | 5.900 ms | 6.162 ms |

## Index Verification

The benchmark table was created with the same indexes as `initialize_active_list_table`, including:

- `idx_al_key`
- `idx_al_value`
- `idx_al_create_time`
- `idx_al_update_time`
- `idx_al_key_create_time`
- `idx_al_value_create_time`
- `idx_al_key_value_create_time`

For the key+value+time-window query, MySQL 9 returned this `EXPLAIN` tree:

```text
-> Aggregate: count(0)  (cost=0.267 rows=1)
    -> Filter: ((_al_bench_10000._key = '10.0.21.56') and (_al_bench_10000._value = '172.16.136.186') and (_al_bench_10000.create_time between <cache>((now() - interval 60 minute)) and <cache>(now())))  (cost=0.255 rows=0.05)
        -> Index lookup on _al_bench_10000 using idx_al_key (_key = '10.0.21.56')  (cost=0.255 rows=1)
```

This confirms the existence check used an index lookup in the 10,000-row test.

## Notes

- These numbers are local-development results and should be treated as a reference point, not a production SLA.
- A long-running production deployment still needs retention cleanup for append-heavy activity lists.
- If many records share the same `_key`, a more selective composite index or a uniqueness strategy may be needed for that workload.
