from typing import Dict, Any

def to_float(v):
    try:
        return float(v)
    except Exception:
        return None

def harmonize_medwood_supplier(row):

    return {

        "supplierId": row.get("Cuenta de Cliente"),

        "supplierName": row.get("Razón Social"),

        "country": row.get("País"),

        "location": {

            "address": row.get("Calle"),

            "postalCode": row.get("Código Postal"),

            "city": row.get("Localidad")

        }
    }
    
def harmonize_raw_iot(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 2: Schema Harmonizer
    - Rename TMP -> temperature
    - Ensure numeric type
    - Keep unit (C/F/K) as provided
    - Normalize location structure
    """
    temperature = raw.get("temperature")
    if temperature is None and "TMP" in raw:
        temperature = to_float(raw.get("TMP"))

    unit = raw.get("temperature_unit") or raw.get("unit")
    location = raw.get("location") or raw.get("meta") or {}
    site = location.get("site") or location.get("locationName")
    line = location.get("line")

    return {
        "deviceId": raw.get("deviceId"),
        "temperature": to_float(temperature),
        "temperature_unit": unit,
        "timestamp": raw.get("timestamp"),
        "status": raw.get("status"),
        "location": {
            "site": site,
            "line": line,
        },
    }

def harmonize_raw_work_order(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    RAW ERP JSON → FDIF Canonical WorkOrder
    """
    # --- Work Order header ---
    work_order = {
        "id": raw.get("WorkOrderID"),
        "status": raw.get("Status"),
        "requestedQuantity": raw.get("Quantity"),
    }

    # --- Product ---
    product = {
        "id": raw.get("ProductID"),
        "name": raw.get("ProductName"),
    }

    # --- BOM ---
    bom_items = []
    for item in raw.get("BOM", []):
        bom_items.append({
            "materialId": item.get("MaterialID"),
            "materialName": item.get("MaterialName"),
            "requiredQuantity": item.get("Qty"),
            "unit": item.get("Unit"),
        })

    bill_of_materials = {
        "items": bom_items
    }

    # --- Processes / Operations ---
    processes = []
    for op in raw.get("Operations", []):
        processes.append({
            "operationId": op.get("OperationID"),
            "name": op.get("Name"),
            "plannedDuration": op.get("PlannedDuration"),
            "workstationId": op.get("Workstation"),
        })

    return {
        "workOrder": work_order,
        "product": product,
        "billOfMaterials": bill_of_materials,
        "processes": processes,
        "executions": []  # optional, empty for now
    }
