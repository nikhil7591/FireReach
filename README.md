# FireReach — Autonomous Outreach Engine

AI agent that harvests buyer signals, analyzes them against your ICP, and writes + sends a hyper-personalized cold email — all in one click.

Built for the **Rabbitt AI** ecosystem, powered by **Groq AI** (Llama 3.3 70B).

---

## Features

- **AI Buyer Signals** — Groq-powered intelligence across 8 categories (funding, hiring, leadership, news, tech stack, G2 reviews, social mentions, competitor churn)
- **3-Step Pipeline** — Signal Harvester → Research Analyst → Email Generator, executed sequentially with real-time SSE streaming
- **Live Progress Bar** — Real-time per-category progress via Server-Sent Events
- **Hyper-Personalized Emails** — Unique emails referencing specific, real signals
- **Multi-Method Sending** — Resend API → Gmail SMTP → Preview-only fallback
- **Demo Mode** — Realistic mock data when `DEMO_MODE=true` or API fails
- **Dark UI** — React + Tailwind dashboard with live pipeline visualization

---

## Tech Stack

| Layer      | Technology                                |
|------------|-------------------------------------------|
| Backend    | FastAPI (Python 3.12+)                    |
| Frontend   | React 18 + Vite + Tailwind CSS            |
| LLM        | Groq AI — Llama 3.3 70B Versatile         |
| Streaming  | Server-Sent Events (SSE)                  |
| Email      | Resend API / Gmail SMTP / Preview         |
| Deploy     | Render (backend) + Vercel (frontend)      |

---

## Local Development

### Backend

```bash
cd firereach
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate

pip install -r backend/requirements.txt

# Create backend/.env:
#   GROQ_API_KEY=your-groq-key
#   GROQ_MODEL=llama-3.3-70b-versatile
#   DEMO_MODE=false

cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend: `http://localhost:8000` | Swagger: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

> Vite proxy forwards `/api` requests to `http://localhost:8000`.

---

## Environment Variables

| Variable         | Required | Description                               |
|------------------|----------|-------------------------------------------|
| `GROQ_API_KEY`   | Yes      | Groq API key (get from console.groq.com)  |
| `GROQ_MODEL`     | Optional | Model name (default: `llama-3.3-70b-versatile`) |
| `RESEND_API_KEY` | Optional | Resend API key for email sending          |
| `SENDER_EMAIL`   | Optional | From-address (default: `onboarding@resend.dev`) |
| `SMTP_USER`      | Optional | Gmail address for SMTP fallback           |
| `SMTP_PASS`      | Optional | Gmail app password                        |
| `DEMO_MODE`      | Optional | `true` = mock data (default: `false`)     |

---

## API

### `POST /api/outreach`

Standard request — runs all 3 tools and returns the full result.

```json
{
  "icp": "We sell cybersecurity training to Series B startups.",
  "company": "Wiz",
  "recipient_email": "ciso@example.com"
}
```

Returns `{ status, mode, steps[], summary, total_steps }`.

### `POST /api/outreach/stream`

SSE streaming endpoint — same payload as above, but returns real-time progress events:

- `step_start` — tool is beginning execution
- `signal_category` — per-category progress (1/8, 2/8, etc.)
- `step_done` — tool finished with result
- `step_error` — tool encountered an error
- `complete` — full pipeline result

### `GET /api/health`

Returns `{ status: "healthy", service: "FireReach", version: "1.0.0" }`.

---

## Deployment

### Backend → Render

**Blueprint**: Push to GitHub → Render → New → Blueprint → connect repo → add `GROQ_API_KEY` env var → Apply.

**Manual**: New → Web Service → Build: `cd backend && pip install -r requirements.txt` → Start: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT` → add env vars → Create.

### Frontend → Vercel

Import repo → Framework: Vite → Root Directory: `frontend` → add `VITE_API_URL` = Render backend URL → Deploy.

---

## Project Structure

```
firereach/
├── backend/
│   ├── main.py              # FastAPI endpoints + SSE streaming
│   ├── config.py            # Env var loader (Groq keys)
│   ├── agent.py             # Sequential 3-tool pipeline orchestrator
│   ├── tools/
│   │   ├── signal_harvester.py  # Tool 1: Groq AI signal intelligence (8 categories)
│   │   ├── research_analyst.py  # Tool 2: Account brief generator
│   │   └── outreach_sender.py   # Tool 3: Email writer + sender
│   └── requirements.txt
├── frontend/
│   └── src/
│       └── App.jsx          # Dashboard UI with progress bar
├── render.yaml
├── DOCS.md
└── README.md
```

---

Built with ❤️ by **Rabbitt AI** × **Groq AI**
