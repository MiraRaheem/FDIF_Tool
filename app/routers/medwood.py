from fastapi import APIRouter, UploadFile, File, Query
import pandas as pd

from app.services.medwood_registry import get_harmonizer

router = APIRouter(tags=["medwood"])


@router.post("/medwood/upload")
async def upload_medwood_dataset(
    dataset: str = Query(...),
    file: UploadFile = File(...)
):

    df = pd.read_excel(file.file)

    rows = df.to_dict(orient="records")

    harmonizer = get_harmonizer(dataset)

    canonical_rows = []

    for row in rows:
        canonical_rows.append(harmonizer(row))

    return {
        "dataset": dataset,
        "rows_processed": len(canonical_rows),
        "sample": canonical_rows[:5]
    }
