# 🔥 FireReach — Autonomous Outreach Engine

> AI agent that harvests real buyer signals from Google Search, analyzes them against your ICP, and writes + sends a hyper-personalized cold email — all in one click.

Built for the **Rabbitt AI** ecosystem, powered by **Google Gemini 2.0 Flash**.

---

## Features

- 🌐 **Real Buyer Signals** — Uses Gemini Google Search Grounding to fetch live data (funding, hiring, leadership, news, tech stack) with source URLs as proof
- 🤖 **Autonomous Agent** — Gemini Function Calling orchestrates 3 tools sequentially with no manual steps
- 📧 **Hyper-Personalized Emails** — Gemini writes unique emails that reference specific, real signals (not templates)
- 📤 **Multi-Method Sending** — Resend API → Gmail SMTP → Preview-only fallback
- 🎭 **Demo Mode** — Realistic mock data when `DEMO_MODE=true` or API fails
- 🌑 **Premium Dark UI** — React + Tailwind dashboard with live pipeline visualization

---

## Tech Stack

| Layer      | Technology                                |
|------------|-------------------------------------------|
| Backend    | FastAPI (Python 3.11+)                    |
| Frontend   | React 18 + Vite + Tailwind CSS           |
| LLM        | Google Gemini 2.0 Flash                   |
| Search     | Gemini Google Search Retrieval (grounded) |
| Email      | Resend API / Gmail SMTP / Preview         |
| Deploy     | Render (backend) + Vercel (frontend)      |

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- [Google Gemini API Key](https://aistudio.google.com) (required)
- [Resend API Key](https://resend.com) (optional — enables email sending)
- Gmail App Password (optional — alternative to Resend)

---

## Setup — Backend

```bash
# 1. Navigate to backend directory
cd firereach/backend

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY (required)
# Optionally add RESEND_API_KEY for email sending

# 5. Run the backend server
uvicorn main:app --reload --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs (Swagger UI): `http://localhost:8000/docs`

---

## Setup — Frontend

```bash
# From the project root
cd firereach/frontend

# 1. Install dependencies
npm install

# 2. (Optional) Set backend URL for production
# Create .env.local and add:
# VITE_API_URL=https://your-render-backend.onrender.com

# 3. Run development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

> In development, the Vite proxy automatically forwards `/api` requests to `http://localhost:8000`.

---

## Environment Variables

| Variable         | Required | Description                               |
|------------------|----------|-------------------------------------------|
| `GEMINI_API_KEY` | ✅ Yes   | Google Gemini API key                     |
| `RESEND_API_KEY` | Optional | Resend API key for email sending          |
| `SENDER_EMAIL`   | Optional | From-address (default: `onboarding@resend.dev`) |
| `SMTP_USER`      | Optional | Gmail address for SMTP fallback           |
| `SMTP_PASS`      | Optional | Gmail app password                        |
| `DEMO_MODE`      | Optional | `true` = use mock data (default: `false`) |

---

## API Documentation

### `POST /api/outreach`

Run the full autonomous outreach sequence.

**Request Body:**
```json
{
  "icp": "We sell high-end cybersecurity training to Series B startups.",
  "company": "Wiz",
  "recipient_email": "ciso@example.com"
}
```

**Response:**
```json
{
  "status": "completed",
  "mode": "function_calling",
  "steps": [
    {
      "step": 1,
      "tool": "tool_signal_harvester",
      "args": {"company_name": "Wiz"},
      "result": { "signals": {...}, "mode": "grounded_search" },
      "status": "completed"
    },
    {
      "step": 2,
      "tool": "tool_research_analyst",
      "result": { "account_brief": "...", "recommended_angle": "..." },
      "status": "completed"
    },
    {
      "step": 3,
      "tool": "tool_outreach_automated_sender",
      "result": {
        "email": { "subject": "...", "body": "..." },
        "send_status": { "method": "preview_only", "success": true }
      },
      "status": "completed"
    }
  ],
  "summary": "FireReach completed outreach for Wiz...",
  "total_steps": 3
}
```

### `GET /api/health`

```json
{
  "status": "healthy",
  "service": "FireReach",
  "version": "1.0.0"
}
```

---

## Deployment

### Backend → Render

1. Push your code to GitHub
2. Go to [Render](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set:
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables: `GEMINI_API_KEY`, `RESEND_API_KEY`
6. The included `render.yaml` can also be used for Infrastructure-as-Code deployment

### Frontend → Vercel

1. Go to [Vercel](https://vercel.com) → New Project
2. Import your GitHub repo
3. Set **Root Directory** to `firereach/frontend`
4. Add environment variable:
   - `VITE_API_URL` = your Render backend URL (e.g., `https://firereach-api.onrender.com`)
5. Deploy

---

## The Rabbitt Challenge — Test Case

Use this exact input to verify the full pipeline works:

```
ICP:    "We sell high-end cybersecurity training to Series B startups."
Company: "Wiz"
Email:   "test@example.com"
```

**Expected behavior:**
1. ✅ Signal Harvester fetches live Google Search results about Wiz (funding, hiring, leadership, news, tech stack)
2. ✅ Research Analyst creates an account brief identifying cybersecurity team growth signals
3. ✅ Outreach Sender writes an email referencing Wiz's specific signals (e.g., their latest funding round or new security leadership)
4. ✅ Email is sent via Resend, SMTP, or shown as preview

---

## Project Structure

```
firereach/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── config.py                # Env var loader
│   ├── agent.py                 # Gemini Function Calling orchestrator
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── signal_harvester.py  # Tool 1: Grounded search
│   │   ├── research_analyst.py  # Tool 2: Account brief AI
│   │   └── outreach_sender.py   # Tool 3: Email writer + sender
│   ├── requirements.txt
│   ├── .env.example
│   └── render.yaml
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       ├── main.jsx
│       ├── index.css
│       └── App.jsx               # Full dashboard
├── DOCS.md
└── README.md
```

---

## License

Built with ❤️ by **Rabbitt AI** × **Google Gemini**
