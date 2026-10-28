from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.services.medwood_pipeline import (
    process_product_type_json
)

router = APIRouter(
    prefix="/fdif/medwood/product-types",
    tags=["Medwood - Product Types"]
)


@router.post("")
def ingest_product_type(body: Dict[str, Any]):
    try:
        return process_product_type_json(body)

    except Exception as e:
        raise HTTPException(400, str(e))
