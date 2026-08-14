# SwasthiQ EOD Billing API

Minimal deterministic backend for the SwasthiQ EOD Billing & Analytics Agent.

## What it does

- Validates billing rows independently.
- Rejects malformed rows without discarding valid rows.
- Calculates billed, collected, outstanding and refunds.
- Splits reconciliation by cash/card/UPI.
- Calculates revenue by UTC hour and peak hour.
- Ranks medicines by quantity and gross line-item revenue.
- Keeps all monetary values in integer paise.
- Returns `complete` or `partial` report status.

The deterministic engine does not call an LLM.

## Run

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

API:
- `GET /health`
- `POST /api/analyze`

Swagger:
`/docs`

## Test

```bash
pytest
```

## Business rules

For normal transactions:

`gross = sum(qty * unit_price_paise)`

`billed = gross - discount_paise`

`outstanding = billed - collected`

Refund rows contribute only to refunds and are excluded from sales analytics.

Medicine revenue is gross line-item revenue. Visit-level discounts are not allocated to individual medicines.
