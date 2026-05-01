# FastAPI Local LLM Demo

This is a simple FastAPI project with Kubernetes monitoring. The `/generate` endpoint uses a small built-in local text generator, so it runs with no API key, no Hugging Face/OpenAI account, and no paid LLM calls.

## Endpoints

- `GET /` - basic app response
- `GET /health` - health check for Kubernetes probes
- `GET /items/{item_id}` - sample item endpoint
- `POST /generate` - free local text generation
- `GET /metrics` - Prometheus metrics

Example:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"text":"Once upon a time"}'
```

## Run With Docker

```bash
docker build -t fastapi-app:latest -f Dockerfile .
docker run --rm -p 8000:8000 fastapi-app:latest
```

Open:

```text
http://localhost:8000
http://localhost:8000/health
http://localhost:8000/metrics
```

## Run On Kubernetes

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f service-monitor.yaml
```

If you are using Minikube:

```bash
minikube service fastapi-service
```

## Monitoring

This project includes:

- `service-monitor.yaml` for Prometheus scraping
- `app/grafana-dashboard.json` for Grafana
- `app/setup.sh` for a Minikube + Prometheus + Grafana setup

Quick setup:

```bash
cd app
./setup.sh
```

## Dependencies

Runtime dependencies are listed in `app/requirements.txt`:

- FastAPI
- Uvicorn
- Gunicorn
- starlette-exporter
- prometheus-client

Development/load-test dependencies are in `app/requirements-dev.txt`.

## Notes

This project intentionally avoids paid LLM APIs. The local generator is lightweight and free, but it is not as powerful as a hosted model like OpenAI or a real local transformer model.

To remove Kubernetes resources:

```bash
kubectl delete -f deployment.yaml
kubectl delete -f service.yaml
kubectl delete -f service-monitor.yaml
```
