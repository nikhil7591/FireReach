import json
import logging
import re
from typing import Any

import google.generativeai as genai
from config import get_gemini_api_key

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """
You are a senior sales intelligence analyst. You have been given:
1. Buyer signals recently harvested about a target company.
2. The seller's Ideal Customer Profile (ICP).

Your job: Produce a concise, actionable account brief in pure JSON.

TARGET COMPANY: {company_name}

ICP (who we sell to and what we offer):
{icp}

BUYER SIGNALS (real data — treat as ground truth):
{signals_json}

Respond ONLY with a valid JSON object matching this EXACT schema — no markdown fences, no extra text:
{{
  "account_brief": "Paragraph 1: Specific pain points or opportunities you infer from the signals above.\\n\\nParagraph 2: How our ICP / offering maps to those opportunities.",
  "key_signals_identified": ["<specific signal 1>", "<specific signal 2>", "<specific signal 3>"],
  "pain_points": ["<pain 1>", "<pain 2>", "<pain 3>"],
  "recommended_angle": "<one-sentence best outreach angle for a cold email>"
}}

CRITICAL RULES:
- Reference SPECIFIC data from the signals (amounts, names, dates, technologies).
- Do NOT invent facts not present in the signals.
- Keep account_brief under 120 words total.
- key_signals_identified must be direct quotes or paraphrases from the signals.
- recommended_angle must be one sentence, actionable, specific to this company.
"""


def _extract_json(raw: str) -> dict:
    # Remove ```json ... ``` or ``` ... ```
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    raw = raw.rstrip("`").strip()

    # Find the first { ... } block
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in model response.")
    return json.loads(raw[start:end])


def _summarize_signals(signals_data: dict) -> str:
    signals = signals_data.get("signals", {})
    lines = []
    for category, findings in signals.items():
        if not findings:
            continue
        lines.append(f"[{category.upper()}]")
        for f in findings[:3]:  # cap at 3 per category to control token usage
            finding_text = f.get("finding", "")
            source = f.get("source_title", "")
            lines.append(f"  • {finding_text}" + (f" [Source: {source}]" if source else ""))
    return "\n".join(lines) if lines else "No signals available."


def analyze_signals(
    company_name: str,
    icp: str,
    signals: dict | None = None,
) -> dict[str, Any]:
    signals_json = _summarize_signals(signals or {})


    try:
        api_key = get_gemini_api_key()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")
    except Exception as exc:
        logger.error("Failed to configure Gemini for analysis: %s", exc)
        return _fallback_brief(company_name, icp)


    prompt = ANALYSIS_PROMPT.format(
        company_name=company_name,
        icp=icp,
        signals_json=signals_json,
    )


    try:
        response = model.generate_content(prompt)
        raw_text = response.text or ""
    except Exception as exc:
        logger.error("Gemini generation failed: %s", exc)
        return _fallback_brief(company_name, icp)


    try:
        brief = _extract_json(raw_text)
    except Exception as exc:
        logger.warning("Failed to parse JSON from model: %s\nRaw: %s", exc, raw_text[:300])
        return _fallback_brief(company_name, icp)

    brief["company"] = company_name
    brief["status"] = "success"
    return brief


def _fallback_brief(company_name: str, icp: str) -> dict:
    return {
        "account_brief": (
            f"{company_name} shows strong growth signals that align with our offering. "
            "Their recent activity suggests investment in scaling operations.\n\n"
            f"Our ICP ({icp[:80]}...) maps well to their current stage."
        ),
        "key_signals_identified": [
            f"{company_name} is actively growing",
            "Signals suggest technology investment",
        ],
        "pain_points": [
            "Scaling teams rapidly",
            "Maintaining security posture during growth",
        ],
        "recommended_angle": (
            f"Reach out to {company_name} with a value proposition tied to their growth phase."
        ),
        "company": company_name,
        "status": "fallback",
    }
