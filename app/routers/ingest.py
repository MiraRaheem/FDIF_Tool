
# app/routers/ingest.py
"""
/fdif/ingest
------------
A single shared ingest endpoint (the "bus") for ALL sources & formats:
- Accepts a single envelope OR a batch (list of envelopes)
- Idempotency: prefer X-Idempotency-Key header; fallback to eventId
- Minimal schema check for CANONICAL domain shapes (e.g., iot)
- Stores accepted items; sends malformed to DLQ
- Returns a 'next' hint so clients know where to POST next step
"""

from typing import Optional, List, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Header
from app.models import IngestEnvelope, IngestBody, CanonicalIoT, CanonicalWorkOrder
from app.services.storage import save_doc, save_dlq, dedupe

router = APIRouter(tags=["ingest"])

MAX_BATCH = 1000  # guardrail for batch size

def _validate_canonical(envelope: IngestEnvelope):
    """
    Light canonical checks by domain. Keep this permissive; strict rules
    belong in /fdif/validate (JSON Schema / SHACL).
    """
    if envelope.source == "iot":
        CanonicalIoT(**envelope.payload)
    elif envelope.source == "work_order":
        CanonicalWorkOrder(**envelope.payload)
    # TODO: add Canonical models for work_order, bom, etc. as needed

def _route_hint(envelope: IngestEnvelope) -> str:
    """
    RAW -> harmonize, CANONICAL -> validate. This guides pipeline clients.
    """
    return "/fdif/harmonize" if envelope.format == "raw" else "/fdif/validate"

def _handle_one(env: IngestEnvelope, idem: Optional[str]) -> Dict[str, Any]:
    """
    Process a single envelope:
    - idempotency
    - (optional) canonical light-check
    - store
    - route hint
    """
    # 1) Idempotency
    idem_key = idem or env.eventId or ""
    ok, why = dedupe("ingest", idem_key)
    if not ok:
        raise HTTPException(status_code=409, detail=why)

    # 2) Canonical light-check
    if env.format == "canonical":
        try:
            _validate_canonical(env)
        except Exception as e:
            save_dlq("ingest:canonical", env.dict(), str(e))
            raise HTTPException(status_code=422, detail=f"Canonical schema error: {e}")

    # 3) Store envelope for traceability (swap for DB/queue later)
    save_doc("ingest", env.dict())

    # 4) Tell the caller what to do next
    return {
        "status": "received",
        "source": env.source,
        "format": env.format,
        "next": _route_hint(env),
        "idempotencyKey": idem_key or None
    }

@router.post("/ingest")
def ingest(body: IngestBody, x_idempotency_key: Optional[str] = Header(default=None)):
    """
    Accepts:
      - Single envelope (object), or
      - Batch of envelopes (array)
    Returns:
      - Single result object, or
      - {count, items:[per-item results]}
    """
    # FastAPI may pass dict for single object; coerce to model
    if isinstance(body, dict):
        body = IngestEnvelope(**body)

    # Single message path
    if isinstance(body, IngestEnvelope):
        return _handle_one(body, x_idempotency_key)

    # Batch path
    if isinstance(body, list):
        if len(body) > MAX_BATCH:
            raise HTTPException(status_code=413, detail=f"Batch too large (>{MAX_BATCH})")
        results: List[Dict[str, Any]] = []
        for i, item in enumerate(body):
            try:
                env = IngestEnvelope(**item)
                # Make per-item idempotency key deterministic when a single header is supplied
                idem = x_idempotency_key and f"{x_idempotency_key}:{i}"
                results.append({"index": i, "ok": True, "result": _handle_one(env, idem)})
            except HTTPException as he:
                results.append({"index": i, "ok": False, "status": he.status_code, "error": he.detail})
            except Exception as e:
                save_dlq("ingest:exception", item, str(e))
                results.append({"index": i, "ok": False, "status": 400, "error": str(e)})
        return {"count": len(results), "items": results}

    raise HTTPException(status_code=400, detail="Invalid body: expected an object or an array of objects")
