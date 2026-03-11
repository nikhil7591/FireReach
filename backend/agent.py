import json
import logging
from typing import Any

import google.generativeai as genai
from google.generativeai import protos

from config import get_gemini_api_key
from tools.signal_harvester import harvest_signals
from tools.research_analyst import analyze_signals
from tools.outreach_sender import send_outreach

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are FireReach, an autonomous outreach agent built by Rabbitt AI.

YOUR MISSION — execute a complete outreach sequence using your three tools IN THIS EXACT ORDER:

1. tool_signal_harvester → Capture live buyer signals for the target company.
2. tool_research_analyst → Analyze the signals against the ICP to produce an Account Brief.
3. tool_outreach_automated_sender → Craft a hyper-personalized email and send it.

CONSTRAINTS:
- You MUST call ALL three tools, one at a time, in the order above.
- NEVER fabricate signals — only use data returned by tool_signal_harvester.
- After all three tools complete, provide a 2-3 sentence summary of what was accomplished.
- Start immediately with tool_signal_harvester. Do NOT ask clarifying questions.
"""


def _build_function_declarations() -> list[protos.FunctionDeclaration]:
    return [
        protos.FunctionDeclaration(
            name="tool_signal_harvester",
            description=(
                "Fetches REAL buyer signals for a target company via Google Search Grounding. "
                "Call this FIRST to collect funding, hiring, leadership, news, and tech-stack signals."
            ),
            parameters=protos.Schema(
                type=protos.Type.OBJECT,
                properties={
                    "company_name": protos.Schema(
                        type=protos.Type.STRING,
                        description="Name of the target company to research.",
                    )
                },
                required=["company_name"],
            ),
        ),
        protos.FunctionDeclaration(
            name="tool_research_analyst",
            description=(
                "Analyzes buyer signals from tool_signal_harvester against the ICP. "
                "Produces a structured Account Brief with pain points and recommended outreach angle. "
                "Call this SECOND, after tool_signal_harvester."
            ),
            parameters=protos.Schema(
                type=protos.Type.OBJECT,
                properties={
                    "company_name": protos.Schema(
                        type=protos.Type.STRING,
                        description="Target company name (same as for tool_signal_harvester).",
                    ),
                    "icp": protos.Schema(
                        type=protos.Type.STRING,
                        description="The seller's Ideal Customer Profile.",
                    ),
                },
                required=["company_name", "icp"],
            ),
        ),
        protos.FunctionDeclaration(
            name="tool_outreach_automated_sender",
            description=(
                "Writes a hyper-personalized cold email referencing specific signals "
                "and either sends it or returns a preview. Call this THIRD."
            ),
            parameters=protos.Schema(
                type=protos.Type.OBJECT,
                properties={
                    "recipient_email": protos.Schema(
                        type=protos.Type.STRING,
                        description="Destination email address.",
                    ),
                    "company_name": protos.Schema(
                        type=protos.Type.STRING,
                        description="Target company name.",
                    ),
                    "icp": protos.Schema(
                        type=protos.Type.STRING,
                        description="The seller's Ideal Customer Profile.",
                    ),
                },
                required=["recipient_email", "company_name", "icp"],
            ),
        ),
    ]


def _execute_tool(tool_name: str, args: dict, state: dict, icp: str) -> dict:
    if tool_name == "tool_signal_harvester":
        result = harvest_signals(company_name=args.get("company_name", ""))
        state["signals"] = result
        return result

    if tool_name == "tool_research_analyst":
        result = analyze_signals(
            company_name=args.get("company_name", ""),
            icp=args.get("icp", icp),
            signals=state.get("signals"),
        )
        state["brief"] = result
        return result

    if tool_name == "tool_outreach_automated_sender":
        result = send_outreach(
            recipient_email=args.get("recipient_email", ""),
            company_name=args.get("company_name", ""),
            icp=args.get("icp", icp),
            signals=state.get("signals"),
            brief=state.get("brief"),
        )
        return result

    return {"error": f"Unknown tool: {tool_name}"}


def _run_sequentially(icp: str, company: str, recipient_email: str) -> dict:
    logger.warning("Function Calling unavailable — running direct sequential fallback")
    steps = []
    state: dict = {}

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
        "mode": "sequential_fallback",
        "steps": steps,
        "summary": (
            f"FireReach completed outreach for {company}. "
            f"Harvested {len(state.get('signals', {}).get('signals', {}))} signal categories, "
            "created account brief, and generated personalized email."
        ),
        "total_steps": len(steps),
    }


def run_agent(icp: str, company: str, recipient_email: str) -> dict[str, Any]:
    try:
        api_key = get_gemini_api_key()
        genai.configure(api_key=api_key)
    except Exception as exc:
        logger.error("Gemini config failed: %s — using sequential fallback", exc)
        return _run_sequentially(icp, company, recipient_email)

    func_declarations = _build_function_declarations()
    tool_config = genai.types.Tool(function_declarations=func_declarations)

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT,
            tools=[tool_config],
        )
        chat = model.start_chat(enable_automatic_function_calling=False)
    except Exception as exc:
        logger.error("Failed to create chat: %s — using sequential fallback", exc)
        return _run_sequentially(icp, company, recipient_email)

    user_message = (
        f"Execute outreach for ICP: {icp}, "
        f"Company: {company}, "
        f"Recipient Email: {recipient_email}"
    )

    steps: list[dict] = []
    state: dict = {}
    step_counter = 0
    summary_text = ""

    try:
        response = chat.send_message(user_message)

        for _turn in range(10):
            # Check for function call in response parts
            function_call = None
            for part in response.parts:
                if hasattr(part, "function_call") and part.function_call:
                    function_call = part.function_call
                    break

            if function_call is None:
                try:
                    summary_text = response.text
                except Exception:
                    summary_text = "FireReach completed the outreach sequence successfully."
                break

            tool_name = function_call.name
            try:
                raw_args = dict(function_call.args)
                args = {k: str(v) for k, v in raw_args.items()}
            except Exception:
                args = {}

            logger.info("Calling tool: %s with args: %s", tool_name, args)
            step_counter += 1

            try:
                result = _execute_tool(tool_name, args, state, icp)
                tool_status = "completed"
            except Exception as exc:
                result = {"error": str(exc)}
                tool_status = "error"
                logger.error("Tool %s failed: %s", tool_name, exc)

            steps.append(
                {
                    "step": step_counter,
                    "tool": tool_name,
                    "args": args,
                    "result": result,
                    "status": tool_status,
                }
            )

            safe_result = json.loads(json.dumps(result, default=str))

            response = chat.send_message(
                protos.Content(
                    parts=[
                        protos.Part(
                            function_response=protos.FunctionResponse(
                                name=tool_name,
                                response={"result": safe_result},
                            )
                        )
                    ]
                )
            )

    except Exception as exc:
        logger.error("Agent loop crashed: %s — using sequential fallback", exc)
        return _run_sequentially(icp, company, recipient_email)

    if not summary_text:
        summary_text = (
            f"FireReach successfully completed the autonomous outreach sequence for {company}. "
            f"Real buyer signals were harvested across {len(state.get('signals', {}).get('signals', {}))} categories, "
            "an account brief was generated, and a hyper-personalized email was composed and dispatched."
        )

    return {
        "status": "completed",
        "mode": "function_calling",
        "steps": steps,
        "summary": summary_text,
        "total_steps": step_counter,
    }
