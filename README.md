
# SwasthiQ EOD Billing & Analytics

Minimal full-stack implementation:

- `backend/` — deterministic reconciliation, analytics, REST API, grounded LLM narrative.
- `frontend/` — React dashboard.

## Architecture

Billing JSON
→ deterministic engine
→ EOD report
→ optional LLM narrative
→ schema validation
→ figure-token validation
→ server-side figure rendering
→ traced figures in UI

The LLM never receives raw billing records. It receives only the deterministic report.

The model is required to use figure tokens such as `{total_billed}` instead of writing numeric values. The backend validates those tokens, rejects untraced numeric literals, and replaces the tokens with values taken directly from the deterministic report.

## Run

Backend:

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

Set `OPENAI_API_KEY` in `.env`.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Default backend URL:

`http://localhost:8000`

Override with `VITE_API_URL`.

## API

- `GET /health`
- `POST /api/analyze`
- `POST /api/narrative`
