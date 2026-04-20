from fastapi import APIRouter
from app.services.harmonizer_melito import harmonize_melito_readings
from app.services.ontology_melito_mapper import map_to_ontology

router = APIRouter(
    prefix="/fdif/cep",   # ✅ FIX URL
    tags=["CEP"]          # ✅ FIX HEADER NAME
)


@router.post("/melito-readings", summary="Ingest Melito Readings")
def ingest_melito_readings(raw: dict):

    canonical = harmonize_melito_readings(raw)
    result = map_to_ontology(canonical)

    return {
        "status": "success",
        "instances_created": result
    }
