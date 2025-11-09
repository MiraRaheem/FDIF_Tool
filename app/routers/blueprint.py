from fastapi import APIRouter

router = APIRouter(tags=["blueprint"])

@router.get("/blueprint/{bp_id}/links")
def blueprint_links(bp_id: str):
    # baby step: static stub
    return {
        "blueprint": bp_id,
        "workOrders": ["WO-1001"],
        "boms": ["BOM-45"],
        "components": ["IC-XYZ123", "RES-10K"]
    }
