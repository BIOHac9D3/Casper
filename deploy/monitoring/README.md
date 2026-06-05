# Casper Monitoring Setup

## Overview

Casper includes comprehensive monitoring with Prometheus, Grafana, and Sentry.

## Quick Start

Start monitoring services:

```bash
docker-compose up -d prometheus grafana
```

Access dashboards:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

## Configuration Files

- Prometheus: deploy/monitoring/prometheus.yml
- Grafana Dashboards: deploy/monitoring/grafana/dashboards/
- Backend Monitoring: backend/configs/monitoring.json
- Sentry: backend/configs/sentry.json

## Health Check

GET /health - Returns service and dependency status
GET /metrics - Prometheus metrics endpoint

## Performance

- Caching: backend/core/performance.py
- Async I/O with retry logic
- Performance monitoring utilities

## References

- [Prometheus Docs](https://prometheus.io/docs/introduction/overview/)
- [Grafana Docs](https://grafana.com/docs/)
- [Sentry Docs](https://docs.sentry.io/)
