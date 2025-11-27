# No-Cloud Costs:

## Laptop depreciation
MacBook Pro cost: ~$2500

Useful life: 4 years = 1460 days

Daily depreciation: $1.71/day

Plus electricity: ~$0.50/day (rough estimate)

Total: ~$2.20/day always-on

## Equivalent AWS EC2
t3.medium (2 vCPU, 4GB): $0.0416/hour

24/7: $0.0416 × 24 = $1.00/day

Plus RDS PostgreSQL db.t3.micro: $0.017/hour × 24 = $0.41/day

Total: ~$1.41/day always-on

[!]
Fixed cost regardless of load (0 users or 1000 users = same cost)