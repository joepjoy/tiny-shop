# Tiny Shop

A small e-commerce app built as microservices and run on Kubernetes, with autoscaling, self-healing, monitoring and a CI/CD pipeline.

**New here? Start with [GUIDE.md](GUIDE.md).** It walks through everything step by step.

## Architecture

```
                 ┌──────────────── Kubernetes cluster (namespace: tiny-shop) ────────────────┐
Browser ──8080──>│ frontend (nginx) x2 ──/api──> api (Flask) x2..6 ──> redis                 │
                 │                                   ▲  │ /metrics                            │
                 │              HPA (CPU 50%) ───────┘  └──> Prometheus ──> Grafana           │
                 └────────────────────────────────────────────────────────────────────────────┘
GitHub push ──> GitHub Actions: unit tests ──> deploy to kind + smoke test ──> push images to GHCR
```

| Service | Tech | Purpose |
|---|---|---|
| `frontend` | nginx | Serves the web page and forwards `/api` to the API |
| `api` | Python, Flask, gunicorn | Products, orders, health check, Prometheus metrics |
| `redis` | Redis 7 | Stores orders |

## Features

- **Containers:** small, non-root Docker images for each service
- **Kubernetes:** Deployments, Services, readiness and liveness probes, resource requests and limits
- **Autoscaling:** a HorizontalPodAutoscaler scales the API from 2 to 6 pods on CPU
- **Self-healing:** crashed pods are replaced automatically
- **Observability:** custom Prometheus metrics (`shop_requests_total`, `shop_request_seconds`, `shop_orders_total`) with Grafana dashboards
- **CI/CD:** GitHub Actions runs tests, deploys to a temporary kind cluster for smoke tests, then publishes images to GitHub Container Registry

## Quick start

```bash
# Docker only
docker compose up --build            # http://localhost:8080

# Kubernetes (kind)
kind create cluster --config kind-config.yaml
docker build -t tiny-shop-api:local ./api
docker build -t tiny-shop-frontend:local ./frontend
kind load docker-image tiny-shop-api:local tiny-shop-frontend:local --name tiny-shop
kubectl apply -f k8s/                # http://localhost:8080
```

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/products` | List products |
| POST | `/api/orders` | Place an order: `{"product_id": 1}` |
| GET | `/api/orders` | 20 most recent orders |
| GET | `/api/health` | Health check (also checks Redis) |
| GET | `/metrics` | Prometheus metrics |

## Running tests

```bash
cd api
pip install -r requirements-dev.txt
pytest
```

## Cost

$0. Everything runs locally on kind, and GitHub Actions and GHCR are free for public repos.

<img width="1917" height="995" alt="image" src="https://github.com/user-attachments/assets/41daf95e-b8af-49b9-a96b-4774ecef1eb6" />

