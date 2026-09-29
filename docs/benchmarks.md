# Benchmarks

Environment: Ubuntu, single node, Redis 7 (native), Python 3.14.

## Retry backoff (PROVIDER_FAIL_RATE=1.0)
Delays follow 1/2/4/8/16s with +/-10% jitter; message moves to DLQ after 5 retries.

    07:34:16 RETRY #1  e2448424 in 0.9s
    07:34:17 RETRY #2  e2448424 in 1.9s
    07:34:19 RETRY #3  e2448424 in 3.8s
    07:34:23 RETRY #4  e2448424 in 7.8s
    07:34:31 RETRY #5  e2448424 in 15.3s
    07:34:47 DLQ       e2448424 after 5 retries

## Token bucket (capacity 2000, refill 1000/s, Redis Lua, atomic)

    burst: 2197/2500 allowed in 372ms (2000 reserve + ~200 refilled during run)
    sec 0: allowed 1500/1500
    sec 1: allowed 1500/1500
    sec 2: allowed 1133/1500
    sec 3: allowed 1001/1500
    sec 4: allowed 996/1500
    sec 5: allowed 1013/1500
    sec 6: allowed 1002/1500
    sec 7: allowed 994/1500
    sec 8: allowed 1041/1500
    sec 9: allowed 1036/1500

Sustained throughput settles at ~1000/s (the refill rate) after the burst reserve drains.

## Idempotency (100 concurrent requests, same Idempotency-Key)
All 100 responses returned one message_id; worker delivered it once.
Same key + different payload -> HTTP 422.

## Crash recovery (kill -9 mid-flight, 30 messages, 4s provider latency)
    sms:processing:<dead-worker> held 30 messages after the crash
    REAPER recovered 30 message(s) from dead workers
    psql: delivered | 30  (0 lost)

## Load test, run 2 (single 12-core box; API cores 0-3, workers 4-6, generator 8-9; Redis/Postgres/docker-proxy unpinned)
Open-loop generator, 20 client IDs, 1,000 req/s for 50 s (50,000 requests), latency from scheduled send time, access logs off.

Full system (3 workers consuming, 15% injected provider failures):
    status codes: {202: 50000}
    client latency ms  p50=10.0  p95=252.4  p99=481.6  max=674.9
    server-side p99 ~370.6 ms (histogram, approximate)
    queue peaked ~2,900, back to 0 by 08:19:21; retry tail cleared 25 s after load ended
    top: 3 workers and 2 API procs at 100% CPU; docker-proxy 70%

API tier only (workers stopped):
    status codes: {202: 50000}
    client latency ms  p50=2.5  p95=47.5  p99=136.4  max=271.9
    server-side p99 ~97.5 ms (histogram, approximate)
    queue length after load: 52000 (50,000 + 2,000 warmup; nothing lost between accept and enqueue)

## Burst (1 client, 2,500 req/s for 2 s; bucket 2,000 capacity, 1,000/s refill)
    status codes: {202: 3800, 429: 1200}

## Delivery latency, run 2 full system (tag 1790583515, 3 workers, 15% injected provider failures)
    rows: 50000   end-to-end p50 = 1.15 s   p99 = 7.26 s (includes retry backoff)

## Load test, run 3 (single 12-core box; API cores 0-3, workers 4-6, generator 8-9, Redis core 10, Postgres/docker-proxy cores 7,11)
Open-loop generator, 20 client IDs, 1,000 req/s for 50 s (50,000 requests), latency from scheduled send time, access logs off, 15% injected provider failures.
    status codes: {202: 50000}
    client latency ms  p50=4.3  p95=34.2  p99=158.3  max=357.5
    server-side p99 ~82.5 ms (histogram, approximate)
    queue peaked at 48; drained 18 s after load ended (retry tail)
    delivered: 50000/50000; end-to-end p50 = 0.06 s, p99 = 3.34 s (includes retry backoff)
API tier only (workers stopped), first repeat: client p99 = 64.1 ms, server-side p99 ~43.9 ms

## Pinned full-system repeats (same config as run 3; worst of 3 reported)
    run 3a: client p99 = 158.3 ms   server-side p99 ~82.5 ms    drain 18 s   delivered 50000/50000   e2e p50 0.063 s, p99 3.34 s
    run 3b: client p99 = 181.7 ms   server-side p99 ~119.9 ms   drain 17 s   delivered 50000/50000   e2e p50 0.068 s, p99 3.37 s
    run 3c: client p99 = 172.5 ms   server-side p99 ~116.5 ms   drain 28 s   delivered 50000/50000   e2e p50 0.070 s, p99 3.40 s
    Client-side P99 with workers running is 158-182 ms (does not meet 150 ms). Server-side values above 100 ms are interpolated inside a 100-150 ms histogram bucket.

## Ceiling probe: 1,500 req/s for 30 s, API tier only (workers stopped, 1 run)
    status codes: {202: 45000}   achieved 1475 accepted/s over 30.5 s
    client latency ms  p50=2.9  p95=88.6  p99=139.3  max=251.7
    server-side p99 ~120.6 ms (coarse)   server-side request count 47000 (45,000 + 2,000 warmup)

## Run 4: full system with probe (same pinning; +50 req/s probe on core 9, main generator on core 8)
    main:  status codes {202: 50000}  client latency ms p50=5.2 p95=74.0 p99=327.3 max=801.6
    probe: status codes {202: 2350}   client latency ms p50=5.1 p95=63.2 p99=324.0 max=768.4
    server-side p99 ~197.6 ms (coarse)   queue peaked at 1,016 (normally <50)   drain 33 s
    redis slowlog: 2 commands >2 ms (EVALSHA 6.1 ms, HSET 2.0 ms), both at the moment of the queue spike
    delivered 50000/50000, e2e p50 0.070 s, p99 3.43 s
    Probe matches main, so the tail is server-side, not generator noise. Suspected ~0.8 s stall; cause under investigation.

## API tier only, 3 repeats (workers stopped; pinned; generator core 8; 1,000 req/s x 50 s; 50,000 requests each)
    run 1: 202 x 50000   client p50/p95/p99/max = 1.9 / 3.6 / 14.8 / 106.4 ms   server-side p99 ~6.6 ms
    run 2: 202 x 50000   client p50/p95/p99/max = 2.2 / 7.8 / 57.3 / 163.8 ms   server-side p99 ~37.1 ms
    run 3: 202 x 50000   client p50/p95/p99/max = 2.4 / 6.2 / 33.2 / 221.2 ms   server-side p99 ~20.6 ms
    Worst client-side P99 of 3: 57.3 ms.

## Host / Redis diagnostics
    redis-cli --intrinsic-latency 30 (idle): worst pause 6.6 ms
    redis: save "3600 1 300 100 60 10000", appendonly no, latest_fork_usec 690

## No-snapshot test (redis save "", 3 full runs with 50 req/s probe)
    run 1: main p99 37.9 ms, probe 41.0, max 191.3, delivered 50000, drain 16 s
    run 2: main p99 86.2 ms, probe 20.7, max 348.2, delivered 49999 + 1 failed after 6 attempts (expected ~0.6 at 15% loss), drain 19 s
    run 3: main p99 177.9 ms, probe 176.7, max 402.4, delivered 50000, drain 31 s
    Redis latency monitor (5 ms threshold): only command-unblocking events, 13/19/24 ms.
    Snapshots off gave no stable improvement: P99 spans 38-178 ms with identical config.

## Environment
    WSL2 (6.18.33.2-microsoft-standard-WSL2), 6 physical cores / 12 threads, shared with the Windows host, 7.8 GB RAM.
    Everything on one machine: API CPUs 0-3, workers 4-6, generator 8, probe 9 (siblings), Redis 10, Postgres/docker-proxy 7 and 11.
    Full-system client P99, 7 pinned runs: 37.9, 86.2, 158.3, 172.5, 177.9, 181.7, 327.3 ms (2 of 7 under 150 ms).

## Latency-based provider failover (500 req/s, 60s, 3 workers, each with an independent circuit breaker)
Injected 400ms latency into provider_a at 10:44:25, cleared at 10:44:45.
    Breaker opened within the same second latency was injected (median of last 10 calls > 200ms).
    Traffic routed to provider_b while open; half-open trial calls correctly stayed open during the outage.
    Breaker closed 1s after the fault cleared (half-open trial succeeded at ~50ms).
    Deliveries: 19,740 via provider_a, 10,260 via provider_b — 30,000/30,000 delivered, 0 lost.

## Kafka event pipeline (Redpanda, single node)
500 req/s for 15s (7,500 requests), worker publishes lifecycle events to topic sms.lifecycle.
    status codes: {202: 7500}
    kafka event counts: delivered=7500, retry=1321, failed=0
    Delivered count matches accepted count exactly (7500/7500); retry count consistent with 15% injected failure rate.

## Kubernetes deployment (kind, local cluster)
Deployment (1-9 replicas via HPA), Service, and HPA applied successfully.
Pod resources: requests/limits cpu=250m, memory=512Mi. Readiness probe on /health.
Pod reaches host Redis/Postgres via the kind node's default gateway IP (172.20.0.1).
NOTE: required disabling Redis protected-mode and binding to 0.0.0.0 for cross-container reachability — local dev only, not a production config.

## HPA autoscaling proof (kind, single node, CPU target 70%)
Load: 300 req/s for 150s against a single pod (250m CPU = ~0.25 core).
    HPA reaction: cpu 1% -> 97% (load ramp) -> HPA scaled 1->2 replicas within ~15-30s -> cpu stabilized at 30-50% across 2 pods.
    NOTE: request-level results during this run are NOT a valid latency benchmark - a single 250m pod is far below the
    provisioned capacity used in the bare-metal tests (4 cores), so the system was intentionally overwhelmed to trigger
    scaling. 40,204/45,000 requests errored, p50=9.07s during the overload window. This demonstrates the HPA mechanism
    correctly detecting and responding to CPU pressure, not a throughput/latency claim.

## Monitoring: Prometheus + Grafana (kind, local cluster)
Prometheus (via Helm, prometheus-community/prometheus) scrapes cluster components plus the sms-gateway pod
(pod annotated prometheus.io/scrape=true, port 8001, path /metrics). Scrape confirmed healthy:
    target: sms-gateway pod, health=up, no scrape errors
    query localhost:9091/api/v1/query?query=sms_accepted_total returns live data
Grafana (standalone deployment) added Prometheus as a data source, confirming the full chain:
    app /metrics -> Prometheus scrape -> Grafana queryable dashboard source.
