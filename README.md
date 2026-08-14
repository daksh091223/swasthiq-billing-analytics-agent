# SwasthiQ EOD Billing & Analytics Agent

A minimal full-stack implementation of the SwasthiQ SDE Intern take-home assignment.

- `backend/` — Python REST API, deterministic reconciliation/analytics engine, grounded LLM narrative, tests.
- `frontend/` — React dashboard matching the three required screens.

## Architecture

```text
Billing JSON
    ↓
Row validation + business rules
    ↓
Deterministic billing engine
    ↓
EOD reconciliation + analytics report
    ↓
Optional LLM narrative
    ↓
Structured response validation
    ↓
Figure-token validation
    ↓
Server-side figure rendering
    ↓
Traced figures in React UI
```

The LLM never receives raw billing records. It receives only the deterministic report. The deterministic layer never calls the LLM.

## Deterministic rules

For a normal transaction:

```text
gross = Σ(qty × unit_price_paise)
billed = gross - discount_paise
outstanding = billed - amount_paid_paise
```

- All monetary values remain integer paise.
- Reconciliation is split by cash, card, and UPI.
- Refunds are tracked separately and are excluded from sales analytics.
- Revenue by hour uses the UTC timestamp hour.
- Medicine rankings are kept separate: quantity and gross line-item revenue.
- Visit IDs must be unique within a billing log.
- All rows in one billing log must belong to the same clinic.
- Invalid rows are rejected individually with an actionable error while valid rows continue to be processed.
- Visit-level discounts are not allocated to individual medicines.

## Grounded narrative design

The model must use figure tokens such as `{total_billed}` rather than writing numeric values directly. The backend validates every token, rejects untraced numeric literals, and replaces tokens with values taken directly from the deterministic report.

Medicine figures are also grounded through `{top_medicine_quantity}` and `{top_medicine_revenue}`. The UI displays the source field for every traced figure used by the narrative.

If the model returns an empty, unparseable, off-schema, or otherwise invalid narrative, the API returns an error instead of silently presenting untrusted output.

## API contracts

### `GET /health`

Returns:

```json
{"status": "ok"}
```

### `POST /api/analyze`

Request body: a JSON array of billing records.

```json
[
  {
    "clinic_id": "C1",
    "visit_id": "V1",
    "timestamp": "2026-07-27T13:20:00Z",
    "doctor_id": "D1",
    "line_items": [
      {"drug_name": "PARACETAMOL", "qty": 2, "unit_price_paise": 1000}
    ],
    "payment_mode": "upi",
    "amount_paid_paise": 2000,
    "discount_paise": 0,
    "is_refund": false
  }
]
```

The response contains `status`, processed/rejected rows, payment-mode reconciliation, totals, revenue by hour, peak hour, and the two medicine rankings.

### `POST /api/narrative`

Request body: the deterministic report returned by `/api/analyze`.

The response contains the generated title/sections, traced figures, and the model identifier. Raw billing rows are never passed to the LLM.

## Run locally

### Backend

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

Set these values in `backend/.env`:

```text
HF_TOKEN=your_huggingface_token
OPENAI_MODEL=openai/gpt-oss-120b:groq
```

Backend: `http://localhost:8000`

Swagger UI: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` if the backend is not running at the default URL used by the frontend.

## Tests

```bash
cd backend
pytest
```

Tests cover reconciliation, discounts, refunds, payment modes, malformed rows, invalid timestamps, business-rule violations, empty input, hourly analytics, medicine rankings, reconciliation invariants, duplicate visit IDs, mixed clinic IDs, and narrative grounding/traceability.

## Deployment

The frontend is deployed on Vercel. The repository is structured as a single submission repository with the required `/backend`, `/frontend`, and root `README.md` components.
