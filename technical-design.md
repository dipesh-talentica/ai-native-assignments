# Technical Design: CI/CD Pipeline Health Dashboard

## Overview

The CI/CD Pipeline Health Dashboard is a production-ready, containerized solution for monitoring CI/CD pipelines (GitHub Actions, Jenkins) with real-time metrics, alerting, and interactive visualization. It is designed for cloud deployment and extensibility.

---

## Architecture

### System Overview

```
┌─────────────────┐    webhook/poll    ┌─────────────────┐
│ GitHub Actions  │ ────────────────▶  │   FastAPI       │
│     Jenkins     │                    │   Backend       │
└─────────────────┘                    │   (Port 8001)   │
                                       └─────────┬───────┘
                                                 │
                ┌─────────────────┐             │ REST API
                │   SQLite DB     │ ◀───────────┤
                │  (Persistent)   │             │
                └─────────────────┘             │
                                                │
┌─────────────────┐    WebSocket           ┌────▼────────────┐
│ React Frontend  │ ◀──────────────────────│  WebSocket      │
│  (Port 5173)    │                        │  Broadcasting   │
└─────────────────┘                        └─────────────────┘
                                                │
                                           ┌────▼────────────┐
                                           │    Alerting     │
                                           │ (Slack/Email)   │
                                           └─────────────────┘
```

- **Backend**: FastAPI, SQLAlchemy, SQLite, REST API, WebSocket, Slack/Email alerting
- **Frontend**: React 18, Vite, Recharts, WebSocket client
- **Infrastructure**: Docker Compose (local), Terraform (AWS EC2, EBS, ECR, CloudWatch, Secrets Manager)

---

## Key Features

- Real-time data collection from GitHub Actions and Jenkins
- Live dashboard updates via WebSocket
- Success/failure rate calculations
- Build duration metrics and visualization
- Alerting system (Slack and email notifications)
- Containerized deployment with health checks
- Volume persistence for database
- Security hardening and environment configuration

---

## Data Flow

1. **Data Ingestion**
    - Collectors ([`backend/collectors/github_collector.py`](backend/collectors/github_collector.py), [`backend/collectors/jenkins_collector.py`](backend/collectors/jenkins_collector.py)) fetch build data via API/webhook.
    - Data is POSTed to backend endpoints (`/ingest/github`, `/ingest/jenkins`).

2. **Persistence**
    - Backend parses and validates data ([`backend/schemas.py`](backend/schemas.py)), stores in SQLite ([`backend/database.py`](backend/database.py), [`backend/models.py`](backend/models.py)).

3. **Metrics Calculation**
    - Aggregated metrics (success/failure rates, average build time, last status by pipeline) are computed in [`backend/main.py`](backend/main.py) (`/metrics/summary` endpoint).

4. **Real-Time Updates**
    - Backend broadcasts build events via WebSocket ([`backend/ws.py`](backend/ws.py)).
    - Frontend subscribes for live updates.

5. **Alerting**
    - On build failure, alerts are sent via Slack/email ([`backend/alerting.py`](backend/alerting.py)), using environment variables or AWS Secrets Manager.

6. **Visualization**
    - Frontend ([`frontend/src/App.jsx`](frontend/src/App.jsx)) displays metrics, charts, and build logs.
    - Data is fetched via REST API and updated via WebSocket.

---

## Component Architecture

### Backend (FastAPI)

- **Technology**: Python, FastAPI, SQLAlchemy, SQLite
- **Responsibilities**:
  - Webhook ingestion from CI/CD providers
  - Metrics calculation (success rates, build times)
  - Real-time WebSocket broadcasting
  - Alerting system (Slack/email notifications)
- **Key Endpoints**:
  - `POST /ingest/github` - GitHub Actions webhook handler
  - `POST /ingest/jenkins` - Jenkins webhook handler
  - `GET /metrics/summary` - Aggregated metrics
  - `GET /builds` - Recent builds data
  - `WebSocket /ws` - Real-time updates
  - `GET /health` - Health check endpoint

### Frontend (React)

- **Technology**: React 18, Vite, Recharts, Tailwind CSS
- **Responsibilities**:
  - Real-time dashboard visualization
  - Metrics display and charts
  - WebSocket connection management
  - Responsive user interface
- **Key Features**:
  - Live metrics cards (success rate, avg build time)
  - Interactive charts for build trends
  - Recent builds table with provider labels
  - Real-time updates without page refresh
  - Modal for build logs

### Database Design

**Builds Table Schema** ([`backend/models.py`](backend/models.py)):
- `id` (Primary Key)
- `provider` (github|jenkins)
- `pipeline`, `repo`, `branch` (string identifiers)
- `status` (success|failure|cancelled|in_progress)
- `started_at`, `completed_at` (timestamps)
- `duration_seconds` (calculated build time)
- `url`, `logs` (optional reference links)
- `created_at` (record timestamp)

### Containerization

- **Multi-stage Docker builds** for optimized production images ([`backend/Dockerfile`](backend/Dockerfile), [`frontend/Dockerfile`](frontend/Dockerfile))
- **Health checks** for container orchestration
- **Volume persistence** for SQLite database
- **Docker Compose** orchestration with service dependencies ([docker-compose.yml](docker-compose.yml))

### Infrastructure (Cloud)

- **Terraform** ([assignment-3/terraform/](assignment-3/terraform/)):
  - EC2 instance (Amazon Linux 2023)
  - ECR repository for Docker images
  - EBS volume for SQLite DB
  - CloudWatch log group
  - Secrets Manager for SMTP/email credentials
  - Security group for HTTP/SSH
  - IAM roles for resource access

---

## API Endpoints

See [`README.md`](README.md):

- `POST /ingest/github`, `POST /ingest/jenkins`: Data ingestion
- `GET /metrics/summary`: Aggregated metrics
- `GET /builds`: Recent builds
- `GET /health`: Health check
- `WebSocket /ws`: Real-time updates

---

## Configuration

### Environment Variables ([README.md](README.md#configuration))

Create a `.env` file based on `env.example`:

```bash
# Backend Configuration
BACKEND_PORT=8001
FRONTEND_PORT=5173

# Database Configuration
SQLALCHEMY_DATABASE_URL=sqlite:///./data/dashboard.db

# CORS Configuration
ALLOW_ORIGINS=http://localhost:5173

# Alerting Configuration (Optional)
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
ALERT_EMAIL_FROM=your-email@gmail.com
ALERT_EMAIL_TO=alerts@yourcompany.com
```

---

## Security & Reliability

- **Health checks**: Dockerfile, Compose, Terraform EC2 user-data
- **Volume persistence**: SQLite DB on EBS (cloud), Docker volume (local)
- **Secrets management**: `.env` (local), AWS Secrets Manager (cloud)
- **IAM roles**: EC2 instance profile for AWS resource access
- **CORS**: Configurable origins for frontend-backend communication

---

## Testing

- **Backend**: [`backend/test_backend.py`](backend/test_backend.py) – API endpoints, models, metrics
- **Frontend**: [`frontend/test_frontend.mjs`](frontend/test_frontend.mjs) – utility functions, props validation, API integration
- **Setup verification**: [`test_setup.py`](test_setup.py) – end-to-end checks

---

## Monitoring and Maintenance

- **Health Checks**: Backend (`/health`), Frontend (`/`)
- **Logs**: Docker Compose logs, CloudWatch logs (cloud)
- **Database Backup**: SQLite file backup via Docker commands
- **Troubleshooting**: See [README.md](README.md#troubleshooting) for common issues and debug mode

---

## Extensibility

- Add more CI/CD providers by extending collectors
- Support additional metrics or alerting channels
- Scale out with managed DB (RDS) or container orchestration (ECS/EKS)
- Enhance frontend with more charts or filtering options

---

## References

- [README.md](README.md)
- [assignment-3/terraform/README.md](assignment-3/terraform/README.md)
- [assignment.md](assignment.md)
