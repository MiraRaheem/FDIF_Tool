from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.services.harmonizer import harmonize_raw_iot
from app.services.validator import validate_and_enrich
from app.services.semantics import to_jsonld_observation
from app.services.blueprint_mapper import map_to_blueprint

router = APIRouter(tags=["iot"])

# 1) RAW -> HARMONIZED
@router.post("/iot/harmonize")
def iot_harmonize(raw: Dict[str, Any]) -> Dict[str, Any]:
    harmonized = harmonize_raw_iot(raw)
    return {"harmonized": harmonized}

# 2) HARMONIZED -> VALIDATED(+ENRICHED)
@router.post("/iot/validate")
def iot_validate(harmonized: Dict[str, Any]) -> Dict[str, Any]:
    ok, validated, msg = validate_and_enrich(harmonized)
    if not ok:
        raise HTTPException(status_code=422, detail=f"Validation failed: {msg}")
    return {"validated": validated}

# 3) VALIDATED -> JSON-LD
@router.post("/iot/tag")
def iot_tag(validated: Dict[str, Any]) -> Dict[str, Any]:
    jsonld = to_jsonld_observation(validated)
    return {"jsonld": jsonld}

# 4) JSON-LD -> BLUEPRINT VIEW
@router.post("/iot/map")
def iot_map(jsonld: Dict[str, Any]) -> Dict[str, Any]:
    blueprint_view = map_to_blueprint(jsonld)
    return {"blueprint": blueprint_view}

# 5) (Optional) ONE-SHOT PIPELINE
@router.post("/iot/run")
def iot_run(raw: Dict[str, Any]) -> Dict[str, Any]:
    harmonized = harmonize_raw_iot(raw)
    ok, validated, msg = validate_and_enrich(harmonized)
    if not ok:
        raise HTTPException(status_code=422, detail=f"Validation failed: {msg}")
    jsonld = to_jsonld_observation(validated)
    blueprint_view = map_to_blueprint(jsonld)
    return {
        "step1_raw": raw,
        "step2_harmonized": harmonized,
        "step4_validated": validated,
        "step5_jsonld": jsonld,
        "step6_blueprint": blueprint_view
    }
