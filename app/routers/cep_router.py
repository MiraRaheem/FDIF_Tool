from fastapi import APIRouter
from app.services.harmonizer_observations import harmonize_observations
from app.services.validator_observations import validate_observations
from app.services.ontology_observations_mapper import map_observations
from app.services.harmonizer_events import (
    harmonize_events,
    harmonize_argon_prediction   # ✅ ADD THIS
)

from app.services.validator_events import (
    validate_events,
    validate_argon_prediction     # ✅ ADD THIS
)

from app.services.ontology_events_mapper import (
    map_events,
    map_argon_prediction          # ✅ ADD THIS
)


router = APIRouter(
    prefix="/fdif/cep",   # ✅ FIX URL
    tags=["CEP"]          # ✅ FIX HEADER NAME
)


@router.post("/observations/melito", summary="Ingest Melito Observations")
def ingest_melito_readings(raw: dict):

    canonical = harmonize_observations(raw)
    validate_observations(canonical)
    result = map_observations(canonical)

    return {
        "status": "success",
        "instances_created": result
    }

@router.post("/observations/argon", summary="Ingest Argon Observations")
def ingest_argon_observations(raw: dict):

    canonical = harmonize_observations(raw)
    validate_observations(canonical)
    result = map_observations(canonical)

    return {
        "status": "success",
        "instances_created": result
    }

@router.post("/events/melito", summary="Ingest Melito Events")
def ingest_melito_events(raw: dict):

    canonical = harmonize_events(raw)
    validate_events(canonical)
    result = map_events(canonical)

    return {
        "status": "success",
        "event_created": result
    }

@router.post("/events/argon-prediction", summary="Ingest Argon Predictive Events")
def ingest_argon_prediction(raw: dict):

    canonical = harmonize_argon_prediction(raw)
    validate_argon_prediction(canonical)
    result = map_argon_prediction(canonical)

    return {
        "status": "success",
        "event_created": result
    }
