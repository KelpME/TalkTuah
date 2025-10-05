# Metrics & Monitoring

This directory contains configuration for monitoring vLLM with Prometheus.

## Quick Start

### Option 1: Direct Scraping (Recommended)

Scrape vLLM metrics directly from the vLLM container:

```bash
# vLLM metrics endpoint
curl http://localhost:8000/metrics
```

Configure your Prometheus to scrape `http://vllm:8000/metrics` (or `http://localhost:8000/metrics` from host).

### Option 2: Via Proxy

The proxy API also exposes vLLM metrics at `/metrics`:

```bash
# Proxied metrics endpoint
curl http://localhost:8787/metrics
```

### Option 3: Run Prometheus with Docker

```bash
# From project root
docker run -d \
  --name prometheus \
  --network vllm-demo_default \
  -p 9090:9090 \
  -v $(pwd)/deploy/metrics/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Access Prometheus UI
open http://localhost:9090
```

## Key Metrics

### Request Metrics

- `vllm:num_requests_running` - Currently executing requests
- `vllm:num_requests_waiting` - Requests queued
- `vllm:num_requests_swapped` - Requests swapped to CPU

### Latency Metrics

- `vllm:time_to_first_token_seconds` - Time to first token (TTFB)
  - Histogram with buckets
  - Use `histogram_quantile(0.95, ...)` for P95
- `vllm:time_per_output_token_seconds` - Per-token generation time
- `vllm:e2e_request_latency_seconds` - End-to-end request latency

### Resource Metrics

- `vllm:gpu_cache_usage_perc` - GPU KV cache utilization (%)
- `vllm:cpu_cache_usage_perc` - CPU cache utilization (%)
- `vllm:num_preemptions_total` - Total preemptions (counter)

### Model Metrics

- `vllm:prompt_tokens_total` - Total prompt tokens processed
- `vllm:generation_tokens_total` - Total tokens generated
- `vllm:request_success_total` - Successful requests
- `vllm:request_failure_total` - Failed requests

## Example Queries

### P95 Time to First Byte

```promql
histogram_quantile(0.95, 
  rate(vllm:time_to_first_token_seconds_bucket[5m])
)
```

### Requests Per Second

```promql
rate(vllm:request_success_total[1m])
```

### GPU Cache Utilization

```promql
vllm:gpu_cache_usage_perc
```

### Average Tokens Per Second

```promql
rate(vllm:generation_tokens_total[1m])
```

### Queue Depth

```promql
vllm:num_requests_waiting
```

## Grafana Dashboard

For visualization, import a Grafana dashboard:

1. Install Grafana: `docker run -d -p 3000:3000 grafana/grafana`
2. Add Prometheus datasource: `http://prometheus:9090`
3. Create dashboard with above queries

## Alerting

Example alert rules for `prometheus.yml`:

```yaml
rule_files:
  - 'alerts.yml'
```

**alerts.yml:**

```yaml
groups:
  - name: vllm_alerts
    interval: 30s
    rules:
      - alert: HighQueueDepth
        expr: vllm:num_requests_waiting > 10
        for: 2m
        annotations:
          summary: "vLLM queue depth is high"
          
      - alert: HighGPUCacheUsage
        expr: vllm:gpu_cache_usage_perc > 90
        for: 5m
        annotations:
          summary: "GPU cache usage above 90%"
          
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(vllm:time_to_first_token_seconds_bucket[5m])) > 2
        for: 5m
        annotations:
          summary: "P95 TTFB above 2 seconds"
```

## Documentation

- [vLLM Metrics Documentation](https://docs.vllm.ai/en/latest/serving/metrics.html)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
