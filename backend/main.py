from typing import Any
from fastapi import FastAPI, HTTPException,Body
from fastapi.middleware.cors import CORSMiddleware
from billing_engine import build_eod_report
from narrative import generate_narrative

app = FastAPI(title="SwasthiQ EOD Billing API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (good for local development)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/analyze")
def analyze(payload: list= Body(...)):
    if not isinstance(payload, list):
        raise HTTPException(
            status_code=400,
            detail="Request body must be a JSON array of billing records.",
        )

    return build_eod_report(payload)

@app.post("/api/narrative")
def narrative(report: dict):
    try:
        return generate_narrative(report)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Unable to generate a grounded narrative.",
        )
