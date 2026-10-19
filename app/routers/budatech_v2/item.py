
from fastapi import APIRouter

from app.services.budatech_v2.excel_reader import (
    read_customers,
    read_suppliers,
    read_items,
)

router = APIRouter(
    prefix="/fdif/budatech-v2/test",
    tags=["Budatech V2 - Testing"],
)


@router.get("/reader")
def test_reader():
    return {
        "message": "Budatech V2 reader imports successfully",
        "readers": [
            "customers",
            "suppliers",
            "items",
        ],
    }

