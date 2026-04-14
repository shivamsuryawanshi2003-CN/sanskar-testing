# JOBRA AI - Resume Intelligence Platform

AI-powered resume analysis and optimization tool built with Next.js and FastAPI.

## Project Structure

```
├── new-frontend/    # Next.js 15 + React 19 + Tailwind CSS 4
└── new-backend/     # FastAPI + OpenAI (Python)
```

## Getting Started

### Frontend

```bash
cd new-frontend
npm install
npm run dev
```

Opens at `http://localhost:3000`

### Backend

```bash
cd new-backend
pip install -r requirements.txt
```

Create `.env` in `new-backend/`:
```
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-5-nano
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Start the server:
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

API runs at `http://localhost:8000`

## Branch Strategy

- `main` - stable release
- `dev` - development branch
- `feature/*` - individual feature branches (created from `dev`)

## Tech Stack

- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS 4
- **Backend**: FastAPI, Python, OpenAI API, Pydantic
- **Theme**: Warm Copper + Black (custom HSL variables)
