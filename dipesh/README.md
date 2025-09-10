# CI/CD Pipeline Health Dashboard

A production-ready dashboard for monitoring CI/CD pipelines from multiple providers (GitHub Actions, Jenkins) with real-time metrics, alerting, and containerized deployment.

## Setup & Run Instructions

### Prerequisites
- Docker and Docker Compose installed
- Git installed
- Ports 8001 (backend) and 5173 (frontend) available

### Quick Setup (2 minutes)

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd dipesh
```

2. **Set up environment variables**
```bash
cp env.example .env
# Edit .env file with your configuration (optional for basic setup)
```

**Note**: The project uses `npm install` instead of `npm ci` in the Docker build to avoid package-lock.json sync issues.

3. **Start the application stack**
```bash
docker-compose up -d
```

4. **Verify deployment**
```bash
# Check container health
docker-compose ps

# Verify services are running
curl http://localhost:8001/health
curl http://localhost:5173
```

5. **Access the application**
- **Dashboard**: http://localhost:5173
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

6. **Test with sample data**
```bash
# Inject sample GitHub Actions build data
curl -X POST http://localhost:8001/ingest/github \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline": "demo-pipeline",
    "repo": "my-org/my-repo",
    "branch": "main",
    "status": "success",
    "started_at": "2025-01-25T10:00:00Z",
    "completed_at": "2025-01-25T10:02:00Z",
    "duration_seconds": 120,
    "url": "https://github.com/my-org/my-repo/actions/runs/123"
  }'

# Inject sample Jenkins build data
curl -X POST http://localhost:8001/ingest/jenkins \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline": "jenkins-pipeline",
    "repo": "test/repo",
    "branch": "main",
    "status": "failure",
    "started_at": "2025-01-25T10:05:00Z",
    "completed_at": "2025-01-25T10:08:00Z",
    "duration_seconds": 180
  }'
```

The dashboard will update in real-time showing the new build data, metrics, and charts.

### Features Verification
- ✅ Real-time data collection from GitHub Actions and Jenkins
- ✅ Live dashboard updates via WebSocket
- ✅ Success/failure rate calculations
- ✅ Build duration metrics and visualization
- ✅ Alerting system (Slack and email notifications)
- ✅ Containerized deployment with health checks

## Architecture Summary

### System Overview
The CI/CD Pipeline Health Dashboard follows a microservices architecture with containerized deployment:

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

### Component Architecture

#### Backend (FastAPI)
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

#### Frontend (React)
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

#### Database Design
**Builds Table Schema**:
- `id` (Primary Key)
- `provider` (github|jenkins)
- `pipeline`, `repo`, `branch` (string identifiers)
- `status` (success|failure|cancelled|in_progress)
- `started_at`, `completed_at` (timestamps)
- `duration_seconds` (calculated build time)
- `url`, `logs` (optional reference links)

#### Containerization
- **Multi-stage Docker builds** for optimized production images
- **Health checks** for container orchestration
- **Volume persistence** for SQLite database
- **Docker Compose** orchestration with service dependencies

## 🚀 Features

- ✅ **Real-time data collection** from multiple CI/CD providers (GitHub Actions, Jenkins)
- ✅ **Live metrics dashboard** with success/failure rates and build times
- ✅ **WebSocket-powered updates** for instant dashboard refreshes
- ✅ **Alerting system** with Slack and email notifications on failures
- ✅ **Modern React UI** with interactive charts and responsive design
- ✅ **Fully containerized** with Docker for consistent deployment
- ✅ **Production-ready** with health checks, security hardening, and proper documentation

## 🧱 Tech Stack

- **Backend**: FastAPI (Python), SQLAlchemy ORM, SQLite database, WebSocket broadcasting
- **Frontend**: React 18 + Vite, Recharts for visualization, Tailwind CSS
- **Containerization**: Docker multi-stage builds, Docker Compose orchestration
- **Collectors**: Webhook endpoints + optional polling scripts
- **Alerts**: Slack webhooks and SMTP email notifications
- **Infrastructure**: Health checks, volume persistence, security hardening

## API Endpoints

### Data Ingestion
- `POST /ingest/github` - Ingest GitHub Actions build data
- `POST /ingest/jenkins` - Ingest Jenkins build data
- `POST /webhook/github` - GitHub webhook handler
- `POST /webhook/jenkins` - Jenkins webhook handler

### Data Retrieval
- `GET /builds` - Get recent builds (with pagination)
- `GET /builds/latest` - Get latest build for a pipeline
- `GET /metrics/summary` - Get aggregated metrics

### System
- `GET /health` - Health check endpoint
- `WebSocket /ws` - Real-time updates

## Configuration

### Environment Variables

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

### Webhook Configuration

#### GitHub Actions
1. Go to your repository settings
2. Navigate to "Webhooks"
3. Add webhook URL: `http://your-domain:8001/webhook/github`
4. Select "Workflow runs" events

#### Jenkins
1. Install the "Generic Webhook Trigger" plugin
2. Configure your job with webhook URL: `http://your-domain:8001/webhook/jenkins`
3. Set up post-build actions to trigger the webhook

## Development

### Local Development Setup

1. **Backend Development**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

2. **Frontend Development**
```bash
cd frontend
npm install
npm run dev
```

### Building for Production

```bash
# Build backend
cd backend
docker build -t ci-dashboard-backend .

# Build frontend
cd frontend
docker build -t ci-dashboard-frontend .

# Or build everything with docker-compose
docker-compose build
```

## Monitoring and Maintenance

### Health Checks
- Backend: `curl http://localhost:8001/health`
- Frontend: `curl http://localhost:5173/`

### Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f
```

### Database Backup
```bash
# Backup SQLite database
docker-compose exec backend cp /app/data/dashboard.db /app/data/dashboard.db.backup

# Copy backup to host
docker cp ci-dashboard-backend:/app/data/dashboard.db.backup ./backup.db
```

## Troubleshooting

### Common Issues

1. **Docker build failures**
   - **npm ci errors**: The project uses `npm install` instead of `npm ci` to avoid package-lock.json sync issues
   - **Permission errors**: Make sure Docker has proper permissions
   - **Network issues**: Check if Docker can access external registries

2. **Port conflicts**
   - Change ports in `.env` file
   - Update `BACKEND_PORT` and `FRONTEND_PORT`

3. **Database issues**
   - Check volume permissions
   - Restart backend container

4. **WebSocket connection issues**
   - Verify CORS settings
   - Check firewall rules

5. **Alerting not working**
   - Verify environment variables
   - Check webhook URLs and SMTP settings

### Debug Mode

Enable debug logging by setting environment variables:
```bash
# In .env file
PYTHONUNBUFFERED=1
LOG_LEVEL=DEBUG
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**The CI/CD Pipeline Health Dashboard is ready for production deployment!**

This containerized solution provides comprehensive monitoring for a CI/CD pipelines with real-time updates, alerting, and a modern user interface.
