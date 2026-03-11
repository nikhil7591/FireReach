# FireReach — Autonomous Outreach Engine

AI agent that harvests real buyer signals from Google Search, analyzes them against your ICP, and writes + sends a hyper-personalized cold email — all in one click.

Built for the **Rabbitt AI** ecosystem, powered by **Google Gemini 2.5 Flash**.

---

## Features

- **Real Buyer Signals** — Gemini Google Search Grounding fetches live data across 8 categories (funding, hiring, leadership, news, tech stack, G2 reviews, social mentions, competitor churn) with source URLs
- **Autonomous Agent** — Gemini Function Calling orchestrates 3 tools sequentially
- **Hyper-Personalized Emails** — Unique emails referencing specific, real signals
- **Multi-Method Sending** — Resend API → Gmail SMTP → Preview-only fallback
- **Demo Mode** — Realistic mock data when `DEMO_MODE=true` or API fails
- **Dark UI** — React + Tailwind dashboard with live pipeline visualization

---

## Tech Stack

| Layer      | Technology                                |
|------------|-------------------------------------------|
| Backend    | FastAPI (Python 3.12+)                    |
| Frontend   | React 18 + Vite + Tailwind CSS           |
| LLM        | Google Gemini 2.5 Flash                   |
| Search     | Gemini Google Search Grounding (`google-genai` SDK) |
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
#   GEMINI_API_KEY=your-key
#   DEMO_MODE=false

cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

Backend: `http://localhost:8001` | Swagger: `http://localhost:8001/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

> Vite proxy forwards `/api` requests to `http://localhost:8001`.

---

## Environment Variables

| Variable         | Required | Description                               |
|------------------|----------|-------------------------------------------|
| `GEMINI_API_KEY` | Yes      | Google Gemini API key                     |
| `RESEND_API_KEY` | Optional | Resend API key for email sending          |
| `SENDER_EMAIL`   | Optional | From-address (default: `onboarding@resend.dev`) |
| `SMTP_USER`      | Optional | Gmail address for SMTP fallback           |
| `SMTP_PASS`      | Optional | Gmail app password                        |
| `DEMO_MODE`      | Optional | `true` = mock data (default: `false`)     |

---

## API

### `POST /api/outreach`

```json
{
  "icp": "We sell cybersecurity training to Series B startups.",
  "company": "Wiz",
  "recipient_email": "ciso@example.com"
}
```

Returns `{ status, mode, steps[], summary, total_steps }`.

### `GET /api/health`

Returns `{ status: "healthy", service: "FireReach", version: "1.0.0" }`.

---

## Deployment

### Backend → Render

**Blueprint**: Push to GitHub → Render → New → Blueprint → connect repo → add `GEMINI_API_KEY` env var → Apply.

**Manual**: New → Web Service → Build: `cd backend && pip install -r requirements.txt` → Start: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT` → add env vars → Create.

### Frontend → Vercel

Import repo → Framework: Vite → Root Directory: `frontend` → add `VITE_API_URL` = Render backend URL → Deploy.

---

## Project Structure

```
firereach/
├── backend/
│   ├── main.py              # FastAPI endpoints
│   ├── config.py            # Env var loader
│   ├── agent.py             # Gemini Function Calling orchestrator
│   ├── tools/
│   │   ├── signal_harvester.py  # Tool 1: Google Search Grounding (8 categories)
│   │   ├── research_analyst.py  # Tool 2: Account brief generator
│   │   └── outreach_sender.py   # Tool 3: Email writer + sender
│   └── requirements.txt
├── frontend/
│   └── src/
│       └── App.jsx          # Dashboard UI
├── render.yaml
├── DOCS.md
└── README.md
```

---

Built with ❤️ by **Rabbitt AI** × **Google Gemini**
