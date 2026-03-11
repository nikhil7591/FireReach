"""
tools/signal_harvester.py — Tool 1: Deterministic Buyer Signal Fetcher.

Uses Gemini 2.0 Flash with Google Search Grounding to retrieve REAL signals
about a target company. Falls back to realistic mock data in DEMO_MODE or on API
failure so the rest of the pipeline can always proceed.

Signal categories:
  funding · hiring · leadership · news · tech_stack
"""

import re
import json
import datetime
import logging
from typing import Any

import google.generativeai as genai
from config import get_gemini_api_key, is_demo_mode

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# SEARCH QUERY TEMPLATES (8 categories)
# ─────────────────────────────────────────────
SEARCH_QUERIES = {
    "funding":          "{company} funding round investment 2024 2025",
    "hiring":           "{company} hiring jobs careers open positions",
    "leadership":       "{company} new CTO CEO CISO VP leadership changes",
    "news":             "{company} news expansion growth announcement",
    "tech_stack":       "{company} technology stack platform engineering",
    # ── New intent signals ──────────────────────────────────────
    "g2_reviews":       "{company} G2 reviews software comparison alternatives evaluation 2025",
    "social_mentions":  "{company} LinkedIn Twitter announcement post team growth 2025",
    "competitor_churn": "{company} switched replaced migrated from competitor vendor tool 2025",
}

# Grounding prompt template
GROUNDING_PROMPT = (
    "Search Google and find the latest information about {query}. "
    "Return only factual findings with specific details like amounts, dates, names. "
    "Do NOT make up any information — only report what you find in search results. "
    "Present 2-3 key findings as concise bullet points."
)


# ─────────────────────────────────────────────
# MOCK / DEMO DATA
# ─────────────────────────────────────────────
def _build_mock_signals(company: str) -> dict:
    """Return realistic demo signals when DEMO_MODE=true or real fetch fails."""
    return {
        "company": company,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "signals": {
            "funding": [
                {
                    "finding": f"{company} raised a $100M Series C led by Sequoia Capital at a $1.2B valuation (Q1 2025).",
                    "source_url": "https://techcrunch.com/demo",
                    "source_title": "TechCrunch (Demo)",
                }
            ],
            "hiring": [
                {
                    "finding": f"{company} posted 45+ open roles in Sales, Security Engineering, and Cloud Infrastructure on LinkedIn (March 2025).",
                    "source_url": "https://linkedin.com/jobs/demo",
                    "source_title": "LinkedIn Jobs (Demo)",
                }
            ],
            "leadership": [
                {
                    "finding": f"{company} appointed a new Chief Security Officer from CrowdStrike, signaling an enterprise security push.",
                    "source_url": "https://businesswire.com/demo",
                    "source_title": "BusinessWire (Demo)",
                }
            ],
            "news": [
                {
                    "finding": f"{company} announced expansion into EMEA region and launched a new Compliance Automation product suite.",
                    "source_url": "https://prnewswire.com/demo",
                    "source_title": "PR Newswire (Demo)",
                }
            ],
            "tech_stack": [
                {
                    "finding": f"{company} runs on AWS and GCP with a Kubernetes-native architecture; uses Terraform, Go, and React.",
                    "source_url": "https://stackshare.io/demo",
                    "source_title": "StackShare (Demo)",
                }
            ],
            "g2_reviews": [
                {
                    "finding": f"{company} is actively being compared against competitors on G2, with 30+ new reviews in Q1 2025 indicating active vendor evaluation.",
                    "source_url": "https://g2.com/demo",
                    "source_title": "G2 Reviews (Demo)",
                }
            ],
            "social_mentions": [
                {
                    "finding": f"{company} team members posted 12+ LinkedIn updates about company growth, new product launches, and team expansion in the last 30 days.",
                    "source_url": "https://linkedin.com/demo",
                    "source_title": "LinkedIn (Demo)",
                }
            ],
            "competitor_churn": [
                {
                    "finding": f"{company} employees mentioned migrating away from a legacy security training vendor, citing gaps in content quality and reporting.",
                    "source_url": "https://reddit.com/demo",
                    "source_title": "Reddit / Community (Demo)",
                }
            ],
        },
        "sources_count": 8,
        "mode": "demo",
    }


# ─────────────────────────────────────────────
# GROUNDED SEARCH — single category
# ─────────────────────────────────────────────
def _grounded_search(model: genai.GenerativeModel, query: str) -> tuple[str, list[dict]]:
    """
    Call Gemini with Google Search grounding for a single query.
    Returns (text_response, list_of_sources).
    """
    prompt = GROUNDING_PROMPT.format(query=query)

    try:
        response = model.generate_content(prompt)
    except Exception as exc:
        logger.warning("Grounded search failed for query '%s': %s", query, exc)
        return "", []

    text = ""
    sources: list[dict] = []

    # Extract text from the first candidate
    try:
        text = response.text or ""
    except Exception:
        try:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text"):
                    text += part.text
        except Exception:
            pass

    # Extract grounding metadata (source URLs / titles)
    try:
        grounding_meta = response.candidates[0].grounding_metadata
        if grounding_meta:
            for chunk in grounding_meta.grounding_chunks:
                try:
                    sources.append(
                        {
                            "source_url": chunk.web.uri or "",
                            "source_title": chunk.web.title or "",
                        }
                    )
                except Exception:
                    pass
    except Exception:
        pass  # grounding_metadata may not exist in all response types

    return text, sources


# ─────────────────────────────────────────────
# PARSE TEXT → LIST OF FINDINGS
# ─────────────────────────────────────────────
def _parse_findings(text: str, sources: list[dict]) -> list[dict]:
    """
    Convert raw response text + source list into structured findings.
    Each finding gets the first available source attached.
    """
    if not text.strip():
        return []

    findings: list[dict] = []
    # Split on bullet points or numbered lines
    lines = re.split(r"\n+", text.strip())
    for i, line in enumerate(lines):
        line = re.sub(r"^[\*\-•\d+\.\s]+", "", line).strip()
        if len(line) < 15:
            continue  # skip very short / empty lines
        source = sources[i] if i < len(sources) else (sources[0] if sources else {})
        findings.append(
            {
                "finding": line,
                "source_url": source.get("source_url", ""),
                "source_title": source.get("source_title", ""),
            }
        )

    # Ensure at least one entry
    if not findings and text.strip():
        source = sources[0] if sources else {}
        findings.append(
            {
                "finding": text.strip()[:500],
                "source_url": source.get("source_url", ""),
                "source_title": source.get("source_title", ""),
            }
        )
    return findings


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────
def harvest_signals(company_name: str) -> dict[str, Any]:
    """
    Tool 1 — Fetch REAL buyer signals for 'company_name' using Gemini grounded search.

    Falls back to demo data when:
      - DEMO_MODE env var is 'true'
      - Gemini API key is missing or invalid
      - All 5 search queries fail

    Returns a structured signals dict.
    """
    # ── Demo mode shortcut ──────────────────────────────────────
    if is_demo_mode():
        logger.info("DEMO_MODE active — returning mock signals for '%s'", company_name)
        return _build_mock_signals(company_name)

    # ── Configure Gemini with Google Search grounding ────────────
    try:
        api_key = get_gemini_api_key()
        genai.configure(api_key=api_key)

        # Create model with google_search_retrieval grounding tool
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            tools="google_search_retrieval",
        )
    except Exception as exc:
        logger.error("Failed to configure Gemini: %s — using demo data", exc)
        return _build_mock_signals(company_name)

    # ── Run 5 grounded searches ──────────────────────────────────
    signals: dict[str, list] = {cat: [] for cat in SEARCH_QUERIES}
    total_sources = 0
    any_success = False

    for category, query_template in SEARCH_QUERIES.items():
        query = query_template.format(company=company_name)
        logger.info("Grounded search [%s]: %s", category, query)

        try:
            text, sources = _grounded_search(model, query)
            findings = _parse_findings(text, sources)
            signals[category] = findings
            total_sources += len(sources)
            if findings:
                any_success = True
        except Exception as exc:
            logger.warning("Category '%s' failed: %s — skipping", category, exc)
            signals[category] = []

    # ── If every query failed → fall back to demo ────────────────
    if not any_success:
        logger.warning("All grounded searches failed — falling back to demo data")
        mock = _build_mock_signals(company_name)
        mock["mode"] = "demo_fallback"
        return mock

    return {
        "company": company_name,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "signals": signals,
        "sources_count": total_sources,
        "mode": "grounded_search",
    }
