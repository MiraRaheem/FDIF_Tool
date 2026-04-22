from fastapi import APIRouter
from app.services.harmonizer_melito import harmonize_melito_readings
from app.services.ontology_melito_mapper import map_to_ontology
from app.services.validator_melito import validate_melito_entities

router = APIRouter(
    prefix="/fdif/cep",   # ✅ FIX URL
    tags=["CEP"]          # ✅ FIX HEADER NAME
)


@router.post("/melito-readings", summary="Ingest Melito Readings")
def ingest_melito_readings(raw: dict):

    # Step 1 — Harmonize
    canonical = harmonize_melito_readings(raw)

    # Step 2 — Validate existence (🔥 NEW)
    validate_melito_entities(canonical)

    # Step 3 — Map
    result = map_to_ontology(canonical)

    return {
        "status": "success",
        "instances_created": result
    }
