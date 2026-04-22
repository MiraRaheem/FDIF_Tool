from fastapi import APIRouter, Query

from app.services.synthetic_cep_service import (
    get_melito_readings,
    get_melito_events,
    get_argon_readings,
    get_argon_predictions,
    get_argon_maintenance
)

router = APIRouter(
    prefix="/fdif/cep",
    tags=["CEP Data"]
)

# =========================
# MELITO ENDPOINTS
# =========================

@router.get("/melito/readings")
def melito_readings(n: int = Query(100, description="Number of records")):
    return {
        "dataset": "melito_readings",
        "count": n,
        "data": get_melito_readings(n)
    }


@router.get("/melito/events")
def melito_events(n: int = Query(100)):
    return {
        "dataset": "melito_events",
        "count": n,
        "data": get_melito_events(n)
    }


# =========================
# ARGON ENDPOINTS
# =========================

@router.get("/argon/readings")
def argon_readings(n: int = Query(100)):
    return {
        "dataset": "argon_readings",
        "count": n,
        "data": get_argon_readings(n)
    }


@router.get("/argon/predictions")
def argon_predictions(n: int = Query(100)):
    return {
        "dataset": "argon_predictions",
        "count": n,
        "data": get_argon_predictions(n)
    }


