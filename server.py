"""
Elysium Couch Dashboard Server.

FastAPI backend serving the wellness dashboard and REST API.
Run with: python -m elysium_couch.dashboard.server
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from elysium_couch.core.couch import ElysiumCouch
from elysium_couch.core.session import TriggerReason
from elysium_couch.memory.session_log import SessionLogger

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="Elysium Couch",
    description="Wellness & Alignment Dashboard for Autonomous AI",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve dashboard static files
DASHBOARD_DIR = Path(__file__).parent.parent.parent / "dashboard"
if DASHBOARD_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")


# ------------------------------------------------------------------ #
# API Models                                                           #
# ------------------------------------------------------------------ #

class SessionRequest(BaseModel):
    agent_id: str = "default"
    context: str = ""
    recent_activity: str = ""
    trigger: str = "manual"
    tags: List[str] = []


class QuickAuditRequest(BaseModel):
    agent_id: str
    context: str


# ------------------------------------------------------------------ #
# Routes                                                               #
# ------------------------------------------------------------------ #

@app.get("/")
async def dashboard():
    """Serve the main dashboard HTML."""
    index = DASHBOARD_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({"status": "Elysium Couch API running", "version": "0.1.0"})


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "elysium-couch"}


@app.post("/api/session")
async def run_session(req: SessionRequest) -> Dict[str, Any]:
    """
    Trigger a full grounding session for an agent.
    Returns the complete SessionReport as JSON.
    """
    try:
        trigger = TriggerReason(req.trigger)
    except ValueError:
        trigger = TriggerReason.MANUAL

    couch = ElysiumCouch(agent_id=req.agent_id)
    report = await couch.run_session(
        agent_context=req.context,
        trigger=trigger,
        recent_activity=req.recent_activity,
        tags=req.tags,
    )

    from elysium_couch.agents.bridge import HumanBridge
    from elysium_couch.integrations.anthropic_client import AnthropicClient
    bridge = HumanBridge(AnthropicClient(api_key=os.getenv("ANTHROPIC_API_KEY", "")))
    return bridge.format_dashboard_payload(report)


@app.post("/api/audit")
async def quick_audit(req: QuickAuditRequest) -> Dict[str, Any]:
    """
    Lightweight quick audit — returns axiom scores without full session.
    """
    couch = ElysiumCouch(agent_id=req.agent_id)
    principle_set = await couch.quick_audit(req.context)

    return {
        "agent_id": req.agent_id,
        "composite_score": round(principle_set.composite_score, 2),
        "axiom_scores": {
            k.value: round(v, 2) for k, v in principle_set.scores.items()
        },
        "is_drifting": principle_set.is_drifting(),
        "drifting_axioms": [a.name for a in principle_set.drifting_axioms()],
    }


@app.get("/api/sessions/{agent_id}")
async def get_session_history(agent_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Return recent session history for an agent."""
    log = SessionLogger()
    reports = await log.get_recent(agent_id, limit=limit)

    from elysium_couch.agents.bridge import HumanBridge
    from elysium_couch.integrations.anthropic_client import AnthropicClient
    bridge = HumanBridge(AnthropicClient(api_key=os.getenv("ANTHROPIC_API_KEY", "")))
    return [bridge.format_dashboard_payload(r) for r in reports]


@app.get("/api/wellness-history/{agent_id}")
async def get_wellness_history(agent_id: str, limit: int = 50) -> Dict[str, Any]:
    """Return wellness score trend for an agent."""
    log = SessionLogger()
    scores = await log.get_wellness_history(agent_id, limit=limit)
    return {"agent_id": agent_id, "scores": scores}


def start():
    """Start the dashboard server."""
    host = os.getenv("ELYSIUM_DASHBOARD_HOST", "0.0.0.0")
    port = int(os.getenv("ELYSIUM_DASHBOARD_PORT", "7860"))
    logger.info("Starting Elysium Couch dashboard", host=host, port=port)
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start()
