"""API bootstrap only; complaint, reporting and session services are not wired yet."""
from __future__ import annotations

import os
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


class HealthResult(BaseModel):
    request_id: str
    service: str = "merlion-express-api"
    status: Literal["degraded"] = "degraded"
    features: dict[str, bool] = Field(default_factory=lambda: {
        "triage": False, "weekly": False, "sessions": False, "semantic_retrieval": False,
    })
    limitations: list[str] = Field(default_factory=lambda: [
        "API bootstrap is running; complaint, reporting and session services are not implemented.",
        "This health check does not probe MySQL, evidence files or the model provider.",
    ])


app = FastAPI(
    title="Merlion Express API",
    version="0.1.0",
    description="Local API bootstrap. Only health is implemented; domain services are pending.",
)
frontend_port = int(os.environ.get("CAPSTONE_FRONTEND_PORT", "5173"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://127.0.0.1:{frontend_port}", f"http://localhost:{frontend_port}"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health", response_model=HealthResult)
def health() -> HealthResult:
    """Report process liveness and explicitly unavailable domain capabilities."""
    return HealthResult(request_id=f"req-{uuid4().hex}")
