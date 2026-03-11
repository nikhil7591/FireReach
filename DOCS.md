# FireReach — Agent Documentation

## Logic Flow

```
User Input
  │  ICP + Company + Email
  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FIREREACH AGENT (Gemini 2.0 Flash)           │
│                     Function Calling Orchestrator               │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
  ┌─────────────┐    ┌────────────────┐    ┌───────────────────┐
  │    TOOL 1   │    │    TOOL 2      │    │     TOOL 3        │
  │  Signal     │───▶│  Research      │───▶│  Outreach         │
  │  Harvester  │    │  Analyst       │    │  Sender           │
  └─────────────┘    └────────────────┘    └───────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
  5 Grounded          Account Brief +         Cold Email
  Search Queries      Pain Points +           Generated +
  (Google Search)     Angle                   Sent / Preview
  → Real Sources

         └─────────────────────────────────────────┘
                   Shared State (state dict)
              signals ──────────────────────────▶
                          brief ────────────────▶
```

## How Outreach is Grounded in Signals

The Signal Harvester uses **Gemini Google Search Grounding**, which fetches REAL Google search results with source URLs as proof of factual grounding. This works as follows:

1. A `GenerativeModel` is created with `tools="google_search_retrieval"` — this activates Gemini's native Google Search tool.
2. For each of the 5 signal categories, Gemini performs a live Google search and returns grounded text with citations.
3. The `response.candidates[0].grounding_metadata.grounding_chunks` field contains real URLs and titles from the actual search results.
4. These URL-cited findings are stored in the `signals` dict and passed directly to the Research Analyst and Email Writer.
5. The Email Writer is instructed to reference **specific signals** (amounts, dates, names, technologies) — making every email unique and fact-anchored.

**The result**: Unlike templates that guess at a company's situation, FireReach references actual facts like "your $100M Series C" or "your new CSO hire from CrowdStrike" because those facts came from real search results, not LLM hallucination.

---

## Tech Stack

| Component        | Technology                                 |
|------------------|--------------------------------------------|
| Backend          | FastAPI (Python 3.11+)                     |
| Frontend         | React 18 + Vite + Tailwind CSS             |
| LLM              | Google Gemini 2.0 Flash                    |
| Grounded Search  | Gemini Google Search Retrieval             |
| Function Calling | Gemini FunctionDeclaration + protos API    |
| Email (primary)  | Resend API                                 |
| Email (fallback) | Gmail SMTP (smtplib)                       |
| Email (last)     | Preview-only (no credentials needed)       |
| Deployment       | Render (backend) + Vercel (frontend)       |

---

## Tool Schemas

### Tool 1: `tool_signal_harvester`

**Description**: Fetches REAL buyer signals for a target company via Google Search Grounding.

**Parameters**:
```json
{
  "company_name": {
    "type": "string",
    "required": true,
    "description": "Name of the target company to research"
  }
}
```

**Returns**:
```json
{
  "company": "string",
  "timestamp": "ISO 8601 datetime",
  "signals": {
    "funding":    [{"finding": "string", "source_url": "string", "source_title": "string"}],
    "hiring":     [{"finding": "string", "source_url": "string", "source_title": "string"}],
    "leadership": [{"finding": "string", "source_url": "string", "source_title": "string"}],
    "news":       [{"finding": "string", "source_url": "string", "source_title": "string"}],
    "tech_stack": [{"finding": "string", "source_url": "string", "source_title": "string"}]
  },
  "sources_count": "integer",
  "mode": "grounded_search | demo | demo_fallback"
}
```

---

### Tool 2: `tool_research_analyst`

**Description**: Analyzes buyer signals against the ICP to produce a structured Account Brief.

**Parameters**:
```json
{
  "company_name": {"type": "string", "required": true},
  "icp":          {"type": "string", "required": true, "description": "Seller's Ideal Customer Profile"}
}
```

**Returns**:
```json
{
  "account_brief": "Two-paragraph string with pain points and ICP alignment",
  "key_signals_identified": ["string", "..."],
  "pain_points": ["string", "..."],
  "recommended_angle": "One-sentence outreach angle",
  "company": "string",
  "status": "success | fallback"
}
```

---

### Tool 3: `tool_outreach_automated_sender`

**Description**: Writes a hyper-personalized cold email referencing specific signals and sends it.

**Parameters**:
```json
{
  "recipient_email": {"type": "string", "required": true},
  "company_name":    {"type": "string", "required": true},
  "icp":             {"type": "string", "required": true}
}
```

**Returns**:
```json
{
  "company": "string",
  "recipient_email": "string",
  "email": {
    "subject": "string — references a specific signal",
    "body": "string — plain text under 150 words, signed by Alex from Rabbitt AI"
  },
  "send_status": {
    "method": "resend | smtp_gmail | preview_only",
    "success": true,
    "details": "string"
  },
  "account_brief_used": "string",
  "recommended_angle": "string",
  "status": "success"
}
```

---

## System Prompt

```
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
```

---

## Deterministic Signal Harvesting

The **Signal Harvester** tool is deterministic because it uses **Gemini Google Search Grounding**:

- Gemini's grounding tool makes actual HTTP requests to Google Search.
- Results include `grounding_metadata.grounding_chunks` — real URLs from actual websites.
- The agent never invents funding amounts, leadership names, or technology choices.
- Every finding is traceable back to a real public source URL.
- In DEMO_MODE, realistic mock data is substituted — but this is clearly labelled in the UI and response.

This architecture means FireReach's outreach is *factually anchored* — it can truthfully say "I saw your $200M funding round in Crunchbase" because the data came from Crunchbase, not from Gemini's training weights.

---

## Important: google-genai vs google-generativeai

FireReach uses **two** Google SDKs:

| SDK | Package | Used By | Purpose |
|-----|---------|---------|---------|
| **New SDK** | `google-genai` | `signal_harvester.py` | Google Search Grounding (real signals) |
| **Old SDK** | `google-generativeai` | `agent.py`, `research_analyst.py`, `outreach_sender.py` | Standard generation + Function Calling |

> ⚠️ The `google-generativeai` package is deprecated. The Signal Harvester uses the new `google-genai` SDK because grounding **silently fails** in the old SDK. Both are listed in `requirements.txt`.

---

## DEMO_MODE

When `DEMO_MODE=true` in the `.env` file (or as an environment variable), **all tools return mock/demo data** instead of making real API calls. This is useful for testing the UI without burning API credits.

Set `DEMO_MODE=false` for real agent generation with live Gemini grounded search.

The Signal Harvester also falls back to demo data if:
- The `google-genai` package is not installed
- The Gemini API key is invalid or missing
- All 8 grounded search queries fail

---

## Deployment Guide

### Backend → Render

#### Prerequisites
- Code pushed to a GitHub repository
- A [Render](https://render.com) account (free tier works)
- Your `GEMINI_API_KEY` ready

#### Steps

**Option A — Blueprint (render.yaml)**:
1. Go to [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**
2. Connect your GitHub repo containing the `render.yaml` file
3. Render auto-detects `render.yaml` and creates the service
4. Add secret environment variables in the dashboard:
   - `GEMINI_API_KEY` = your Google Gemini API key
   - `RESEND_API_KEY` = your Resend API key *(optional, for email sending)*
   - `SMTP_USER` = your Gmail address *(optional)*
   - `SMTP_PASS` = your Gmail app password *(optional)*
5. Click **Apply** — deployment starts

**Option B — Manual**:
1. Go to Render → **New** → **Web Service**
2. Connect your GitHub repo
3. Set:
   - **Name**: `firereach-api`
   - **Runtime**: Python
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables (same as Option A)
5. **Create Web Service**

**Verify**: `https://firereach-api.onrender.com/api/health` → `{"status": "healthy"}`

#### render.yaml Reference

```yaml
services:
  - type: web
    name: firereach-api
    runtime: python
    region: oregon
    plan: free
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /api/health
    envVars:
      - key: GEMINI_API_KEY
        sync: false          # set manually in dashboard
      - key: DEMO_MODE
        value: "false"
```

---

### Frontend → Vercel

#### Prerequisites
- Code pushed to a GitHub repository
- A [Vercel](https://vercel.com) account (free tier works)
- Your Render backend URL (e.g., `https://firereach-api.onrender.com`)

#### Steps

1. Go to [Vercel Dashboard](https://vercel.com/dashboard) → **Add New** → **Project**
2. Import your GitHub repo
3. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend` *(click Edit to change)*
   - **Build Command**: `npm run build` *(auto-detected)*
   - **Output Directory**: `dist` *(auto-detected)*
4. Add environment variable:
   - **Key**: `VITE_API_URL`
   - **Value**: `https://firereach-api.onrender.com` *(your Render backend URL)*
5. Click **Deploy**

**Verify**: Open your Vercel URL → the FireReach dashboard should load and connect to the backend.

#### How VITE_API_URL Works

In the frontend code (`App.jsx`):
```js
const API_URL = import.meta.env.VITE_API_URL || ''
```

- **Local dev**: `VITE_API_URL` is empty → requests go to `/api/*` → Vite proxy forwards to `localhost:8000`
- **Production (Vercel)**: `VITE_API_URL` = Render URL → requests go directly to `https://firereach-api.onrender.com/api/*`

---

### Post-Deployment Verification

1. **Backend health**: `GET https://firereach-api.onrender.com/api/health`
2. **Frontend loads**: Open your Vercel URL
3. **Full pipeline test**: Submit outreach request from the UI → verify all 3 tools run with `mode: "grounded_search"` (not `demo`)
4. **CORS**: The backend allows all origins (`*`) so cross-origin requests from Vercel to Render work out of the box
