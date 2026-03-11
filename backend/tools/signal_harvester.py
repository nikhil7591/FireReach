import re
import datetime
import logging
from typing import Any

from groq import Groq

from config import get_groq_api_key, get_groq_model, is_demo_mode

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

SIGNAL_PROMPT = (
    "You are a sales intelligence researcher. Provide the latest known information about: {query}\n\n"
    "Return 2-3 specific, factual findings as concise bullet points. "
    "Include specific details like amounts, dates, names when possible.\n"
    "Format each finding on its own line starting with •"
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


def _query_groq(client: Groq, query: str, category: str) -> str:
    """Query Groq for signal information about a company."""
    prompt = SIGNAL_PROMPT.format(query=query)
    try:
        response = client.chat.completions.create(
            model=get_groq_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        logger.error("[%s] Groq API call failed: %s", category, exc)
        return ""


def _parse_findings(text: str) -> list[dict]:
    if not text.strip():
        return []

    findings: list[dict] = []
    lines = re.split(r"\n+", text.strip())
    for line in lines:
        line = re.sub(r"^[\*\-•\d+\.\s]+", "", line).strip()
        if len(line) < 15:
            continue
        findings.append({
            "finding":      line,
            "source_url":   "",
            "source_title": "Groq AI Analysis",
        })

    if not findings and text.strip():
        findings.append({
            "finding":      text.strip()[:500],
            "source_url":   "",
            "source_title": "Groq AI Analysis",
        })
    return findings


def harvest_signals(company_name: str, on_category_progress=None) -> dict[str, Any]:

    if is_demo_mode():
        return _build_mock_signals(company_name)

    try:
        client = Groq(api_key=get_groq_api_key())
    except Exception as exc:
        logger.error("Failed to configure Groq client: %s", exc)
        mock = _build_mock_signals(company_name)
        mock["mode"] = "demo_fallback_config_error"
        return mock

    signals: dict[str, list] = {cat: [] for cat in SEARCH_QUERIES}
    any_success = False

    query_list = list(SEARCH_QUERIES.items())
    for idx, (category, query_template) in enumerate(query_list):
        if on_category_progress:
            on_category_progress(category, idx + 1, len(query_list))
        query = query_template.format(company=company_name)
        try:
            text = _query_groq(client, query, category)
            findings = _parse_findings(text)
            signals[category] = findings
            if findings:
                any_success = True
                logger.info("[%s] %d findings", category, len(findings))
            else:
                logger.warning("[%s] 0 findings returned", category)
        except Exception as exc:
            logger.error("[%s] Exception: %s", category, exc)
            signals[category] = []

    if not any_success:
        logger.warning("All Groq queries failed — falling back to demo data")
        mock = _build_mock_signals(company_name)
        mock["mode"] = "demo_fallback"
        return mock

    return {
        "company":       company_name,
        "timestamp":     datetime.datetime.utcnow().isoformat() + "Z",
        "signals":       signals,
        "sources_count": sum(len(v) for v in signals.values()),
        "mode":          "groq_ai",
    }
