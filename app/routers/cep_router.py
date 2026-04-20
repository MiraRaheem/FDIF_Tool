from fastapi import APIRouter
from app.services.harmonizer_melito import harmonize_melito_readings
from app.services.ontology_melito_mapper import map_to_ontology

router = APIRouter()

@router.post("/cep/melito-readings")
def ingest_melito_readings(raw: dict):

    # Step 1 — Harmonize
    canonical = harmonize_melito_readings(raw)

    # Step 2 — Map to ontology
    result = map_to_ontology(canonical)

    return {
        "status": "success",
        "instances_created": result
    }
