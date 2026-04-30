# FastAPI Kubernetes Deployment with Monitoring

This project demonstrates how to deploy a FastAPI application on Kubernetes with integrated monitoring using Prometheus and Grafana. It includes a FastAPI app, Dockerfile for containerization, Kubernetes configuration files, and setup scripts for easy deployment and monitoring.

## Table of Contents

1. [Project Structure](#project-structure)
2. [FastAPI Application](#fastapi-application)
3. [Docker Configuration](#docker-configuration)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Monitoring Setup](#monitoring-setup)
6. [Getting Started](#getting-started)
7. [Manual Setup](#manual-setup)
8. [Dependencies](#dependencies)
9. [Cleanup](#cleanup)

## Project Structure

```
.
├── app/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── setup.sh
│   ├── locustfile.py
│   └── grafana-dashboard.json
├── deployment.yaml
├── service.yaml
├── service-monitor.yaml
└── README.md
```

## FastAPI Application

The FastAPI application provides several endpoints:

1. Root endpoint (`/`): Returns a greeting message
2. Items endpoint (`/items/{item_id}`): Returns item details
3. Generate endpoint (`/generate`): Generates text using a language model
4. Generate Quantized endpoint (`/generate_quantized`): Generates text using a quantized language model
5. Health endpoint (`/health`): Returns the health status of the application
6. Metrics endpoint (`/metrics`): Exposes application metrics for Prometheus

For more details, see `app/main.py`.

## Docker Configuration

The application is containerized using Docker. The Dockerfile specifies:

- Python 3.12 slim image as the base
- Installation of dependencies from `requirements.txt`
- Copying of application files
- Command to run the FastAPI app using Gunicorn and Uvicorn workers

For more details, see `app/Dockerfile`.

## Kubernetes Deployment

The application is deployed on Kubernetes using the following configurations:

### Deployment (`deployment.yaml`)

- Creates replicas of the FastAPI application
- Uses the `fastapi-app:latest` image
- Sets resource requests and limits
- Configures liveness and readiness probes

### Service (`service.yaml`)

- Exposes the application using a NodePort service
- Maps port 8000 of the container to NodePort 30001

### ServiceMonitor (`service-monitor.yaml`)

- Configures Prometheus to scrape metrics from the FastAPI application

## Monitoring Setup

The project uses Prometheus for metrics collection and Grafana for visualization.

- Prometheus: Collects and stores metrics from the application and cluster.
- Grafana: Visualizes the metrics collected by Prometheus.

A custom Grafana dashboard is provided in `app/grafana-dashboard.json`.

## Getting Started

For a quick start, run the following command:

```bash
cd app
./setup.sh
```

This script will:
1. Start or configure Minikube
2. Build the Docker image
3. Deploy the application to Kubernetes
4. Install Prometheus and Grafana using Helm
5. Apply the custom Grafana dashboard

After the setup is complete:
- Access the FastAPI application via Minikube service or NodePort
- Access Grafana at http://localhost:3000 (username: admin, password will be displayed)

To start the FastAPI service:
```bash
minikube service fastapi-service
```

To run load tests with Locust:
```bash
locust -f app/locustfile.py --host=<URL-FROM-MINIKUBE-COMMAND-ABOVE>
```

## Manual Setup

If you prefer to set up the project manually:

1. Install required tools: Docker, Kubernetes (Minikube), Helm

2. Build the Docker image:
   ```bash
   docker build -t fastapi-app:latest ./app
   ```

3. Apply Kubernetes configurations:
   ```bash
   kubectl apply -f deployment.yaml
   kubectl apply -f service.yaml
   kubectl apply -f service-monitor.yaml
   ```

4. Install Prometheus and Grafana:
   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo update
   helm install monitoring prometheus-community/kube-prometheus-stack
   ```

5. Apply the Grafana dashboard:
   ```bash
   kubectl create configmap grafana-dashboard-config --from-file=app/grafana-dashboard.json -n monitoring
   kubectl label configmap grafana-dashboard-config grafana_dashboard=1 -n monitoring
   ```

6. Access the application and monitoring tools as described in the "Getting Started" section.

## Dependencies

- Python 3.12
- FastAPI
- Uvicorn
- Gunicorn
- Prometheus client
- Transformers (for text generation)
- Locust (for load testing)

For a complete list of Python dependencies, see `app/requirements.txt`.

## Cleanup

To remove all resources created by this project:

```bash
# Delete application resources
kubectl delete -f deployment.yaml
kubectl delete -f service.yaml
kubectl delete -f service-monitor.yaml

# Delete Prometheus and Grafana
helm uninstall monitoring

# If using Minikube, stop the cluster
minikube stop
```

This project provides a comprehensive example of deploying a FastAPI application on Kubernetes with integrated monitoring. It's designed to be easily deployable and extensible for your own projects.