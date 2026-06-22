# FinPilot

FinPilot is an AI-powered personal finance platform built to help users understand, monitor, and improve their financial health from one dashboard. It combines a React frontend with a FastAPI backend to turn uploaded financial statements into insights such as spending analytics, budget tracking, savings planning, fraud alerts, subscription audits, and AI-assisted recommendations.

The project is designed as a financial copilot experience. Users can upload bank, credit card, or UPI statement CSV files, review categorized transactions, track monthly income and expenses, monitor a wellness score, generate reports, and interact with an AI copilot for guided financial actions. On the backend, FinPilot uses a multi-agent workflow with LangGraph and Groq-ready integrations, while still supporting mock behavior when no live API key is configured.

## Core Features

- Upload and process financial statement CSV files
- Track income, expenses, savings rate, and monthly trends
- Monitor subscriptions and recurring payments
- Detect suspicious or unusual transactions
- View a financial wellness score and history
- Create budgets and savings goals
- Generate reports and financial summaries
- Chat with an AI copilot for financial guidance

## Tech Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, React Query, Recharts
- Backend: FastAPI, SQLAlchemy, SQLite, LangChain, LangGraph
- AI: Groq-ready LLM integration with mock fallback support

## Project Structure

- `frontend/`: React application and dashboard UI
- `backend/`: FastAPI services, business logic, agent workflow, and data layer

## Run Locally

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend is configured to call the backend at `http://localhost:8000/api/v1`.

## Notes

- Keep secrets such as `GROQ_API_KEY` out of git and store them only in a local `.env` file.
- Generated folders such as `venv/`, `node_modules/`, build output, and runtime database files should remain untracked.
