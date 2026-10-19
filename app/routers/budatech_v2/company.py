from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.budatech_v2.pipeline import ingest_company_excel

router = APIRouter(
    prefix="/fdif/budatech-v2",
    tags=["FDIF Budatech v2"],
)


ALLOWED_EXTENSIONS = {".xlsx", ".xls"}


@router.post("/ingest")
async def ingest_company(file: UploadFile = File(...)) -> dict[str, Any]:
    """Ingest Company rows from an uploaded Excel file as LeadManufacturer instances."""
    suffix = Path(file.filename or "").suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Upload an Excel file with .xlsx or .xls extension.",
        )

    temp_path: str | None = None
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")

        with NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        result = ingest_company_excel(temp_path)
        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Company ingestion failed: {exc}",
        ) from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
        await file.close()

