from typing import Dict, Any, Tuple

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


def validate_station(data):

    if not data.get("stationId"):
        raise ValueError("Missing stationId")

    if data.get("capacityHoursPerDay") is None:
        raise ValueError("Missing capacityHoursPerDay")

    return data
