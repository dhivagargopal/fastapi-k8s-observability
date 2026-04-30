#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Variables
APP_NAME="fastapi-app"
DOCKER_IMAGE="fastapi-app:latest"
NAMESPACE="default"
PROM_RELEASE_NAME="monitoring"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "Starting setup..."

# Check for required commands
for cmd in docker kubectl helm minikube; do
    if ! command_exists $cmd; then
        echo "Error: $cmd is not installed."
        exit 1
    fi
done

# Start Minikube if not running, with increased resources
if ! minikube status >/dev/null 2>&1; then
    echo "Starting Minikube with increased resources..."
    minikube start --cpus 4 --memory 7680
else
    echo "Minikube is already running. Continuing with setup..."
fi

# Set up Docker environment for Minikube
echo "Setting up Docker environment for Minikube..."
eval $(minikube docker-env)

# Build the Docker image inside Minikube's Docker daemon
echo "Building Docker image..."
docker build -t $DOCKER_IMAGE .

# Install Prometheus and Grafana using Helm
echo "Installing Prometheus and Grafana..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install $PROM_RELEASE_NAME prometheus-community/kube-prometheus-stack

# Wait for Prometheus CRDs to be ready
echo "Waiting for Prometheus CRDs to be ready..."
kubectl wait --for condition=established --timeout=60s crd/servicemonitors.monitoring.coreos.com

# Apply Kubernetes configurations
echo "Applying Kubernetes configurations..."
kubectl apply -f ../deployment.yaml
kubectl apply -f ../service.yaml

# Apply ServiceMonitor configuration
echo "Applying ServiceMonitor configuration..."
kubectl apply -f ../service-monitor.yaml

# Wait for Pods to be ready
echo "Waiting for Pods to be ready..."
kubectl rollout status deployment/fastapi-deployment

# Wait for Prometheus and Grafana Pods to be ready
echo "Waiting for Prometheus and Grafana to be ready..."
kubectl rollout status deployment/$PROM_RELEASE_NAME-grafana
kubectl rollout status deployment/$PROM_RELEASE_NAME-kube-prometheus-operator

# Retrieve Grafana admin password
echo "Retrieving Grafana admin password..."
GRAFANA_PASSWORD=$(kubectl get secret --namespace $NAMESPACE $PROM_RELEASE_NAME-grafana -o jsonpath="{.data.admin-password}" | base64 --decode)

echo "Grafana admin password: $GRAFANA_PASSWORD"

# Create Grafana dashboard
echo "Creating Grafana dashboard..."
kubectl create configmap grafana-dashboard-config --from-file=../app/grafana-dashboard.json -n $NAMESPACE
kubectl label configmap grafana-dashboard-config grafana_dashboard=1 -n $NAMESPACE

# Wait for the dashboard to be created
echo "Waiting for Grafana dashboard to be created..."
kubectl rollout status deployment/$PROM_RELEASE_NAME-grafana

# Port-forward Grafana (in the background)
echo "Port-forwarding Grafana service to localhost:3000..."
kubectl port-forward svc/$PROM_RELEASE_NAME-grafana 3000:80 --namespace $NAMESPACE >/dev/null 2>&1 &
GRAFANA_PID=$!

# Port-forward Prometheus (in the background)
echo "Port-forwarding Prometheus service to localhost:9090..."
kubectl port-forward svc/$PROM_RELEASE_NAME-kube-prometheus-prometheus 9090:9090 --namespace $NAMESPACE >/dev/null 2>&1 &
PROMETHEUS_PID=$!

echo "Setup complete!"
echo "Access the FastAPI application via Minikube service or NodePort."
echo "To access Grafana, navigate to http://localhost:3000 and log in with username 'admin' and the retrieved password."

# Function to clean up resources
cleanup() {
    echo "Cleaning up..."
    kubectl delete -f ../deployment.yaml
    kubectl delete -f ../service.yaml
    kubectl delete -f ../service-monitor.yaml
    kubectl delete configmap grafana-dashboard-config -n $NAMESPACE
    helm uninstall $PROM_RELEASE_NAME
    minikube stop
    echo "Cleanup complete!"
    exit
}

# Wait for user input to terminate the script
echo "Press Ctrl+C to stop port-forwarding and exit."

# Trap Ctrl+C and execute cleanup
trap cleanup INT

# Keep script running
while true; do
    sleep 1
done
