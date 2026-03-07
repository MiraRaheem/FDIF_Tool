# app/routers/work_order.py
from fastapi import APIRouter, HTTPException
from app.models import IngestEnvelope
from app.services.harmonizer import harmonize_raw_work_order
from app.services.validator import validate_work_order
from app.services.storage import save_doc, save_dlq
from app.services.semantics import tag_work_order

router = APIRouter(
    prefix="/work_order",
    tags=["work_order"]
)

@router.post("/harmonize")
def work_order_harmonize(envelope: IngestEnvelope):
    if envelope.source != "work_order" or envelope.format != "raw":
        raise HTTPException(
            status_code=400,
            detail="Expected RAW work_order envelope"
        )

    try:
        canonical = harmonize_raw_work_order(envelope.payload)

        out = envelope.copy(update={
            "format": "canonical",
            "payload": canonical
        })

        save_doc("work_order:harmonize", out.dict())

        return {
            "status": "harmonized",
            "next": "/fdif/work_order/validate",
            "envelope": out.dict()
        }

    except Exception as e:
        save_dlq("work_order:harmonize", envelope.dict(), str(e))
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/validate")
def work_order_validate(envelope: IngestEnvelope):
    if envelope.source != "work_order" or envelope.format != "canonical":
        raise HTTPException(
            status_code=400,
            detail="Expected CANONICAL work_order envelope"
        )

    ok, enriched, err = validate_work_order(envelope.payload)

    if not ok:
        save_dlq("work_order:validate", envelope.dict(), err)
        raise HTTPException(status_code=422, detail=err)

    out = envelope.copy(update={"payload": enriched})
    save_doc("work_order:validate", out.dict())

    return {
        "status": "validated",
        "next": "semantic-tagging",
        "envelope": out.dict()
    }

@router.post("/tag")
def work_order_tag(envelope: IngestEnvelope):
    if envelope.source != "work_order" or envelope.format != "canonical":
        raise HTTPException(
            status_code=400,
            detail="Expected CANONICAL work_order envelope"
        )

    tagged_payload = tag_work_order(envelope.payload)

    out = envelope.copy(update={"payload": tagged_payload})
    save_doc("work_order:tag", out.dict())

    return {
        "status": "tagged",
        "next": "/fdif/work_order/map",
        "envelope": out.dict()
    }
