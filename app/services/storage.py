# app/services/storage.py
"""
Simple in-memory storage used in Phase 2:
- DATA: accepted items by kind
- DLQ:  failed items with reason
- SEEN: idempotency keys we've processed
Replace with Postgres/Mongo/Kafka/etc. in later phases.
"""

from typing import Dict, Any, List, Tuple

DATA: Dict[str, List[Dict[str, Any]]] = {}
DLQ:  List[Dict[str, Any]] = []
SEEN: Dict[str, set] = {}  # idempotency keys we've seen per 'kind'

def save_doc(kind: str, obj: Dict[str, Any]) -> None:
    DATA.setdefault(kind, []).append(obj)

def save_dlq(stage: str, obj: Dict[str, Any], error: str) -> None:
    DLQ.append({"stage": stage, "error": error, "payload": obj})

def dedupe(kind: str, key: str) -> Tuple[bool, str]:
    """
    Returns (ok, why). If key is empty, we allow (best-effort).
    If duplicate, return False so caller can 409.
    """
    if not key:
        return True, ""
    seen = SEEN.setdefault(kind, set())
    if key in seen:
        return False, "duplicate idempotency key"
    seen.add(key)
    return True, ""

