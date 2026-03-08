from typing import Dict, Any, Tuple

ALLOWED_UNITS = {"C", "F", "K"}

def convert_to_celsius(value: float, unit: str) -> float:
    if unit == "C":
        return value
    if unit == "K":
        return value - 273.15
    if unit == "F":
        return (value - 32.0) * 5.0/9.0
    # unknown -> return as-is
    return value

def validate_and_enrich(harmonized: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
    """
    Step 4: Validation Engine (structure + semantics)
    - required fields
    - unit in {C,F,K}
    - compute temperature_celsius
    """
    dev = harmonized.get("deviceId")
    t = harmonized.get("temperature")
    u = harmonized.get("temperature_unit")
    ts = harmonized.get("timestamp")

    if not dev:
        return False, harmonized, "deviceId missing"
    if t is None:
        return False, harmonized, "temperature missing or not numeric"
    if not u or u not in ALLOWED_UNITS:
        return False, harmonized, f"temperature_unit must be one of {sorted(ALLOWED_UNITS)}"
    if not ts:
        return False, harmonized, "timestamp missing"

    t_c = round(convert_to_celsius(float(t), u), 2)
    enriched = dict(harmonized)
    enriched["temperature_celsius"] = t_c
    # normalize unit to 'C' for downstream (optional)
    return True, enriched, ""

ALLOWED_WO_STATUS = {"Planned", "Released", "Running", "Completed"}

def validate_work_order(canonical: Dict[str, Any]):
    wo = canonical.get("workOrder", {})
    product = canonical.get("product", {})
    bom = canonical.get("billOfMaterials", {})
    processes = canonical.get("processes", [])

    if not wo.get("id"):
        return False, canonical, "workOrder.id missing"

    if wo.get("requestedQuantity") is None or wo.get("requestedQuantity") <= 0:
        return False, canonical, "requestedQuantity must be > 0"

    if wo.get("status") not in ALLOWED_WO_STATUS:
        return False, canonical, f"invalid work order status: {wo.get('status')}"

    if not product.get("id"):
        return False, canonical, "product.id missing"

    if not bom.get("items"):
        return False, canonical, "billOfMaterials.items missing or empty"

    if not processes:
        return False, canonical, "no production processes defined"

    return True, canonical, ""
def validate_supplier(canonical):

    if not canonical.get("supplierId"):
        raise ValueError("supplierId is required")

    if not canonical.get("supplierName"):
        raise ValueError("supplierName is required")

    if not canonical.get("country"):
        raise ValueError("country is required")

    location = canonical.get("location", {})

    if not location.get("city"):
        raise ValueError("city is required")

    return canonical
def validate_supplier_performance(data):

    if not data.get("supplierId"):
        raise ValueError("supplierId is required")

    return data
