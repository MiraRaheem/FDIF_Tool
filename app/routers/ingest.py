from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict

router = APIRouter(tags=["ingest"])

class CanonicalRecord(BaseModel):
    source: str                 # "bom" | "work_order" | "sales_order" | ...
    payload: Dict[str, Any]     # raw/canonical JSON from Excel

@router.post("/ingest")
def ingest(record: CanonicalRecord):
    # baby step: just echo what we got
    return {
        "status": "received",
        "source": record.source,
        "fields": len(record.payload)
    }
