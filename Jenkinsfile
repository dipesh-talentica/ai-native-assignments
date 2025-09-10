pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'your-registry.com'
        IMAGE_NAME = 'ci-cd-dashboard'
        BACKEND_IMAGE = "${DOCKER_REGISTRY}/${IMAGE_NAME}-backend"
        FRONTEND_IMAGE = "${DOCKER_REGISTRY}/${IMAGE_NAME}-frontend"
        VERSION = "${BUILD_NUMBER}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                }
            }
        }
        
        stage('Build Backend') {
            steps {
                script {
                    echo "Building backend Docker image..."
                    sh """
                        docker build -t ${BACKEND_IMAGE}:${VERSION} \
                            -t ${BACKEND_IMAGE}:latest \
                            -f backend/Dockerfile backend/
                    """
                }
            }
        }
        
        stage('Build Frontend') {
            steps {
                script {
                    echo "Building frontend Docker image..."
                    sh """
                        docker build -t ${FRONTEND_IMAGE}:${VERSION} \
                            -t ${FRONTEND_IMAGE}:latest \
                            -f frontend/Dockerfile frontend/
                    """
                }
            }
        }
        
        stage('Test Backend') {
            steps {
                script {
                    echo "Running backend tests..."
                    sh """
                        docker run --rm \
                            -v $(pwd)/backend:/app \
                            -w /app \
                            python:3.11-slim \
                            bash -c "pip install -r requirements.txt && python -m pytest test_backend.py -v"
                    """
                }
            }
        }
        
        stage('Test Frontend') {
            steps {
                script {
                    echo "Running frontend tests..."
                    sh """
                        docker run --rm \
                            -v $(pwd)/frontend:/app \
                            -w /app \
                            node:20-alpine \
                            sh -c "npm install && npm test"
                    """
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                script {
                    echo "Running security scans..."
                    sh """
                        # Scan backend image
                        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                            aquasec/trivy image ${BACKEND_IMAGE}:${VERSION}
                        
                        # Scan frontend image
                        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                            aquasec/trivy image ${FRONTEND_IMAGE}:${VERSION}
                    """
                }
            }
        }
        
        stage('Push Images') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "Pushing Docker images to registry..."
                    sh """
                        docker push ${BACKEND_IMAGE}:${VERSION}
                        docker push ${BACKEND_IMAGE}:latest
                        docker push ${FRONTEND_IMAGE}:${VERSION}
                        docker push ${FRONTEND_IMAGE}:latest
                    """
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "Deploying to staging environment..."
                    sh """
                        # Update docker-compose with new image tags
                        sed -i "s|image: ${BACKEND_IMAGE}:latest|image: ${BACKEND_IMAGE}:${VERSION}|g" docker-compose.staging.yml
                        sed -i "s|image: ${FRONTEND_IMAGE}:latest|image: ${FRONTEND_IMAGE}:${VERSION}|g" docker-compose.staging.yml
                        
                        # Deploy to staging
                        docker-compose -f docker-compose.staging.yml up -d
                    """
                }
            }
        }
        
        stage('Integration Tests') {
            when {
                branch 'main'
            }
            steps {
                script {
                    echo "Running integration tests..."
                    sh """
                        # Wait for services to be ready
                        sleep 30
                        
                        # Test health endpoints
                        curl -f http://staging-backend:8001/health
                        curl -f http://staging-frontend:5173/
                        
                        # Run integration tests
                        python test_setup.py --backend http://staging-backend:8001
                    """
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                branch 'main'
                not { changeRequest() }
            }
            steps {
                script {
                    echo "Deploying to production environment..."
                    sh """
                        # Update production docker-compose
                        sed -i "s|image: ${BACKEND_IMAGE}:latest|image: ${BACKEND_IMAGE}:${VERSION}|g" docker-compose.prod.yml
                        sed -i "s|image: ${FRONTEND_IMAGE}:latest|image: ${FRONTEND_IMAGE}:${VERSION}|g" docker-compose.prod.yml
                        
                        # Deploy to production
                        docker-compose -f docker-compose.prod.yml up -d
                        
                        # Verify deployment
                        sleep 30
                        curl -f http://production-backend:8001/health
                        curl -f http://production-frontend:5173/
                    """
                }
            }
        }
    }
    
    post {
        always {
            script {
                echo "Cleaning up workspace..."
                sh """
                    # Remove local images to save space
                    docker rmi ${BACKEND_IMAGE}:${VERSION} || true
                    docker rmi ${FRONTEND_IMAGE}:${VERSION} || true
                """
            }
        }
        
        success {
            script {
                echo "Pipeline completed successfully!"
                // Send success notification
                sh """
                    curl -X POST -H 'Content-type: application/json' \
                        --data '{"text":"✅ CI/CD Dashboard Pipeline #${BUILD_NUMBER} completed successfully!"}' \
                        ${SLACK_WEBHOOK_URL}
                """
            }
        }
        
        failure {
            script {
                echo "Pipeline failed!"
                // Send failure notification
                sh """
                    curl -X POST -H 'Content-type: application/json' \
                        --data '{"text":"❌ CI/CD Dashboard Pipeline #${BUILD_NUMBER} failed! Check Jenkins for details."}' \
                        ${SLACK_WEBHOOK_URL}
                """
            }
        }
        
        unstable {
            script {
                echo "Pipeline completed with warnings!"
                // Send warning notification
                sh """
                    curl -X POST -H 'Content-type: application/json' \
                        --data '{"text":"⚠️ CI/CD Dashboard Pipeline #${BUILD_NUMBER} completed with warnings!"}' \
                        ${SLACK_WEBHOOK_URL}
                """
            }
        }
    }
}
