import asyncio
import json as json_module
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from agent import run_agent
from tools.signal_harvester import harvest_signals
from tools.research_analyst import analyze_signals
from tools.outreach_sender import send_outreach, generate_outreach_email, deliver_email

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="FireReach — Autonomous Outreach Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OutreachRequest(BaseModel):
    icp: str = Field(..., min_length=10, max_length=1000)
    company: str = Field(..., min_length=1, max_length=200)
    recipient_email: str = Field(...)

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


class OutreachResponse(BaseModel):
    status: str
    mode: str
    steps: list[dict]
    summary: str
    total_steps: int


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@app.post("/api/outreach", response_model=OutreachResponse)
async def run_outreach(request: OutreachRequest) -> OutreachResponse:
    logger.info("Outreach request — company='%s', email='%s'", request.company, request.recipient_email)
    try:
        result = run_agent(icp=request.icp, company=request.company, recipient_email=request.recipient_email)
        return OutreachResponse(**result)
    except Exception as exc:
        logger.exception("Outreach agent raised an unhandled exception")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(exc)}")


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy", service="FireReach", version="1.0.0")


# ── SSE Streaming Endpoint ─────────────────────────────────────────────────
def _sse_event(data: dict) -> str:
    """Format a dict as an SSE data line."""
    return f"data: {json_module.dumps(data, default=str)}\n\n"


@app.post("/api/outreach/stream")
async def run_outreach_stream(request: OutreachRequest):
    """SSE streaming endpoint — sends real-time progress events."""
    logger.info("Stream outreach — company='%s', email='%s'", request.company, request.recipient_email)

    async def event_generator():
        loop = asyncio.get_event_loop()
        sub_events: asyncio.Queue = asyncio.Queue()
        steps: list[dict] = []
        state: dict = {}

        def signal_progress_cb(category, current, total):
            asyncio.run_coroutine_threadsafe(
                sub_events.put({"type": "signal_category", "category": category, "current": current, "total": total}),
                loop,
            )

        # ── Step 1: Signal Harvester ────────────────────────────
        yield _sse_event({"type": "step_start", "step": 1, "total_steps": 3, "tool": "tool_signal_harvester", "message": "Harvesting buyer signals\u2026"})

        try:
            task = asyncio.ensure_future(asyncio.to_thread(harvest_signals, request.company, signal_progress_cb))
            while not task.done():
                try:
                    evt = await asyncio.wait_for(sub_events.get(), timeout=0.5)
                    yield _sse_event(evt)
                except asyncio.TimeoutError:
                    pass
            signals = task.result()
            state["signals"] = signals
            steps.append({"step": 1, "tool": "tool_signal_harvester", "args": {"company_name": request.company}, "result": signals, "status": "completed"})
            yield _sse_event({"type": "step_done", "step": 1, "tool": "tool_signal_harvester", "result": signals})
        except Exception as exc:
            logger.error("Signal harvester failed: %s", exc)
            steps.append({"step": 1, "tool": "tool_signal_harvester", "args": {"company_name": request.company}, "result": {"error": str(exc)}, "status": "error"})
            yield _sse_event({"type": "step_error", "step": 1, "tool": "tool_signal_harvester", "error": str(exc)})

        # ── Step 2: Research Analyst ────────────────────────────
        yield _sse_event({"type": "step_start", "step": 2, "total_steps": 3, "tool": "tool_research_analyst", "message": "Analyzing signals & building account brief\u2026"})

        try:
            brief = await asyncio.to_thread(analyze_signals, company_name=request.company, icp=request.icp, signals=state.get("signals"))
            state["brief"] = brief
            steps.append({"step": 2, "tool": "tool_research_analyst", "args": {"company_name": request.company, "icp": request.icp}, "result": brief, "status": "completed"})
            yield _sse_event({"type": "step_done", "step": 2, "tool": "tool_research_analyst", "result": brief})
        except Exception as exc:
            logger.error("Research analyst failed: %s", exc)
            steps.append({"step": 2, "tool": "tool_research_analyst", "args": {"company_name": request.company, "icp": request.icp}, "result": {"error": str(exc)}, "status": "error"})
            yield _sse_event({"type": "step_error", "step": 2, "tool": "tool_research_analyst", "error": str(exc)})

        # ── Step 3: Outreach Sender ─────────────────────────────
        yield _sse_event({"type": "step_start", "step": 3, "total_steps": 3, "tool": "tool_outreach_automated_sender", "message": "Crafting personalized email\u2026"})

        try:
            # Generate email content only (fast — just a Groq call)
            email_result = await asyncio.to_thread(
                generate_outreach_email,
                recipient_email=request.recipient_email,
                company_name=request.company,
                icp=request.icp,
                signals=state.get("signals"),
                brief=state.get("brief"),
            )
            steps.append({"step": 3, "tool": "tool_outreach_automated_sender", "args": {"recipient_email": request.recipient_email, "company_name": request.company, "icp": request.icp}, "result": email_result, "status": "completed"})
            yield _sse_event({"type": "step_done", "step": 3, "tool": "tool_outreach_automated_sender", "result": email_result})

            # Fire-and-forget: send the email via SMTP/Resend in background
            subject = email_result.get("email", {}).get("subject", "")
            body = email_result.get("email", {}).get("body", "")
            if subject and body:
                asyncio.ensure_future(asyncio.to_thread(
                    deliver_email, request.recipient_email, subject, body
                ))
        except Exception as exc:
            logger.error("Outreach sender failed: %s", exc)
            steps.append({"step": 3, "tool": "tool_outreach_automated_sender", "args": {"recipient_email": request.recipient_email, "company_name": request.company, "icp": request.icp}, "result": {"error": str(exc)}, "status": "error"})
            yield _sse_event({"type": "step_error", "step": 3, "tool": "tool_outreach_automated_sender", "error": str(exc)})

        # ── Final ───────────────────────────────────────────────
        signal_mode = state.get("signals", {}).get("mode", "unknown")
        sig_count = len(state.get("signals", {}).get("signals", {}))
        summary = (
            f"FireReach completed outreach for {request.company}. "
            f"Harvested {sig_count} signal categories, "
            "created account brief, and generated personalized email."
        )
        yield _sse_event({
            "type": "complete",
            "result": {
                "status": "completed",
                "mode": signal_mode,
                "steps": steps,
                "summary": summary,
                "total_steps": len(steps),
            },
        })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
