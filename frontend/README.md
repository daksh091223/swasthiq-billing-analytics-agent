# SwasthiQ EOD Billing Frontend

React + Vite frontend for the deterministic billing API.

## Run

```bash
npm install
npm run dev
```

The frontend expects the backend at:

`http://localhost:8000`

To change it:

```bash
VITE_API_URL=http://localhost:8000
```

## Flow

Billing JSON
→ POST `/api/analyze`
→ deterministic EOD report
→ reconciliation / analytics UI

The AI Narrative screen is intentionally a placeholder for the next LLM pipeline. Its traced figures are currently sourced directly from the deterministic report.
