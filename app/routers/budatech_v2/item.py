
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Literal

from app.services.budatech_v2.excel_reader import read_excel_records

router = APIRouter(
    prefix="/fdif/budatech-v2/test",
    tags=["Budatech V2 - Testing"],
)


@router.post("/reader")
async def test_excel_reader(
    entity: Literal["customers", "suppliers", "items"],
    file: UploadFile = File(...),
):
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Please upload an Excel file.",
        )

    try:
        records = read_excel_records(file.file)

        return {
            "entity": entity,
            "filename": file.filename,
            "record_count": len(records),
            "columns": list(records[0].keys()) if records else [],
            "first_record": records[0] if records else None,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Excel reading failed: {str(exc)}",
        )
    finally:
        await file.close()
