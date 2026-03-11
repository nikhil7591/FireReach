# FireReach — Agent Documentation

## Architecture

```
User Input (ICP + Company + Email)
         │
         ▼
┌──────────────────────────────────────────┐
│   FIREREACH AGENT (Gemini 2.5 Flash)     │
│   Function Calling Orchestrator          │
└──────────────────────────────────────────┘
         │                │               │
         ▼                ▼               ▼
  ┌─────────────┐  ┌────────────┐  ┌───────────────┐
  │  Tool 1     │  │  Tool 2    │  │  Tool 3       │
  │  Signal     │─▶│  Research  │─▶│  Outreach     │
  │  Harvester  │  │  Analyst   │  │  Sender       │
  └─────────────┘  └────────────┘  └───────────────┘
         │                │               │
         ▼                ▼               ▼
  8 Grounded        Account Brief    Cold Email
  Search Queries    + Pain Points    Generated +
  (Google Search)   + Angle          Sent/Preview
  → Real Sources

         └────────────────────────────────┘
                Shared State (dict)
           signals ─────────────────────▶
                      brief ────────────▶
```

---

## How Grounding Works

The Signal Harvester uses **Gemini Google Search Grounding** via the `google-genai` SDK:

1. For each of the 8 signal categories, Gemini performs a live Google Search
2. `response.candidates[0].grounding_metadata.grounding_chunks` contains real URLs and titles
3. These URL-cited findings flow to the Research Analyst and Email Writer
4. The Email Writer references **specific signals** (amounts, dates, names) — making every email unique and fact-anchored

---

## Tech Stack

| Component        | Technology                                 |
|------------------|--------------------------------------------|
| Backend          | FastAPI (Python 3.12+)                     |
| Frontend         | React 18 + Vite + Tailwind CSS             |
| LLM              | Google Gemini 2.5 Flash                    |
| Grounded Search  | `google-genai` SDK + Google Search         |
| Function Calling | `google-generativeai` SDK + protos API     |
| Email (primary)  | Resend API                                 |
| Email (fallback) | Gmail SMTP                                 |
| Email (last)     | Preview-only (no credentials needed)       |
| Deployment       | Render (backend) + Vercel (frontend)       |

---

## Tool Schemas

### Tool 1: `tool_signal_harvester`

Fetches real buyer signals via Google Search Grounding across 8 categories: funding, hiring, leadership, news, tech_stack, g2_reviews, social_mentions, competitor_churn.

**Input**: `{ "company_name": "string" }`

**Output**: `{ company, timestamp, signals: { [category]: [{ finding, source_url, source_title }] }, sources_count, mode }`

### Tool 2: `tool_research_analyst`

Analyzes buyer signals against the ICP to produce a structured account brief.

**Input**: `{ "company_name": "string", "icp": "string" }`

**Output**: `{ account_brief, key_signals_identified[], pain_points[], recommended_angle, company, status }`

### Tool 3: `tool_outreach_automated_sender`

Writes a hyper-personalized cold email referencing specific signals and sends it.

**Input**: `{ "recipient_email": "string", "company_name": "string", "icp": "string" }`

**Output**: `{ company, recipient_email, email: { subject, body }, send_status: { method, success, details }, status }`

---

## SDKs

FireReach uses two Google SDKs:

| SDK | Package | Used By | Purpose |
|-----|---------|---------|---------|
| New | `google-genai` | `signal_harvester.py` | Google Search Grounding |
| Old | `google-generativeai` | `agent.py`, `research_analyst.py`, `outreach_sender.py` | Standard generation + Function Calling |

Both are listed in `requirements.txt`.

---

## Demo Mode

When `DEMO_MODE=true`, all tools return mock data. The Signal Harvester also falls back to demo data if:
- `google-genai` package is not installed
- API key is invalid or missing
- All 8 grounded search queries fail

---

## Deployment

### Backend → Render

**Blueprint**: Push to GitHub → Render → New → Blueprint → connect repo → add `GEMINI_API_KEY` in dashboard → Apply.

**Manual**: New → Web Service → Build: `cd backend && pip install -r requirements.txt` → Start: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT` → add env vars.

### Frontend → Vercel

Import repo → Framework: Vite → Root: `frontend` → add `VITE_API_URL` = Render backend URL → Deploy.

### How `VITE_API_URL` Works

```js
const API_URL = import.meta.env.VITE_API_URL || ''
```

- **Local**: Empty → requests go to `/api/*` → Vite proxy forwards to `localhost:8001`
- **Production**: Set to Render URL → requests go directly to backend
