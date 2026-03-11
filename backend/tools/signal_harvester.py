"""
tools/signal_harvester.py — Tool 1: Deterministic Buyer Signal Fetcher.

Uses google-genai (NEW SDK) with Google Search Grounding to fetch REAL signals.
The old google-generativeai SDK is DEPRECATED and grounding silently fails in it.

Signal categories (8):
  funding · hiring · leadership · news · tech_stack ·
  g2_reviews · social_mentions · competitor_churn
"""

import re
import datetime
import logging
import traceback
from typing import Any

# ── NEW SDK — google-genai ────────────────────────────────────────────────────
# Install: pip install google-genai
try:
    from google import genai
    from google.genai import types as genai_types
    NEW_SDK_AVAILABLE = True
except ImportError:
    NEW_SDK_AVAILABLE = False
    print("=" * 70)
    print("ERROR: 'google-genai' package NOT installed!")
    print("Run:  pip install google-genai")
    print("The old 'google-generativeai' package is DEPRECATED and grounding")
    print("silently fails in it. You MUST use 'google-genai' instead.")
    print("=" * 70)

from config import get_gemini_api_key, is_demo_mode

logger = logging.getLogger(__name__)

# Force INFO level so grounding logs always show in console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)


# ─────────────────────────────────────────────
# SEARCH QUERY TEMPLATES (8 categories)
# ─────────────────────────────────────────────
SEARCH_QUERIES = {
    "funding":          "{company} funding round investment 2024 2025",
    "hiring":           "{company} hiring jobs careers open positions",
    "leadership":       "{company} new CTO CEO CISO VP leadership changes",
    "news":             "{company} news expansion growth announcement",
    "tech_stack":       "{company} technology stack platform engineering",
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
            "funding": [{"finding": f"{company} raised a $100M Series C led by Sequoia Capital at a $1.2B valuation (Q1 2025).", "source_url": "https://techcrunch.com/demo", "source_title": "TechCrunch (Demo)"}],
            "hiring": [{"finding": f"{company} posted 45+ open roles in Sales, Security Engineering, and Cloud Infrastructure on LinkedIn (March 2025).", "source_url": "https://linkedin.com/jobs/demo", "source_title": "LinkedIn Jobs (Demo)"}],
            "leadership": [{"finding": f"{company} appointed a new Chief Security Officer from CrowdStrike, signaling an enterprise security push.", "source_url": "https://businesswire.com/demo", "source_title": "BusinessWire (Demo)"}],
            "news": [{"finding": f"{company} announced expansion into EMEA region and launched a new Compliance Automation product suite.", "source_url": "https://prnewswire.com/demo", "source_title": "PR Newswire (Demo)"}],
            "tech_stack": [{"finding": f"{company} runs on AWS and GCP with a Kubernetes-native architecture; uses Terraform, Go, and React.", "source_url": "https://stackshare.io/demo", "source_title": "StackShare (Demo)"}],
            "g2_reviews": [{"finding": f"{company} is actively being compared against competitors on G2, with 30+ new reviews in Q1 2025 indicating active vendor evaluation.", "source_url": "https://g2.com/demo", "source_title": "G2 Reviews (Demo)"}],
            "social_mentions": [{"finding": f"{company} team members posted 12+ LinkedIn updates about company growth, new product launches, and team expansion in the last 30 days.", "source_url": "https://linkedin.com/demo", "source_title": "LinkedIn (Demo)"}],
            "competitor_churn": [{"finding": f"{company} employees mentioned migrating away from a legacy security training vendor, citing gaps in content quality and reporting.", "source_url": "https://reddit.com/demo", "source_title": "Reddit / Community (Demo)"}],
        },
        "sources_count": 8,
        "mode": "demo",
    }


# ─────────────────────────────────────────────
# GROUNDED SEARCH — NEW SDK (google-genai)
# ─────────────────────────────────────────────
def _grounded_search_new_sdk(client: "genai.Client", query: str, category: str) -> tuple[str, list[dict]]:
    """
    Use the NEW google-genai SDK to do a grounded Google Search.
    Returns (response_text, list_of_sources).
    """
    prompt = GROUNDING_PROMPT.format(query=query)

    print(f"\n[SIGNAL HARVESTER] Searching [{category}]: {query}")
    logger.info("[%s] Sending grounded search query to Gemini...", category)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())],
            ),
        )
    except Exception as exc:
        print(f"[SIGNAL HARVESTER] ERROR [{category}] API call failed: {exc}")
        print(traceback.format_exc())
        logger.error("[%s] API call failed: %s", category, exc)
        return "", []

    text = ""
    sources: list[dict] = []

    # Extract text
    try:
        text = response.text or ""
        print(f"[SIGNAL HARVESTER] [{category}] Got {len(text)} chars text response")
    except Exception as exc:
        print(f"[SIGNAL HARVESTER] [{category}] Text extraction failed: {exc}")
        logger.error("[%s] Text extraction failed: %s", category, exc)

    # Extract grounding metadata sources
    try:
        candidate = response.candidates[0]
        gm = candidate.grounding_metadata
        if gm and gm.grounding_chunks:
            for chunk in gm.grounding_chunks:
                try:
                    uri   = chunk.web.uri   or ""
                    title = chunk.web.title or ""
                    if uri:
                        sources.append({"source_url": uri, "source_title": title})
                except Exception:
                    pass
            print(f"[SIGNAL HARVESTER] [{category}] Found {len(sources)} grounding sources")
        else:
            print(f"[SIGNAL HARVESTER] [{category}] WARNING: No grounding_chunks in response (grounding may not be active)")
            logger.warning("[%s] No grounding_chunks — grounding may require a paid/eligible API key", category)
    except Exception as exc:
        print(f"[SIGNAL HARVESTER] [{category}] Grounding metadata extraction failed: {exc}")
        logger.warning("[%s] Grounding metadata error: %s", category, exc)

    return text, sources


# ─────────────────────────────────────────────
# PARSE TEXT → LIST OF FINDINGS
# ─────────────────────────────────────────────
def _parse_findings(text: str, sources: list[dict]) -> list[dict]:
    """Convert raw response text + sources into structured findings."""
    if not text.strip():
        return []

    findings: list[dict] = []
    lines = re.split(r"\n+", text.strip())
    for i, line in enumerate(lines):
        line = re.sub(r"^[\*\-•\d+\.\s]+", "", line).strip()
        if len(line) < 15:
            continue
        source = sources[i] if i < len(sources) else (sources[0] if sources else {})
        findings.append({
            "finding":      line,
            "source_url":   source.get("source_url",   ""),
            "source_title": source.get("source_title", ""),
        })

    # Ensure at least one entry if text exists
    if not findings and text.strip():
        source = sources[0] if sources else {}
        findings.append({
            "finding":      text.strip()[:500],
            "source_url":   source.get("source_url",   ""),
            "source_title": source.get("source_title", ""),
        })
    return findings


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────
def harvest_signals(company_name: str) -> dict[str, Any]:
    """
    Tool 1 — Fetch REAL buyer signals using Gemini 2.0 Flash + Google Search Grounding.

    Uses the NEW google-genai SDK (not the deprecated google-generativeai).
    Falls back to demo data if new SDK is not installed or all queries fail.
    """
    print("\n" + "=" * 65)
    print(f"[SIGNAL HARVESTER] Starting for company: {company_name}")
    print(f"[SIGNAL HARVESTER] NEW_SDK_AVAILABLE: {NEW_SDK_AVAILABLE}")
    print(f"[SIGNAL HARVESTER] DEMO_MODE: {is_demo_mode()}")
    print("=" * 65)

    # ── Demo mode shortcut ──────────────────────────────────────
    if is_demo_mode():
        print("[SIGNAL HARVESTER] DEMO_MODE=true → returning mock signals")
        logger.info("DEMO_MODE active — returning mock signals for '%s'", company_name)
        return _build_mock_signals(company_name)

    # ── Check new SDK availability ───────────────────────────────
    if not NEW_SDK_AVAILABLE:
        print("[SIGNAL HARVESTER] FATAL: google-genai not installed! Using demo fallback.")
        print("[SIGNAL HARVESTER] Fix: pip install google-genai")
        mock = _build_mock_signals(company_name)
        mock["mode"] = "demo_fallback_no_sdk"
        return mock

    # ── Configure NEW SDK client ─────────────────────────────────
    try:
        api_key = get_gemini_api_key()
        print(f"[SIGNAL HARVESTER] API key loaded: {api_key[:8]}...{api_key[-4:]}")
        client = genai.Client(api_key=api_key)
        print("[SIGNAL HARVESTER] google-genai Client initialized OK")
    except Exception as exc:
        print(f"[SIGNAL HARVESTER] FATAL: Failed to init Gemini client: {exc}")
        print(traceback.format_exc())
        logger.error("Failed to configure Gemini client: %s — using demo data", exc)
        mock = _build_mock_signals(company_name)
        mock["mode"] = "demo_fallback_config_error"
        return mock

    # ── Run 8 grounded searches ──────────────────────────────────
    signals: dict[str, list] = {cat: [] for cat in SEARCH_QUERIES}
    total_sources = 0
    any_success   = False

    for category, query_template in SEARCH_QUERIES.items():
        query = query_template.format(company=company_name)
        try:
            text, sources = _grounded_search_new_sdk(client, query, category)
            findings = _parse_findings(text, sources)
            signals[category] = findings
            total_sources += len(sources)
            if findings:
                any_success = True
                print(f"[SIGNAL HARVESTER] ✓ [{category}] {len(findings)} findings, {len(sources)} sources")
                logger.info("✓ [%s] %d findings, %d sources", category, len(findings), len(sources))
            else:
                print(f"[SIGNAL HARVESTER] ✗ [{category}] 0 findings (text_len={len(text)}, sources={len(sources)})")
                logger.warning("✗ [%s] 0 findings returned", category)
        except Exception as exc:
            print(f"[SIGNAL HARVESTER] ERROR [{category}]: {exc}")
            print(traceback.format_exc())
            logger.error("[%s] Exception: %s", category, exc)
            signals[category] = []

    print(f"\n[SIGNAL HARVESTER] Done. any_success={any_success}, total_sources={total_sources}")

    # ── If every query failed → fall back to demo ────────────────
    if not any_success:
        print("[SIGNAL HARVESTER] WARNING: All queries failed → using demo_fallback data")
        logger.warning("All grounded searches failed — falling back to demo data")
        mock = _build_mock_signals(company_name)
        mock["mode"] = "demo_fallback"
        return mock

    return {
        "company":       company_name,
        "timestamp":     datetime.datetime.utcnow().isoformat() + "Z",
        "signals":       signals,
        "sources_count": total_sources,
        "mode":          "grounded_search",
    }
