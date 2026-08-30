# PropIQ Deployment Checklist

This document outlines deployment requirements and operational procedures for deploying PropIQ.

## Environment Requirements

- **Python Version**: Python 3.11.x
- **Node Version**: Node.js v18+ (React 18 + Vite 5)
- **Operating System**: Windows / Linux / macOS compatible

## Environment Variables

### Backend (`backend/.env`)

```env
GROQ_API_KEY=your_groq_api_key_here
FRONTEND_ORIGIN=http://localhost:5173
```

### Frontend (`frontend/.env`)

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

*Note: No secret variables exist in the frontend environment or Vite bundle.*

## Backend Setup & Execution

1. Navigate to backend directory: `cd backend`
2. Install Python dependencies: `pip install -r requirements.txt`
3. Launch uvicorn web server: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
4. Verify health check endpoint: `GET http://localhost:8000/api/health`

## Frontend Setup & Execution

1. Navigate to frontend directory: `cd frontend`
2. Install Node dependencies: `npm install`
3. Run development server: `npm run dev`
4. Build static production bundle: `npm run build`

## Security & Deployment Architecture

- **Session Isolation**: Multi-tenant session state isolated by cryptographically secure 256-bit entropy UUID session tokens (`sess_{secrets.token_urlsafe(32)}`).
- **Local Vectors & FAISS**: Proposal PDF parsing, text chunking, and 384-dim sentence-transformer embedding generation execute 100% locally.
- **Privacy Model**: Excerpts sent to external LLM only when AI extraction or executive narrative reasoning is required.
- **Single-Process Limitation**: In-memory rate limiting (20 req/min) and operation locking run in-process. Production deployment behind multi-instance load balancers requires a Redis backing store.
- **Session Lifecycle**: In-memory session stores auto-prune after 60 minutes (`SESSION_TTL_MINUTES = 60`).
