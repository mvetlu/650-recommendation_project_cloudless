# No-Cloud Baseline Performance (10 users dataset)

## Test Configuration
- Hardware: MacBook Pro 16" 2019, 8-core i9, 16GB RAM
- Database: PostgreSQL (localhost, single instance)
- API: FastAPI (single worker, no connection pooling)
- Dataset: 10 users, 1479 items, 1567 interactions

## Load Test Results

| Load Level | Users | P50 Latency | P95 Latency | P99 Latency | Throughput | Error Rate |
|------------|-------|-------------|-------------|-------------|------------|------------|
| Normal     | 10    | 18ms        | 34ms        | 45ms        | 73 req/s   | 0%         |
| Moderate   | 50    | 240ms       | 362ms       | 478ms       | 93 req/s   | 0%         |
| Heavy      | 200   | 1350ms      | 1616ms      | 1798ms      | 100 req/s  | 0%         |
| Extreme    | 500   | 4121ms      | 4414ms      | 4949ms      | 100 req/s  | 0%         |

## Observations
- System handled load without crashing
- Latency degraded significantly under heavy load (211x slower)
- Throughput capped at ~100 req/s (single-threaded bottleneck)
- No auto-scaling, fixed capacity