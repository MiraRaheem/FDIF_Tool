
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.budatech_v2.pipeline import ingest_customer_excel


router = APIRouter(
    prefix="/fdif/budatech-v2",
    tags=["FDIF Budatech v2"],
)


@router.post("/customers/ingest")
def ingest_customers(file: UploadFile = File(...)):
    """
    Ingest Customer records from an Excel file.

    Existing Customer IDs are skipped and reported as duplicates.
    """

    filename = file.filename or ""

    if Path(filename).suffix.lower() != ".xlsx":
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

        result = ingest_customer_excel(temporary_path)

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Customer ingestion failed: {exc}",
        ) from exc

    finally:
        file.file.close()

        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)

