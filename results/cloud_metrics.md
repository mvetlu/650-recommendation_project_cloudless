# Cloud (AWS) Performance Metrics

## Test Configuration
- **Architecture:** AWS Lambda + DynamoDB + API Gateway
- **Region:** us-east-1 (N. Virginia)
- **Lambda:** 512 MB memory, Python 3.12, concurrency limit: 10
- **DynamoDB:** On-demand pricing, 4 tables
- **API Gateway:** REST API, regional endpoint
- **WAF:** Rate limiting (100 req per 5 min per IP)
- **Test Dataset:** 10 users, 1479 items, 1567 interactions

## Load Test Results

| Load Level | Users | P50 Latency | P95 Latency | P99 Latency | Throughput | Error Rate |
|------------|-------|-------------|-------------|-------------|------------|------------|
| Light      | 5     | 31ms        | 42ms        | 64ms        | 36 req/s   | 0%         |
| Normal     | 10    | 30ms        | 39ms        | 57ms        | 62 req/s   | 0%         |
| Moderate   | 15    | 30ms        | 39ms        | 53ms        | 100 req/s  | 3%         |
| Heavy      | 25    | 31ms        | 41ms        | 55ms        | 170 req/s  | 41%        |

## Key Observations

### Performance Characteristics
- **Consistent latency:** P50 remained 30-31ms across all load levels
- **No latency degradation:** Unlike no-cloud (18ms → 4100ms), cloud maintained stable response times
- **Graceful failure:** At overload, errors increased but successful requests stayed fast
- **Cold start impact:** Initial requests ~700ms (Lambda initialization), subsequent ~30ms

### Scalability
- **Auto-scaling:** Lambda automatically handled concurrent requests up to limit
- **Concurrency limit:** Set to 10 (free tier constraint), could increase to 1000+ in production
- **Throttling behavior:** Returned HTTP 500 when exceeding capacity (proper error handling)
- **No manual intervention:** System continued operating under overload without crash