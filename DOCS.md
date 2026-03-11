# FireReach — Agent Documentation

## Architecture

```
User Input (ICP + Company + Email)
         │
         ▼
┌──────────────────────────────────────────┐
│   FIREREACH PIPELINE (Groq AI)           │
│   Sequential 3-Tool Orchestrator         │
│   + SSE Real-Time Streaming              │
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
  8 AI-Powered      Account Brief    Cold Email
  Signal Queries    + Pain Points    Generated +
  (Groq LLM)       + Angle          Sent/Preview

         └────────────────────────────────┘
                Shared State (dict)
           signals ─────────────────────▶
                      brief ────────────▶
```

---

## How Signal Harvesting Works

The Signal Harvester uses **Groq AI** (Llama 3.3 70B) to generate buyer intelligence:

1. For each of the 8 signal categories, a targeted prompt is sent to Groq
2. Groq returns structured findings with specific details (amounts, dates, names)
3. These findings flow to the Research Analyst and Email Writer via shared state
4. The Email Writer references **specific signals** — making every email unique and fact-anchored
5. Real-time progress is streamed to the frontend via SSE (Server-Sent Events)

---

## Tech Stack

| Component        | Technology                                 |
|------------------|-------------------------------------------|
| Backend          | FastAPI (Python 3.12+)                     |
| Frontend         | React 18 + Vite + Tailwind CSS             |
| LLM              | Groq AI — Llama 3.3 70B Versatile          |
| SDK              | `groq` Python SDK                          |
| Streaming        | Server-Sent Events (SSE)                   |
| Email (primary)  | Resend API                                 |
| Email (fallback) | Gmail SMTP                                 |
| Email (last)     | Preview-only (no credentials needed)       |
| Deployment       | Render (backend) + Vercel (frontend)       |

---

## Tool Schemas

### Tool 1: `tool_signal_harvester`

Fetches buyer signals via Groq AI across 8 categories: funding, hiring, leadership, news, tech_stack, g2_reviews, social_mentions, competitor_churn.

**Input**: `{ "company_name": "string" }`

**Output**: `{ company, timestamp, signals: { [category]: [{ finding, source_url, source_title }] }, sources_count, mode }`

**Progress callback**: `on_category_progress(category, current, total)` — used by the SSE streaming endpoint to send real-time progress events.

### Tool 2: `tool_research_analyst`

Analyzes buyer signals against the ICP to produce a structured account brief.

**Input**: `{ "company_name": "string", "icp": "string" }`

**Output**: `{ account_brief, key_signals_identified[], pain_points[], recommended_angle, company, status }`

### Tool 3: `tool_outreach_automated_sender`

Writes a hyper-personalized cold email referencing specific signals and sends it.

**Input**: `{ "recipient_email": "string", "company_name": "string", "icp": "string" }`

**Output**: `{ company, recipient_email, email: { subject, body }, send_status: { method, success, details }, status }`

---

## SSE Streaming

The `/api/outreach/stream` endpoint uses Server-Sent Events to provide real-time progress:

| Event Type         | Description                              |
|--------------------|------------------------------------------|
| `step_start`       | A tool is starting execution             |
| `signal_category`  | Signal harvester progress (e.g. 3/8)     |
| `step_done`        | A tool completed with its result         |
| `step_error`       | A tool encountered an error              |
| `complete`         | Full pipeline result with all steps      |

The frontend tries `/api/outreach/stream` first and falls back to `/api/outreach` if SSE is unavailable.

---

## Demo Mode

When `DEMO_MODE=true`, all tools return mock data. The Signal Harvester also falls back to demo data if:
- Groq API key is invalid or missing
- All 8 signal queries fail

---

## Deployment

### Backend → Render

**Blueprint**: Push to GitHub → Render → New → Blueprint → connect repo → add `GROQ_API_KEY` in dashboard → Apply.

**Manual**: New → Web Service → Build: `cd backend && pip install -r requirements.txt` → Start: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT` → add env vars.

### Frontend → Vercel

Import repo → Framework: Vite → Root: `frontend` → add `VITE_API_URL` = Render backend URL → Deploy.

### How `VITE_API_URL` Works

```js
const API_URL = import.meta.env.VITE_API_URL || ''
```

- **Local**: Empty → requests go to `/api/*` → Vite proxy forwards to `localhost:8000`
- **Production**: Set to Render URL → requests go directly to backend
