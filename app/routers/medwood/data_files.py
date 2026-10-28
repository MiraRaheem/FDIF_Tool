"""Generate Medwood review files and return them as ZIP downloads."""

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.services.medwood_process_executions import build_process_execution_outputs
from app.services.medwood_work_orders import write_work_order_csvs

router = APIRouter(
    prefix="/fdif/medwood/data-files",
    tags=["MEDWOOD Data Files"],
)


def _zip_response(files: dict[str, Path], filename: str) -> StreamingResponse:
    archive = BytesIO()
    with ZipFile(archive, mode="w", compression=ZIP_DEFLATED) as zip_file:
        for path in files.values():
            zip_file.write(path, arcname=path.name)
    archive.seek(0)
    return StreamingResponse(
        archive,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/work-orders", response_class=StreamingResponse)
def generate_work_order_files(
    transactions_file: UploadFile = File(...),
    performance_file: UploadFile = File(...),
):
    """Upload source workbooks and download the three Work Order CSV reports."""
    try:
        with TemporaryDirectory(prefix="fdif-medwood-work-orders-") as temp_dir:
            root = Path(temp_dir)
            transactions_path = root / Path(transactions_file.filename or "transactions.xlsx").name
            performance_path = root / Path(performance_file.filename or "performance.xlsx").name
            transactions_path.write_bytes(transactions_file.file.read())
            performance_path.write_bytes(performance_file.file.read())
            output_dir = root / "outputs"
            outputs = write_work_order_csvs(
                output_dir=output_dir,
                transactions_path=transactions_path,
                performance_path=performance_path,
            )
            return _zip_response(outputs, "medwood_work_order_outputs.zip")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        transactions_file.file.close()
        performance_file.file.close()


@router.post("/process-executions", response_class=StreamingResponse)
def generate_process_execution_files(
    performance_file: UploadFile = File(...),
    work_orders_file: UploadFile | None = File(default=None),
):
    """Upload a performance workbook and download the three ProcessExecution reports.

    Optionally include the generated Work Order review CSV to cross-check
    ProcessExecution references against known Work Order IDs.
    """
    try:
        with TemporaryDirectory(prefix="fdif-medwood-process-executions-") as temp_dir:
            root = Path(temp_dir)
            performance_path = root / Path(performance_file.filename or "performance.xlsx").name
            performance_path.write_bytes(performance_file.file.read())
            work_orders_path = None
            if work_orders_file is not None:
                work_orders_path = root / Path(work_orders_file.filename or "work_orders.csv").name
                work_orders_path.write_bytes(work_orders_file.file.read())
            output_dir = root / "outputs"
            outputs = build_process_execution_outputs(
                performance_path=performance_path,
                output_dir=output_dir,
                work_orders_path=work_orders_path,
            )
            return _zip_response(outputs, "medwood_process_execution_outputs.zip")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        performance_file.file.close()
        if work_orders_file is not None:
            work_orders_file.file.close()
