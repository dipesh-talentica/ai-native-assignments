import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from pydantic_settings import BaseSettings
from database import SessionLocal, engine, Base
from models import Build
from schemas import IngestRequest, BuildOut, SummaryOut
from alerting import alert_failure
from ws import manager

class Settings(BaseSettings):
    BACKEND_PORT: int = 8001
    ALLOW_ORIGINS: str = "http://localhost:5173"

settings = Settings()

app = FastAPI(title="CI/CD Pipeline Health Dashboard API")

origins = [o.strip() for o in settings.ALLOW_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB init
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _persist(db: Session, provider: str, data: IngestRequest) -> Build:
    dur = data.duration_seconds
    if dur is None and data.completed_at:
        dur = (data.completed_at - data.started_at).total_seconds()
    b = Build(
        provider=provider,
        pipeline=data.pipeline,
        repo=data.repo,
        branch=data.branch,
        status=data.status,
        started_at=data.started_at,
        completed_at=data.completed_at,
        duration_seconds=dur,
        url=data.url,
        logs=data.logs,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b

@app.post("/ingest/github", response_model=BuildOut)
async def ingest_github(payload: IngestRequest, db: Session = Depends(get_db)):
    b = _persist(db, "github", payload)
    if b.status == "failure":
        alert_failure(b.pipeline, b.repo, b.url or "", b.logs or "")
    
    # Broadcast real-time update to connected clients
    await manager.broadcast({
        "event": "build_ingested",
        "data": {
            "pipeline": b.pipeline,
            "repo": b.repo,
            "status": b.status,
            "provider": b.provider
        }
    })
    return b

@app.post("/ingest/jenkins", response_model=BuildOut)
async def ingest_jenkins(payload: IngestRequest, db: Session = Depends(get_db)):
    b = _persist(db, "jenkins", payload)
    if b.status == "failure":
        alert_failure(b.pipeline, b.repo, b.url or "", b.logs or "")
    
    # Broadcast real-time update to connected clients
    await manager.broadcast({
        "event": "build_ingested",
        "data": {
            "pipeline": b.pipeline,
            "repo": b.repo,
            "status": b.status,
            "provider": b.provider
        }
    })
    return b

@app.get("/builds", response_model=List[BuildOut])
def list_builds(limit: int = 50, db: Session = Depends(get_db)):
    q = select(Build).order_by(desc(Build.started_at)).limit(limit)
    rows = db.execute(q).scalars().all()
    return rows

@app.get("/builds/latest", response_model=Optional[BuildOut])
def latest_build(pipeline: Optional[str] = None, db: Session = Depends(get_db)):
    q = select(Build)
    if pipeline:
        q = q.where(Build.pipeline == pipeline)
    q = q.order_by(desc(Build.started_at)).limit(1)
    row = db.execute(q).scalars().first()
    return row

@app.get("/metrics/summary", response_model=SummaryOut)
def metrics_summary(window: str = "7d", db: Session = Depends(get_db)):
    # parse window
    now = datetime.now(timezone.utc)
    delta = timedelta(days=7)
    if window.endswith("h"):
        delta = timedelta(hours=int(window[:-1]))
    elif window.endswith("d"):
        delta = timedelta(days=int(window[:-1]))
    since = now - delta

    q = select(Build).where(Build.started_at >= since)
    rows = db.execute(q).scalars().all()

    total = len(rows)
    succ = sum(1 for r in rows if r.status == "success")
    fail = sum(1 for r in rows if r.status == "failure")
    durations = [r.duration_seconds for r in rows if r.duration_seconds is not None]
    avg = sum(durations) / len(durations) if durations else None

    last_by_pipeline: Dict[str, Build] = {}
    for r in rows:
        key = r.pipeline
        if key not in last_by_pipeline or r.started_at > last_by_pipeline[key].started_at:
            last_by_pipeline[key] = r

    out = SummaryOut(
        window=window,
        success_rate=(succ / total * 100.0) if total else 0.0,
        failure_rate=(fail / total * 100.0) if total else 0.0,
        avg_build_time=avg,
        last_status_by_pipeline={k: v.status for k, v in last_by_pipeline.items()},
    )
    return out

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive or ignore client msgs
    except Exception:
        pass
    finally:
        manager.disconnect(ws)

@app.post("/webhook/jenkins")
async def webhook_jenkins(payload: dict, db: Session = Depends(get_db)):
    """Handle Jenkins webhook payloads"""
    try:
        # Extract data from Jenkins webhook format
        workflow_run = payload.get("workflow_run", {})
        repo_info = payload.get("repository", {})
        
        # Map Jenkins data to our internal format
        ingest_data = IngestRequest(
            pipeline=workflow_run.get("name", "unknown"),
            repo=repo_info.get("full_name", "unknown"),
            branch="main",  # Jenkins webhooks might not have branch info
            status="success" if workflow_run.get("conclusion") == "success" else "failure",
            started_at=datetime.fromisoformat(workflow_run.get("created_at", datetime.now(timezone.utc).isoformat()).replace("Z", "+00:00")),
            completed_at=datetime.fromisoformat(workflow_run.get("updated_at", datetime.now(timezone.utc).isoformat()).replace("Z", "+00:00")),
            url=workflow_run.get("html_url"),
            logs=f"Jenkins build #{workflow_run.get('run_number', 'unknown')}"
        )
        
        # Persist the build
        build = _persist(db, "jenkins", ingest_data)
        
        if build.status == "failure":
            alert_failure(build.pipeline, build.repo, build.url or "", build.logs or "")
        
        # Broadcast real-time update
        await manager.broadcast({
            "event": "build_ingested",
            "data": {
                "pipeline": build.pipeline,
                "repo": build.repo,
                "status": build.status,
                "provider": build.provider
            }
        })
        
        return {"status": "success", "message": "Jenkins webhook processed"}
        
    except Exception as e:
        print(f"Error processing Jenkins webhook: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/webhook/github")
async def webhook_github(payload: dict, db: Session = Depends(get_db)):
    """Handle GitHub Actions webhook payloads"""
    try:
        # Extract data from GitHub webhook format
        workflow_run = payload.get("workflow_run", {})
        repo_info = payload.get("repository", {})
        
        # Only process completed workflows
        if payload.get("action") != "completed":
            return {"status": "ignored", "message": "Only processing completed workflows"}
        
        # Map GitHub data to our internal format
        ingest_data = IngestRequest(
            pipeline=workflow_run.get("name", "unknown"),
            repo=repo_info.get("full_name", "unknown"),
            branch=workflow_run.get("head_branch", "main"),
            status="success" if workflow_run.get("conclusion") == "success" else "failure",
            started_at=datetime.fromisoformat(workflow_run.get("created_at", datetime.now(timezone.utc).isoformat()).replace("Z", "+00:00")),
            completed_at=datetime.fromisoformat(workflow_run.get("updated_at", datetime.now(timezone.utc).isoformat()).replace("Z", "+00:00")),
            url=workflow_run.get("html_url"),
            logs=f"GitHub Actions run #{workflow_run.get('run_number', 'unknown')}"
        )
        
        # Persist the build
        build = _persist(db, "github", ingest_data)
        
        if build.status == "failure":
            alert_failure(build.pipeline, build.repo, build.url or "", build.logs or "")
        
        # Broadcast real-time update
        await manager.broadcast({
            "event": "build_ingested",
            "data": {
                "pipeline": build.pipeline,
                "repo": build.repo,
                "status": build.status,
                "provider": build.provider
            }
        })
        
        return {"status": "success", "message": "GitHub webhook processed"}
        
    except Exception as e:
        print(f"Error processing GitHub webhook: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint for container monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "ci-cd-dashboard-backend"
    }
