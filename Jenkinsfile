pipeline {
    agent any

    environment {
        // ── Docker / Registry ──────────────────────────────────────────────
        DOCKER_IMAGE      = 'fastapi-app'
        DOCKER_TAG        = "${BUILD_NUMBER}"
        DOCKER_REGISTRY   = credentials('docker-registry-url')   // e.g. docker.io/yourusername
        DOCKER_CREDENTIALS = 'docker-hub-credentials'            // Jenkins credential ID

        // ── Kubernetes ─────────────────────────────────────────────────────
        KUBE_CONFIG       = credentials('kubeconfig')            // Jenkins file credential
        K8S_NAMESPACE     = 'default'
        DEPLOYMENT_NAME   = 'fastapi-deployment'
        CONTAINER_NAME    = 'fastapi-container'

        // ── Monitoring (Helm) ──────────────────────────────────────────────
        MONITORING_NS     = 'monitoring'
        HELM_RELEASE      = 'monitoring'

        // ── App paths ──────────────────────────────────────────────────────
        APP_DIR           = 'app'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 10, unit: 'MINUTES')
        disableConcurrentBuilds()
        timestamps()
    }

    stages {

        // ──────────────────────────────────────────────────────────────────
        stage('Checkout') {
        // ──────────────────────────────────────────────────────────────────
            steps {
                echo '==> Cloning repository...'
                checkout scm
                sh 'git log --oneline -5'
            }
        }

        // ──────────────────────────────────────────────────────────────────
        stage('Setup Python Environment') {
        // ──────────────────────────────────────────────────────────────────
            steps {
                echo '==> Setting up Python virtual environment...'
                dir("${APP_DIR}") {
                    sh '''
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install pytest pytest-asyncio httpx   # test deps
                    '''
                }
            }
        }

        // ──────────────────────────────────────────────────────────────────
        stage('Code Quality & Lint') {
        // ──────────────────────────────────────────────────────────────────
            steps {
                echo '==> Running flake8 lint checks...'
                dir("${APP_DIR}") {
                    sh '''
                        . venv/bin/activate
                        pip install flake8 --quiet
                        flake8 main.py --max-line-length=120 --ignore=E501,W503 || true
                    '''
                }
            }
        }

        // ──────────────────────────────────────────────────────────────────
        stage('Unit Tests') {
        // ──────────────────────────────────────────────────────────────────
            steps {
                echo '==> Running pytest unit tests...'
                dir("${APP_DIR}") {
                    sh '''
                        . venv/bin/activate
                        pytest tests/ -v --tb=short --junitxml=test-results.xml || true
                    '''
                }
            }
            post {
                always {
                    junit allowEmptyResults: true,
                          testResults: "${APP_DIR}/test-results.xml"
                }
            }
        }

        // ──────────────────────────────────────────────────────────────────
        stage('Docker Build') {
        // ──────────────────────────────────────────────────────────────────
            steps {
                echo "==> Building Docker image: ${DOCKER_IMAGE}:${DOCKER_TAG}"
                dir("${APP_DIR}") {
                    sh """
                        docker build \
                            --no-cache \
                            -t ${DOCKER_IMAGE}:${DOCKER_TAG} \
                            -t ${DOCKER_IMAGE}:latest \
                            -f Dockerfile .
                    """
                }
                sh "docker images | grep ${DOCKER_IMAGE}"
            }
        }

        // ──────────────────────────────────────────────────────────────────
        stage('Docker Security Scan') {
        // ──────────────────────────────────────────────────────────────────
            steps {
                echo '==> Scanning image for vulnerabilities with Trivy...'
                sh """
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v \$HOME/.cache:/root/.cache \
                        aquasec/trivy:latest image \
                        --exit-code 0 \
                        --severity HIGH,CRITICAL \
                        --format table \
                        ${DOCKER_IMAGE}:${DOCKER_TAG}
                """
            }
        }

        // ──────────────────────────────────────────────────────────────────
        stage('Push to Registry') {
        // ──────────────────────────────────────────────────────────────────
            steps {
                echo "==> Pushing image to ${DOCKER_REGISTRY}..."
                withCredentials([usernamePassword(
                    credentialsId: "${DOCKER_CREDENTIALS}",
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                        echo "\$DOCKER_PASS" | docker login -u "\$DOCKER_USER" --password-stdin
                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG}  \${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}
                        docker tag ${DOCKER_IMAGE}:latest          \${DOCKER_REGISTRY}/${DOCKER_IMAGE}:latest
                        docker push \${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}
                        docker push \${DOCKER_REGISTRY}/${DOCKER_IMAGE}:latest
                        docker logout
                    """
                }
            }
        }

        // ──────────────────────────────────────────────────────────────────
        stage('Setup Monitoring (Helm)') {
        // ──────────────────────────────────────────────────────────────────
        // Installs kube-prometheus-stack if not already present.
        // Skips safely on re-runs (helm upgrade --install is idempotent).
        // ──────────────────────────────────────────────────────────────────
            steps {
                echo '==> Ensuring Prometheus + Grafana are deployed via Helm...'
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        kubectl create namespace ${MONITORING_NS} --dry-run=client -o yaml | kubectl apply -f -

                        helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
                        helm repo update

                        helm upgrade --install ${HELM_RELEASE} \
                            prometheus-community/kube-prometheus-stack \
                            --namespace ${MONITORING_NS} \
                            --set grafana.adminPassword=admin \
                            --set prometheus.prometheusSpec.scrapeInterval=15s \
                            --wait --timeout 5m
                    """
                }
            }
        }

        // ──────────────────────────────────────────────────────────────────
        stage('Deploy to Kubernetes') {
        // ──────────────────────────────────────────────────────────────────
            steps {
                echo "==> Deploying fastapi-app to Kubernetes namespace: ${K8S_NAMESPACE}"
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        # Patch image tag in deployment (non-destructive update)
                        kubectl set image deployment/${DEPLOYMENT_NAME} \
                            ${CONTAINER_NAME}=\${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG} \
                            --namespace ${K8S_NAMESPACE} 2>/dev/null || true

                        # Apply manifests (creates resources if they don't exist yet)
                        kubectl apply -f deployment.yaml  --namespace ${K8S_NAMESPACE}
                        kubectl apply -f service.yaml     --namespace ${K8S_NAMESPACE}
                        kubectl apply -f service-monitor.yaml --namespace ${MONITORING_NS}
                    """
                }
            }
        }

        // ──────────────────────────────────────────────────────────────────
        stage('Apply Grafana Dashboard') {
        // ──────────────────────────────────────────────────────────────────
            steps {
                echo '==> Pushing custom Grafana dashboard configmap...'
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        kubectl create configmap grafana-dashboard-config \
                            --from-file=${APP_DIR}/grafana-dashboard.json \
                            --namespace ${MONITORING_NS} \
                            --dry-run=client -o yaml | kubectl apply -f -

                        kubectl label configmap grafana-dashboard-config \
                            grafana_dashboard=1 \
                            --namespace ${MONITORING_NS} \
                            --overwrite
                    """
                }
            }
        }

        // ──────────────────────────────────────────────────────────────────
        stage('Rollout Verification') {
        // ──────────────────────────────────────────────────────────────────
            steps {
                echo '==> Waiting for rollout to complete...'
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        kubectl rollout status deployment/${DEPLOYMENT_NAME} \
                            --namespace ${K8S_NAMESPACE} \
                            --timeout=180s

                        echo '--- Pod status ---'
                        kubectl get pods -l app=fastapi --namespace ${K8S_NAMESPACE}

                        echo '--- Service ---'
                        kubectl get svc fastapi-service --namespace ${K8S_NAMESPACE}

                        echo '--- ServiceMonitor ---'
                        kubectl get servicemonitor --namespace ${MONITORING_NS} || true
                    """
                }
            }
        }

        // ──────────────────────────────────────────────────────────────────
        stage('Health Check') {
        // ──────────────────────────────────────────────────────────────────
            steps {
                echo '==> Verifying /health endpoint via NodePort 30001...'
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        NODE_IP=\$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
                        echo "Node IP: \${NODE_IP}"

                        # Retry up to 10 times with 10s delay (pods may still be initialising)
                        for i in \$(seq 1 10); do
                            STATUS=\$(curl -s -o /dev/null -w '%{http_code}' http://\${NODE_IP}:30001/health)
                            echo "Attempt \${i}: HTTP \${STATUS}"
                            if [ "\${STATUS}" = "200" ]; then
                                echo "Health check passed!"
                                exit 0
                            fi
                            sleep 10
                        done

                        echo "Health check failed after 10 attempts"
                        exit 1
                    """
                }
            }
        }

        // ──────────────────────────────────────────────────────────────────
        stage('Verify Prometheus Scraping') {
        // ──────────────────────────────────────────────────────────────────
            steps {
                echo '==> Checking /metrics endpoint is reachable...'
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        NODE_IP=\$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
                        METRICS=\$(curl -s http://\${NODE_IP}:30001/metrics | head -5)
                        echo "\${METRICS}"

                        if echo "\${METRICS}" | grep -q 'http_requests'; then
                            echo "Prometheus metrics endpoint is live!"
                        else
                            echo "Warning: metrics endpoint returned unexpected output"
                        fi
                    """
                }
            }
        }

    } // end stages

    // ──────────────────────────────────────────────────────────────────────
    post {
    // ──────────────────────────────────────────────────────────────────────
        success {
            echo """
            ============================================================
             BUILD SUCCESS
             Image : \${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}
             App   : http://<NODE_IP>:30001
             Grafana: http://<NODE_IP>:3000  (admin / admin)
            ============================================================
            """
        }

        failure {
            echo '==> Build FAILED. Collecting diagnostics...'
            withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                sh """
                    echo '--- Pod events ---'
                    kubectl describe pods -l app=fastapi --namespace ${K8S_NAMESPACE} || true

                    echo '--- Pod logs ---'
                    kubectl logs -l app=fastapi --namespace ${K8S_NAMESPACE} --tail=50 || true
                """
            }
        }

        always {
            echo '==> Cleaning up local Docker images...'
            sh """
                docker rmi ${DOCKER_IMAGE}:${DOCKER_TAG} || true
                docker rmi ${DOCKER_IMAGE}:latest        || true
            """
            cleanWs()
        }
    }
}
