from fastapi import APIRouter, UploadFile, File
import pandas as pd
import json

from app.services.medwood_pipeline import (
    process_component_json,
    process_component_excel
)

router = APIRouter(
    prefix="/fdif/medwood/components",
    tags=["MEDWOOD Components"]
)


# -----------------------------------
# JSON ENDPOINT
# -----------------------------------

@router.post("")
async def ingest_component_json(payload: dict):

    result = process_component_json(payload)

    return result


# -----------------------------------
# EXCEL ENDPOINT
# -----------------------------------

@router.post("/upload")
async def upload_component_excel(file: UploadFile = File(...)):

    df = pd.read_excel(file.file)

    result = process_component_excel(df)

    return result
