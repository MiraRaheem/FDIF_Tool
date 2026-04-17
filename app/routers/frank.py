from fastapi import APIRouter, HTTPException
from typing import Dict, Any

# Existing
from app.services.harmonizer_frank_event import harmonize_frank_event
from app.services.validator_frank_event import validate_frank_event
from app.services.blueprint_adapter import create_frank_event

# NEW (alerts)
from app.services.harmonizer_frank_alert import harmonize_frank_alert
from app.services.validator_frank_alert import validate_frank_alert
from app.services.blueprint_adapter import create_frank_alert


router = APIRouter(prefix="/fdif/frank", tags=["Frank Events"])


# =========================================
# EVENT (EXISTING)
# =========================================
@router.post("/event")
def ingest_frank_event(body: Dict[str, Any]):

    try:
        canonical = harmonize_frank_event(body)
        validated = validate_frank_event(canonical)
        result = create_frank_event(validated)

        return {
            "status": "success",
            "canonical": canonical,
            "blueprint": result
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================================
# ALERT (NEW)
# =========================================
@router.post("/alert")
def ingest_frank_alert(body: Dict[str, Any]):

    try:
        # -------- STEP 1: Harmonize --------
        canonical = harmonize_frank_alert(body)

        # -------- STEP 2: Validate --------
        validated = validate_frank_alert(canonical)

        # -------- STEP 3: Blueprint --------
        result = create_frank_alert(validated)

        return {
            "status": "success",
            "canonical": canonical,
            "blueprint": result
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
