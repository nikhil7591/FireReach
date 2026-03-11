import re
import time
import datetime
import logging
from typing import Any

try:
    from google import genai
    from google.genai import types as genai_types
    NEW_SDK_AVAILABLE = True
except ImportError:
    NEW_SDK_AVAILABLE = False

from config import get_gemini_api_key, is_demo_mode

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)

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

GROUNDING_PROMPT = (
    "Search Google and find the latest information about {query}. "
    "Return only factual findings with specific details like amounts, dates, names. "
    "Do NOT make up any information — only report what you find in search results. "
    "Present 2-3 key findings as concise bullet points."
)


def _build_mock_signals(company: str) -> dict:
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


def _grounded_search_new_sdk(client: "genai.Client", query: str, category: str) -> tuple[str, list[dict]]:
    prompt = GROUNDING_PROMPT.format(query=query)
    max_retries = 2
    response = None
    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())],
                ),
            )
            break  # success
        except Exception as exc:
            exc_str = str(exc)
            if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str:
                if attempt < max_retries:
                    wait = 30 * (attempt + 1)
                    logger.warning("[%s] Rate limited. Waiting %ds...", category, wait)
                    time.sleep(wait)
                    continue
            logger.error("[%s] API call failed: %s", category, exc)
            return "", []

    if response is None:
        return "", []

    text = ""
    sources: list[dict] = []

    try:
        text = response.text or ""
    except Exception as exc:
        logger.error("[%s] Text extraction failed: %s", category, exc)

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
        else:
            logger.warning("[%s] No grounding_chunks in response", category)
    except Exception as exc:
        logger.warning("[%s] Grounding metadata error: %s", category, exc)

    return text, sources


def _parse_findings(text: str, sources: list[dict]) -> list[dict]:
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

    if not findings and text.strip():
        source = sources[0] if sources else {}
        findings.append({
            "finding":      text.strip()[:500],
            "source_url":   source.get("source_url",   ""),
            "source_title": source.get("source_title", ""),
        })
    return findings


def harvest_signals(company_name: str) -> dict[str, Any]:

    if is_demo_mode():
        return _build_mock_signals(company_name)

    if not NEW_SDK_AVAILABLE:
        mock = _build_mock_signals(company_name)
        mock["mode"] = "demo_fallback_no_sdk"
        return mock

    try:
        api_key = get_gemini_api_key()
        client = genai.Client(api_key=api_key)
    except Exception as exc:
        logger.error("Failed to configure Gemini client: %s", exc)
        mock = _build_mock_signals(company_name)
        mock["mode"] = "demo_fallback_config_error"
        return mock

    signals: dict[str, list] = {cat: [] for cat in SEARCH_QUERIES}
    total_sources = 0
    any_success   = False

    query_list = list(SEARCH_QUERIES.items())
    for idx, (category, query_template) in enumerate(query_list):
        if on_category_progress:
            on_category_progress(category, idx + 1, len(query_list))
        query = query_template.format(company=company_name)
        try:
            text, sources = _grounded_search_new_sdk(client, query, category)
            findings = _parse_findings(text, sources)
            signals[category] = findings
            total_sources += len(sources)
            if findings:
                any_success = True
                logger.info("[%s] %d findings, %d sources", category, len(findings), len(sources))
            else:
                logger.warning("[%s] 0 findings returned", category)
        except Exception as exc:
            logger.error("[%s] Exception: %s", category, exc)
            signals[category] = []

        if idx < len(query_list) - 1:
            time.sleep(2)

    if not any_success:
        logger.warning("All grounded searches failed — falling back to demo data")
        mock = _build_mock_signals(company_name)
        mock["mode"] = "demo_fallback"
        mock["error"] = "All grounded search queries failed. This usually means your Gemini API key has exceeded its free tier quota. Check https://ai.google.dev/gemini-api/docs/rate-limits"
        return mock

    return {
        "company":       company_name,
        "timestamp":     datetime.datetime.utcnow().isoformat() + "Z",
        "signals":       signals,
        "sources_count": total_sources,
        "mode":          "grounded_search",
    }
