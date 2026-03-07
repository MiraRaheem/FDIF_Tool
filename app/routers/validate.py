# app/routers/validate.py
"""
/fdif/validate
--------------
Runs structural + semantic validation on CANONICAL messages.
"""

from fastapi import APIRouter, HTTPException
from app.models import IngestEnvelope
from app.services.validator import (
    validate_and_enrich,
    validate_work_order
)
from app.services.storage import save_doc, save_dlq

router = APIRouter(tags=["validate"])


@router.post("/validate")
def validate(envelope: IngestEnvelope):
    if envelope.format != "canonical":
        raise HTTPException(
            status_code=400,
            detail="Only CANONICAL messages can be validated"
        )

    try:
        if envelope.source == "iot":
            ok, enriched, err = validate_and_enrich(envelope.payload)

        elif envelope.source == "work_order":
            ok, enriched, err = validate_work_order(envelope.payload)

        else:
            raise ValueError(f"No validator for source '{envelope.source}'")

        if not ok:
            save_dlq("validate:failed", envelope.dict(), err)
            raise HTTPException(status_code=422, detail=err)

        validated_envelope = envelope.dict()
        validated_envelope["payload"] = enriched

        save_doc("validate", validated_envelope)

        return {
            "status": "validated",
            "source": envelope.source,
            "next": "semantic-tagging",
            "envelope": validated_envelope
        }

    except Exception as e:
        save_dlq("validate:error", envelope.dict(), str(e))
        raise HTTPException(status_code=422, detail=str(e))
