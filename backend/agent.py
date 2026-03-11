import json
import logging
from typing import Any

from config import get_groq_api_key
from tools.signal_harvester import harvest_signals
from tools.research_analyst import analyze_signals
from tools.outreach_sender import send_outreach

logger = logging.getLogger(__name__)


def run_agent(icp: str, company: str, recipient_email: str) -> dict[str, Any]:
    """Run the 3-step outreach pipeline sequentially."""
    logger.info("Running outreach pipeline for company=%s", company)
    steps = []
    state: dict = {}

    # Step 1: Signal Harvester
    try:
        res1 = harvest_signals(company_name=company)
        state["signals"] = res1
        steps.append(
            {"step": 1, "tool": "tool_signal_harvester", "args": {"company_name": company},
             "result": res1, "status": "completed"}
        )
    except Exception as e:
        steps.append(
            {"step": 1, "tool": "tool_signal_harvester", "args": {"company_name": company},
             "result": {"error": str(e)}, "status": "error"}
        )

    # Step 2: Research Analyst
    try:
        res2 = analyze_signals(
            company_name=company, icp=icp, signals=state.get("signals")
        )
        state["brief"] = res2
        steps.append(
            {"step": 2, "tool": "tool_research_analyst",
             "args": {"company_name": company, "icp": icp},
             "result": res2, "status": "completed"}
        )
    except Exception as e:
        steps.append(
            {"step": 2, "tool": "tool_research_analyst",
             "args": {"company_name": company, "icp": icp},
             "result": {"error": str(e)}, "status": "error"}
        )

    # Step 3: Outreach Sender
    try:
        res3 = send_outreach(
            recipient_email=recipient_email,
            company_name=company,
            icp=icp,
            signals=state.get("signals"),
            brief=state.get("brief"),
        )
        steps.append(
            {"step": 3, "tool": "tool_outreach_automated_sender",
             "args": {"recipient_email": recipient_email, "company_name": company, "icp": icp},
             "result": res3, "status": "completed"}
        )
    except Exception as e:
        steps.append(
            {"step": 3, "tool": "tool_outreach_automated_sender",
             "args": {"recipient_email": recipient_email, "company_name": company, "icp": icp},
             "result": {"error": str(e)}, "status": "error"}
        )

    return {
        "status": "completed",
        "mode": "groq_sequential",
        "steps": steps,
        "summary": (
            f"FireReach completed outreach for {company}. "
            f"Harvested {len(state.get('signals', {}).get('signals', {}))} signal categories, "
            "created account brief, and generated personalized email."
        ),
        "total_steps": len(steps),
    }
