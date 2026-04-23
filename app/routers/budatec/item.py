from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any

from app.services.budatec_pipeline import process_item_json, process_item_excel

router = APIRouter(
    prefix="/fdif/budatec/items",
    tags=["Budatec - Items"]
)


@router.post("", summary="Ingest single item (JSON)")
def ingest_item(body: Dict[str, Any]):

    try:
        return process_item_json(body)

    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/upload", summary="Bulk upload items (Excel)")
async def upload_items(file: UploadFile = File(...)):

    try:
        return process_item_excel(file)

    except Exception as e:
        raise HTTPException(400, str(e))
