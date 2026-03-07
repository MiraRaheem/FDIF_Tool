# app/models.py
"""
Pydantic models (contracts) used by /fdif/ingest.
We keep RAW permissive and CANONICAL slightly stricter per domain.
"""

from typing import Any, Dict, Optional, Literal, List, Union
from pydantic import BaseModel, Field

# Enumerations for envelope fields
Source = Literal["iot", "work_order", "bom", "supplier", "sales_order", "customer"]
Fmt    = Literal["raw", "canonical"]

class IngestEnvelope(BaseModel):
    """
    A tiny, stable ENVELOPE that every message (RAW or CANONICAL) must carry.
    - lets us route, trace, dedupe, and attribute a payload without inspecting it
    """
    source: Source                       # which domain this belongs to
    format: Fmt                          # raw or canonical
    schemaVersion: str = "1.0.0"         # your contract versioning
    eventId: Optional[str] = None        # provider event id (optional)
    correlationId: Optional[str] = None  # for cross-step correlation (optional)
    timestamp: Optional[str] = None      # ISO8601 (optional, but recommended)
    meta: Optional[Dict[str, Any]] = None  # adapter/site/line/etc (free-form)
    payload: Dict[str, Any]              # the actual data (raw OR canonical)

class CanonicalIoT(BaseModel):
    """
    Minimal shape for CANONICAL IoT messages.
    NOTE: 'extra = allow' ensures we don't break when new fields show up.
    """
    deviceId: str
    timestamp: str
    temperature: float
    temperature_unit: Literal["C", "F", "K"]
    status: Optional[str] = None
    location: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"
from typing import List

class CanonicalWorkOrder(BaseModel):
    """
    Light canonical shape for Production Work Orders.
    This is NOT full validation — only structure.
    """
    workOrder: Dict[str, Any]
    product: Dict[str, Any]
    billOfMaterials: Dict[str, Any]
    processes: List[Dict[str, Any]]
    executions: Optional[List[Dict[str, Any]]] = None

    class Config:
        extra = "allow"

# Body can be a single envelope or a batch (list of envelopes)
IngestBody = Union[IngestEnvelope, List[IngestEnvelope]]

