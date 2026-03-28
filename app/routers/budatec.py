from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.services.harmonizer_budatec import harmonize_budatec_supplier
from app.services.validator_budatec import validate_budatec_supplier
from app.services.blueprint_adapter import create_supplier_instance

router = APIRouter(tags=["BUDATEC"])

@router.post("/budatec/{entity_type}")
def ingest_budatec(entity_type: str, raw: Dict[str, Any]):

    try:

        # ---- Step 1: Route by type ----
        if entity_type == "supplier":
            canonical = harmonize_budatec_supplier(raw)
            validated = validate_budatec_supplier(canonical)
            result = create_supplier_instance(validated)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported entity_type: {entity_type}"
            )

        return {
            "entity": entity_type,
            "status": "success",
            "canonical": canonical,
            "blueprint": result
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
