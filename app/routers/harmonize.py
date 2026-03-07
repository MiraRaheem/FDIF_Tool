# app/routers/harmonize.py
"""
/fdif/harmonize
---------------
Transforms RAW envelopes into CANONICAL envelopes
using domain-specific harmonizers.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.models import IngestEnvelope
from app.services.harmonizer import (
    harmonize_raw_iot,
    harmonize_raw_work_order
)
from app.services.storage import save_doc, save_dlq

router = APIRouter(tags=["harmonize"])


@router.post("/harmonize")
def harmonize(envelope: IngestEnvelope):
    # 1) Guardrails
    if envelope.format != "raw":
        raise HTTPException(
            status_code=400,
            detail="Only RAW messages can be harmonized"
        )

    try:
        # 2) Dispatch by source
        if envelope.source == "iot":
            canonical_payload = harmonize_raw_iot(envelope.payload)

        elif envelope.source == "work_order":
            canonical_payload = harmonize_raw_work_order(envelope.payload)

        else:
            raise ValueError(f"No harmonizer for source '{envelope.source}'")

        # 3) Build CANONICAL envelope
        canonical_envelope = IngestEnvelope(
            source=envelope.source,
            format="canonical",
            schemaVersion=envelope.schemaVersion,
            eventId=envelope.eventId,
            correlationId=envelope.correlationId,
            timestamp=envelope.timestamp,
            meta=envelope.meta,
            payload=canonical_payload
        )

        # 4) Store canonical result
        save_doc("harmonize", canonical_envelope.dict())

        # 5) Forward hint
        return {
            "status": "harmonized",
            "source": canonical_envelope.source,
            "next": "/fdif/validate",
            "envelope": canonical_envelope.dict()
        }

    except Exception as e:
        save_dlq("harmonize:error", envelope.dict(), str(e))
        raise HTTPException(status_code=422, detail=str(e))
