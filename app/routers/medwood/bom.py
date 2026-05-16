from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.medwood_pipeline import (
    process_bom_excel
)

router = APIRouter(
    prefix="/fdif/medwood/boms",
    tags=["Medwood - BOMs"]
)


@router.post("/upload")
async def upload_bom(file: UploadFile = File(...)):
    try:
        return process_bom_excel(file)

    except Exception as e:
        raise HTTPException(400, str(e))
