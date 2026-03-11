# 🔥 FireReach — Autonomous Outreach Engine

> AI agent that harvests real buyer signals from Google Search, analyzes them against your ICP, and writes + sends a hyper-personalized cold email — all in one click.

Built for the **Rabbitt AI** ecosystem, powered by **Google Gemini 2.0 Flash**.

---

## Features

- 🌐 **Real Buyer Signals** — Uses Gemini Google Search Grounding to fetch live data (funding, hiring, leadership, news, tech stack, G2 reviews, social mentions, competitor churn) with source URLs as proof
- 🤖 **Autonomous Agent** — Gemini Function Calling orchestrates 3 tools sequentially with no manual steps
- 📧 **Hyper-Personalized Emails** — Gemini writes unique emails that reference specific, real signals (not templates)
- 📤 **Multi-Method Sending** — Resend API → Gmail SMTP → Preview-only fallback
- 🎭 **Demo Mode** — Realistic mock data when `DEMO_MODE=true` or API fails
- 🌑 **Premium Dark UI** — React + Tailwind dashboard with live pipeline visualization

---

## Tech Stack

| Layer      | Technology                                |
|------------|-------------------------------------------|
| Backend    | FastAPI (Python 3.12+)                    |
| Frontend   | React 18 + Vite + Tailwind CSS           |
| LLM        | Google Gemini 2.0 Flash                   |
| Search     | Gemini Google Search Grounding (new SDK)  |
| Email      | Resend API / Gmail SMTP / Preview         |
| Deploy     | Render (backend) + Vercel (frontend)      |

---

## Prerequisites

- Python 3.12+
- Node.js 18+
- [Google Gemini API Key](https://aistudio.google.com) (required)
- [Resend API Key](https://resend.com) (optional — enables email sending)
- Gmail App Password (optional — alternative to Resend)

---

## Local Development

### Backend

```bash
# 1. Navigate to project root
cd firereach

# 2. Create and activate virtual environment
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Set up environment variables
cp backend/.env.example backend/.env
# Edit backend/.env and add your GEMINI_API_KEY (required)
# Optionally add RESEND_API_KEY or SMTP_USER/SMTP_PASS for email sending
# Make sure DEMO_MODE=false for real agent generation

# 5. Run the backend server
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs (Swagger UI): `http://localhost:8000/docs`

### Frontend

```bash
# From the project root
cd frontend

# 1. Install dependencies
npm install

# 2. Run development server
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

> ⚠️ **Important**: Set `DEMO_MODE=false` to use real Gemini agent generation. When `true`, all tools return mock demo data.

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

## 🚀 Deployment

### Backend → Render (Free Tier)

#### Option A: Using render.yaml (Recommended)

1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**
3. Connect your GitHub repo
4. Render will auto-detect the `render.yaml` and configure everything
5. Add the following **environment variables** in Render dashboard:
   - `GEMINI_API_KEY` = your Gemini API key
   - `RESEND_API_KEY` = your Resend key *(optional)*
   - `SMTP_USER` = your Gmail address *(optional)*
   - `SMTP_PASS` = your Gmail app password *(optional)*
6. Click **Apply** → Deploy starts automatically

#### Option B: Manual Setup

1. Go to [Render Dashboard](https://dashboard.render.com) → **New** → **Web Service**
2. Connect your GitHub repo
3. Configure:
   - **Name**: `firereach-api`
   - **Region**: Oregon (US West)
   - **Runtime**: Python
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
4. Go to **Environment** tab and add:
   - `GEMINI_API_KEY` = your Gemini API key
   - `DEMO_MODE` = `false`
   - `RESEND_API_KEY` = your Resend key *(optional)*
   - `SMTP_USER` = your Gmail address *(optional)*
   - `SMTP_PASS` = your Gmail app password *(optional)*
5. Click **Create Web Service**

After deploy, your backend URL will be: `https://firereach-api.onrender.com`

> 💡 **Tip**: Test with `https://firereach-api.onrender.com/api/health` — should return `{"status": "healthy"}`.

> ⚠️ Render free tier sleeps after 15 min of inactivity. First request after sleep takes ~30s.

---

### Frontend → Vercel (Free Tier)

1. Go to [Vercel Dashboard](https://vercel.com/dashboard) → **Add New** → **Project**
2. Import your GitHub repo
3. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`  *(click "Edit" next to Root Directory)*
   - **Build Command**: `npm run build` *(auto-detected)*
   - **Output Directory**: `dist` *(auto-detected)*
4. Go to **Environment Variables** and add:
   - `VITE_API_URL` = `https://firereach-api.onrender.com` *(your Render backend URL)*
5. Click **Deploy**

After deploy, your frontend URL will be: `https://your-project.vercel.app`

> 💡 **Tip**: The `VITE_API_URL` env var tells the frontend where to send API requests. In local dev this is handled by Vite proxy, but in production you must point to your Render backend URL.

---

### Post-Deployment Checklist

- [ ] Backend health check works: `https://firereach-api.onrender.com/api/health`
- [ ] Frontend loads at your Vercel URL
- [ ] `VITE_API_URL` on Vercel points to your Render backend
- [ ] `GEMINI_API_KEY` is set on Render
- [ ] `DEMO_MODE` is set to `false` on Render
- [ ] Test a full outreach run from the frontend

---

## The Rabbitt Challenge — Test Case

Use this exact input to verify the full pipeline works:

```
ICP:    "We sell high-end cybersecurity training to Series B startups."
Company: "Wiz"
Email:   "test@example.com"
```

**Expected behavior:**
1. ✅ Signal Harvester fetches live Google Search results about Wiz (funding, hiring, leadership, news, tech stack, G2 reviews, social mentions, competitor churn)
2. ✅ Research Analyst creates an account brief identifying cybersecurity team growth signals
3. ✅ Outreach Sender writes an email referencing Wiz's specific signals (e.g., their latest funding round or new security leadership)
4. ✅ Email is sent via Resend, SMTP, or shown as preview

---

## Project Structure

```
firereach/
├── backend/
│   ├── main.py                  # FastAPI app + endpoints
│   ├── config.py                # Env var loader (.env)
│   ├── agent.py                 # Gemini Function Calling orchestrator
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── signal_harvester.py  # Tool 1: Grounded Google Search (8 categories)
│   │   ├── research_analyst.py  # Tool 2: Account brief AI generator
│   │   └── outreach_sender.py   # Tool 3: Email writer + multi-method sender
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                     # Your local env vars (gitignored)
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js           # Dev proxy + build config
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       ├── main.jsx
│       ├── index.css
│       └── App.jsx              # Full dashboard UI
├── render.yaml                  # Render Infrastructure-as-Code
├── DOCS.md                      # Detailed agent documentation
└── README.md                    # This file
```

---

## License

Built with ❤️ by **Rabbitt AI** × **Google Gemini**
