"""
main.py — FireReach FastAPI Application.

Endpoints:
  POST /api/outreach  — Run the full autonomous outreach agent.
  GET  /api/health    — Health check.
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from agent import run_agent

# ─────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# APP INSTANCE
# ─────────────────────────────────────────────
app = FastAPI(
    title="FireReach — Autonomous Outreach Engine",
    description=(
        "AI agent that harvests real buyer signals, writes hyper-personalized emails, "
        "and sends them automatically. Powered by Rabbitt AI × Google Gemini."
    ),
    version="1.0.0",
)

# ─────────────────────────────────────────────
# CORS (allow all origins for frontend dev + production)
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────────
class OutreachRequest(BaseModel):
    """Input body for POST /api/outreach."""

    icp: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Ideal Customer Profile — describe who you sell to and what you offer.",
        examples=["We sell high-end cybersecurity training to Series B startups."],
    )
    company: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Target company name to research.",
        examples=["Wiz"],
    )
    recipient_email: str = Field(
        ...,
        description="Recipient's email address for the outreach email.",
        examples=["ciso@example.com"],
    )

    @field_validator("recipient_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address format.")
        return v.strip()

    @field_validator("company")
    @classmethod
    def validate_company(cls, v: str) -> str:
        return v.strip()


class StepResult(BaseModel):
    """A single tool-call step result."""

    step: int
    tool: str
    args: dict
    result: dict
    status: str  # "completed" | "error"


class OutreachResponse(BaseModel):
    """Response from POST /api/outreach."""

    status: str
    mode: str
    steps: list[dict]
    summary: str
    total_steps: int


class HealthResponse(BaseModel):
    """Response from GET /api/health."""

    status: str
    service: str
    version: str


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────
@app.post(
    "/api/outreach",
    response_model=OutreachResponse,
    summary="Run full autonomous outreach sequence",
    description=(
        "Triggers the FireReach agent which:\n"
        "1. Harvests real buyer signals via Gemini Google Search Grounding.\n"
        "2. Analyzes signals against the ICP to create an Account Brief.\n"
        "3. Writes and sends a hyper-personalized cold email."
    ),
)
async def run_outreach(request: OutreachRequest) -> OutreachResponse:
    """Execute the 3-tool autonomous outreach pipeline."""
    logger.info(
        "Outreach request — company='%s', email='%s'",
        request.company,
        request.recipient_email,
    )
    try:
        result = run_agent(
            icp=request.icp,
            company=request.company,
            recipient_email=request.recipient_email,
        )
        return OutreachResponse(**result)
    except Exception as exc:
        logger.exception("Outreach agent raised an unhandled exception")
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution failed: {str(exc)}",
        )


@app.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Health check",
)
async def health_check() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(
        status="healthy",
        service="FireReach",
        version="1.0.0",
    )


# ─────────────────────────────────────────────
# ENTRYPOINT (for local dev: python main.py)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
