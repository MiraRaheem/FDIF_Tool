
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.budatech_v2.pipeline import ingest_supplier_excel


router = APIRouter(
    prefix="/fdif/budatech-v2",
    tags=["FDIF Budatech v2"],
)


@router.post("/suppliers/ingest")
def ingest_suppliers(file: UploadFile = File(...)):
    """
    Ingest Supplier records from an Excel file.

    Existing Supplier IDs are skipped and reported as duplicates.
    """
    filename = file.filename or ""

    if Path(filename).suffix.lower() != ".xlsx":
        file.file.close()
        raise HTTPException(
            status_code=400,
            detail="Please upload an .xlsx Excel file.",
        )

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".xlsx",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name

            while chunk := file.file.read(1024 * 1024):
                temporary_file.write(chunk)

        return ingest_supplier_excel(temporary_path)

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Supplier ingestion failed: {exc}",
        ) from exc

    finally:
        file.file.close()

        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)

